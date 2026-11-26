# Makes the very heavy original pictures of the media folder lighter WITHOUT changing a single path in the database:
# a picture bigger than MIN_MB is scaled down so that its longer side is at most MAX_SIDE pixels (aspect ratio kept, orientation of the camera applied) and
# re-saved in the SAME format under the SAME name. The original is copied first to BACKUP_DIR (same relative path), a manifest lists every change, and the
# width/height of the matching Image row are updated. A picture is left alone if the new file would not be at least 20% smaller.
#
# Why: pictures of 20-40 MB were uploaded straight from cameras; the site shrinks them through /img-cache, but that proxy refuses files over 30 MB, and then the
# browser downloads the full original.
#
# SAFE BY DESIGN: dry (default) writes nothing; every file is written to a temporary name and swapped in atomically; apply refuses to run twice (manifest exists);
# undo copies the originals back (only a file that still is the optimized one: edited since -> left and listed). Run as www-data so the new files belong to the
# site user (never leave root-owned files under media/).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/optimize_images.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/optimize_images.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/optimize_images.py
# Settings (environment): MIN_MB (default 8), MAX_SIDE (default 2400), QUALITY (default 85), BACKUP_DIR (default /var/backups/fermi-media-originals),
# LIMIT (apply at most N pictures, default all), ONLY (only paths containing this text), MEDIA_DIR (default MEDIA_ROOT).
import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime

from django.conf import settings
from PIL import Image as PILImage, ImageOps

from apps.media_lib.models import Image

MODE = os.environ.get("MODE", "dry")
MIN_BYTES = int(float(os.environ.get("MIN_MB", "8")) * 1024 * 1024)
MAX_SIDE = int(os.environ.get("MAX_SIDE", "2400"))
QUALITY = int(os.environ.get("QUALITY", "85"))
LIMIT = int(os.environ.get("LIMIT", "0")) or None
ONLY = os.environ.get("ONLY", "")
MEDIA_DIR = os.environ.get("MEDIA_DIR", str(settings.MEDIA_ROOT))
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-media-originals")
MANIFEST = os.path.join(BACKUP_DIR, "manifest.json")
FOLDERS = ("uploads", "migrated")
EXTENSIONS = {".jpg": "JPEG", ".jpeg": "JPEG", ".png": "PNG", ".webp": "WEBP"}
PILImage.MAX_IMAGE_PIXELS = 400_000_000  # a 41 MB camera file is ~100 megapixels at most


def digest(path):
    hasher = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def candidates():
    found = []
    for folder in FOLDERS:
        for root, _, names in os.walk(os.path.join(MEDIA_DIR, folder)):
            for name in names:
                path = os.path.join(root, name)
                if os.path.splitext(name)[1].lower() not in EXTENSIONS or ONLY not in path:
                    continue
                size = os.path.getsize(path)
                if size > MIN_BYTES:
                    found.append((size, os.path.relpath(path, MEDIA_DIR)))
    return sorted(found, reverse=True)


def optimized_copy(path, target_dir):
    """Returns (temporary file path, new size, old dimensions, new dimensions) or None when the picture should stay as it is."""
    with PILImage.open(path) as source:
        fmt = EXTENSIONS[os.path.splitext(path)[1].lower()]
        old = source.size
        image = ImageOps.exif_transpose(source)
        icc = source.info.get("icc_profile")
        if max(image.size) > MAX_SIDE:
            image.thumbnail((MAX_SIDE, MAX_SIDE), PILImage.LANCZOS)
        if fmt == "JPEG" and image.mode not in ("RGB", "L"):
            image = image.convert("RGB")
        handle, temp = tempfile.mkstemp(dir=target_dir, suffix=os.path.splitext(path)[1])
        os.close(handle)
        options = {"quality": QUALITY, "optimize": True, "progressive": True} if fmt == "JPEG" else {"optimize": True} if fmt == "PNG" else {"quality": QUALITY}
        if icc:
            options["icc_profile"] = icc
        image.save(temp, fmt, **options)
        new = image.size
    size = os.path.getsize(temp)
    if size > os.path.getsize(path) * 0.8:
        os.unlink(temp)
        return None
    return temp, size, old, new


