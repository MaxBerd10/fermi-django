# "Videolar" (videos) under the page of the anti-corruption department
#   /blog/1944/korrupsiyaga-qarshi-kurashish-komplayens-nazorat-tizimini-boshqarish-bolimi   (page slug below)
# Eight short videos (3 explainers in phone format 1080x1920 + 5 clips of the Anti-Corruption Agency campaign "Har bir sukut - yangi oqibat",
# hotline 1253). The videos were compressed from 317 MB to 33 MB (H.264, same resolution, same audio) and each has a poster frame
# (the poster is required by the site: it is what shows before the video starts).
#
# What this script does (all or nothing, in one transaction):
#   * reads the 8 videos and 8 posters from the folder SRC (default /home/fermi-django/korrupsiya-video-kichik),
#   * stores them in the media library (uploads/videos/YYYY/MM/ and uploads/YYYY/MM/) as Video and Image rows,
#   * adds to the END of the page (after its existing text) one heading "Videolar / Видео / Videos" and 8 video blocks, each with a
#     caption in uz, ru and en. The existing block of the page is not touched.
#   * if it runs as root, gives the new files and folders to www-data (the site runs as www-data; root-owned media breaks uploads).
#
# SAFE BY DESIGN: dry (default) writes nothing and checks that every file and the page exist; apply refuses to run twice (backup file) and
# refuses if the page already has a video block; undo removes exactly the blocks, Video/Image rows and files this script created (a block that was
# edited since is left and listed).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/korrupsiya-video/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/korrupsiya-video/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/korrupsiya-video/apply.py
import json
import os
import shutil
from datetime import datetime

from django.core.files import File
from django.db import transaction
from django.utils import timezone

from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image, Video

MODE = os.environ.get("MODE", "dry")
SRC = os.environ.get("SRC", "/home/fermi-django/korrupsiya-video-kichik")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "korrupsiya-video.json")
SLUG = "korrupsiyaga-qarshi-kurashish-komplayens-nazorat-tizimini-boshqarish-bolimi"

# file name (without .mp4 / poster-), captions uz / ru / en.  Uzbek uses the apostrophe U+02BB.
HEADING = {"uz": "Videolar", "ru": "Видео", "en": "Videos"}
ITEMS = [
    ("korrupsiya-oqibatlari", "Korrupsiya oqibatlari", "Последствия коррупции", "Consequences of corruption"),
    ("tanish-bilishchilik", "Tanish-bilishchilik", "Знакомства и протекция", "Connections and favoritism"),
    ("yoldan-ogirlangan-har-bir-som", "Yoʻldan oʻgʻirlangan har bir soʻm", "Каждый сум, украденный у дороги", "Every som stolen from the road"),
    ("video-1", "Adolat — har bir toʻgʻri qarorning natijasi. Korrupsiya haqida xabar bering: ishonch telefoni 1253", "Справедливость — результат каждого правильного решения. Сообщите о коррупции: телефон доверия 1253", "Justice is the result of every right decision. Report corruption: hotline 1253"),
    ("video-2", "Har bir sukut — yangi oqibat (1)", "Каждое молчание — новое последствие (1)", "Every silence is a new consequence (1)"),
    ("video-3", "Har bir sukut — yangi oqibat (2)", "Каждое молчание — новое последствие (2)", "Every silence is a new consequence (2)"),
    ("video-4", "Har bir sukut — yangi oqibat (3)", "Каждое молчание — новое последствие (3)", "Every silence is a new consequence (3)"),
    ("video-5", "Har bir sukut — yangi oqibat (4)", "Каждое молчание — новое последствие (4)", "Every silence is a new consequence (4)"),
]

print("MODE:", MODE)


def give_to_www_data(path, stop):
    """Only when run as root: the file and every folder created up to `stop` go to www-data."""
    if os.geteuid() != 0:
        return
    shutil.chown(path, "www-data", "www-data")
    d = os.path.dirname(path)
    while d.startswith(stop) and len(d) > len(stop):
        try:
            if os.stat(d).st_uid == 0:
                shutil.chown(d, "www-data", "www-data")
        except OSError:
            pass
        d = os.path.dirname(d)


if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    removed = 0
    with transaction.atomic():
        for row in backup["blocks"]:
            block = ContentBlock.objects.filter(pk=row["pk"]).first()
            if block is None:
                continue
            if block.data != row["data"]:
                print("left block %s (#%s): edited after this script" % (row["pk"], block.order))
                continue
            block.delete()
            removed += 1
        for row in backup["videos"]:
            if ContentBlock.objects.filter(block_type="video", data__uz__video_id=row["pk"]).exists():
                print("left video %s: still used by a block" % row["pk"])
                continue
            Video.objects.filter(pk=row["pk"]).delete()
        for row in backup["images"]:
            try:
                Image.objects.filter(pk=row["pk"]).delete()
            except Exception as exc:  # a poster still used by a video that was left
                print("left poster %s: %s" % (row["pk"], exc))
        Page.objects.filter(slug=SLUG).update(updated_at=timezone.now())
    from django.core.files.storage import default_storage
    for name in backup["files"]:
        if default_storage.exists(name):
            default_storage.delete(name)
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d blocks removed, files deleted. (backup kept under a new name)" % removed)
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

page = Page.objects.filter(slug=SLUG).first()
if page is None:
    raise SystemExit("STOP: page %s not found." % SLUG)
if page.blocks.filter(block_type="video").exists():
    raise SystemExit("STOP: the page already has a video block; nothing was changed.")
last_order = max([b.order for b in page.blocks.all()] or [0])

total = 0
for base, uz, ru, en in ITEMS:
    for name in ("%s.mp4" % base, "poster-%s.jpg" % base):
        path = os.path.join(SRC, name)
        if not os.path.isfile(path):
            raise SystemExit("STOP: file not found: %s (copy the folder to the server first, or set SRC=...)" % path)
        total += os.path.getsize(path)
print("page: %s (id %s), now %d block(s); the new blocks get orders %d..%d" % (SLUG, page.pk, page.blocks.count(), last_order + 1, last_order + 1 + len(ITEMS)))
print("files: %d videos + %d posters, %.1f MB, all found in %s" % (len(ITEMS), len(ITEMS), total / 1e6, SRC))
print("  order %d  heading: %s / %s / %s" % (last_order + 1, HEADING["uz"], HEADING["ru"], HEADING["en"]))
for k, (base, uz, ru, en) in enumerate(ITEMS):
    print("  order %d  video %s.mp4\n      uz: %s\n      ru: %s\n      en: %s" % (last_order + 2 + k, base, uz, ru, en))
if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

created = {"blocks": [], "videos": [], "images": [], "files": []}
media_root = str(__import__("django.conf", fromlist=["settings"]).settings.MEDIA_ROOT)
with transaction.atomic():
    order = last_order
    order += 1
    data = {lang: {"text": text, "level": 2} for lang, text in HEADING.items()}
    block = ContentBlock(page=page, order=order, block_type="heading", data=data)
    block.full_clean()
    block.save()
    created["blocks"].append({"pk": block.pk, "data": data})
    for base, uz, ru, en in ITEMS:
        with open(os.path.join(SRC, "poster-%s.jpg" % base), "rb") as f:
            img = Image(alt_text=uz)
            img.file.save("poster-%s.jpg" % base, File(f), save=True)
        with open(os.path.join(SRC, "%s.mp4" % base), "rb") as f:
            vid = Video(poster=img)
            vid.file.save("%s.mp4" % base, File(f), save=True)
        created["images"].append({"pk": img.pk})
        created["videos"].append({"pk": vid.pk})
        created["files"] += [img.file.name, vid.file.name]
        order += 1
        data = {lang: {"video_id": vid.pk, "caption": cap} for lang, cap in (("uz", uz), ("ru", ru), ("en", en))}
        block = ContentBlock(page=page, order=order, block_type="video", data=data)
        block.full_clean()
        block.save()
        created["blocks"].append({"pk": block.pk, "data": data})
    Page.objects.filter(pk=page.pk).update(updated_at=timezone.now())

os.makedirs(BACKUP_DIR, exist_ok=True)
json.dump({"created_at": datetime.now().isoformat(), **created}, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("backup saved:", BACKUP_FILE)
for name in created["files"]:
    give_to_www_data(os.path.join(media_root, name), media_root)
print("DONE: 1 heading + %d videos added to %s. To put everything back: MODE=undo with the same command." % (len(ITEMS), SLUG))
print("(the site shows it within about 10 minutes at most)")