def mb(size):
    return "%.1f MB" % (size / 1048576)


if MODE not in ("dry", "apply", "undo"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")

if MODE == "undo":
    if not os.path.exists(MANIFEST):
        raise SystemExit("STOP: no manifest (%s): nothing to undo." % MANIFEST)
    manifest = json.load(open(MANIFEST, encoding="utf8"))
    restored = left = 0
    for entry in manifest["files"]:
        path = os.path.join(MEDIA_DIR, entry["path"])
        backup = os.path.join(BACKUP_DIR, "files", entry["path"])
        if not os.path.exists(path) or digest(path) != entry["new_sha"] or not os.path.exists(backup):
            left += 1
            print("left %s: it is not the optimized file any more (or its backup is missing)" % entry["path"])
            continue
        shutil.copy2(backup, path + ".restoring")
        os.replace(path + ".restoring", path)
        Image.objects.filter(file=entry["path"]).update(width=entry["old_dims"][0], height=entry["old_dims"][1])
        restored += 1
    os.rename(MANIFEST, MANIFEST + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d restored, %d left. The backup copies stay in %s." % (restored, left, BACKUP_DIR))
else:
    if MODE == "apply" and os.path.exists(MANIFEST):
        raise SystemExit("STOP: %s exists, so this was applied before. Run MODE=undo first." % MANIFEST)
    found = candidates()
    total = sum(size for size, _ in found)
    print("%d picture(s) over %s (%s in all), longer side limit %d px, quality %d" % (len(found), mb(MIN_BYTES), mb(total), MAX_SIDE, QUALITY))
    free = shutil.disk_usage(MEDIA_DIR).free
    if MODE == "apply" and total * 1.2 > free:
        raise SystemExit("STOP: the backups need about %s but only %s is free." % (mb(total), mb(free)))
    files, saved, kept = [], 0, 0
    for size, rel in found[:LIMIT]:
        path = os.path.join(MEDIA_DIR, rel)
        try:
            result = optimized_copy(path, os.path.dirname(path)) if MODE == "apply" else None
            if MODE == "dry":
                with PILImage.open(path) as probe:
                    print("  %s  %s  %dx%d" % (mb(size).rjust(8), rel, probe.size[0], probe.size[1]))
                continue
        except Exception as error:  # an unreadable or odd file stays as it is
            print("SKIPPED %s: %s" % (rel, error))
            continue
        if result is None:
            kept += 1
            print("kept   %s (the new file would not be 20%% smaller)" % rel)
            continue
        temp, new_size, old_dims, new_dims = result
        backup = os.path.join(BACKUP_DIR, "files", rel)
        os.makedirs(os.path.dirname(backup), exist_ok=True)
        shutil.copy2(path, backup)
        mode = os.stat(path).st_mode
        os.chmod(temp, mode & 0o777)
        os.replace(temp, path)
        Image.objects.filter(file=rel).update(width=new_dims[0], height=new_dims[1])
        files.append({"path": rel, "old_size": size, "new_size": new_size, "old_dims": list(old_dims), "new_dims": list(new_dims), "new_sha": digest(path)})
        saved += size - new_size
        print("%s -> %s  %dx%d -> %dx%d  %s" % (mb(size).rjust(8), mb(new_size).rjust(8), old_dims[0], old_dims[1], new_dims[0], new_dims[1], rel))
        if len(files) % 10 == 0:  # the manifest is kept up to date, so an interruption can still be undone
            os.makedirs(BACKUP_DIR, exist_ok=True)
            json.dump({"created_at": datetime.now().isoformat(), "files": files}, open(MANIFEST, "w", encoding="utf8"), ensure_ascii=False)
    if MODE == "apply":
        os.makedirs(BACKUP_DIR, exist_ok=True)
        json.dump({"created_at": datetime.now().isoformat(), "files": files}, open(MANIFEST, "w", encoding="utf8"), ensure_ascii=False)
        print("\nDONE: %d optimized, %d kept, %s saved. Originals: %s. To put everything back: MODE=undo with the same command." % (len(files), kept, mb(saved), BACKUP_DIR))
    else:
        print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
