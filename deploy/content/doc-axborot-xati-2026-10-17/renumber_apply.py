# Replaces the live Russian and English PDFs of the information letter by the renumbered versions (their footer page
# numbers 3-4 / 5-6 become 1-2, see renumber_pages.py). Only these two files change; the cards, captions, links and the
# Uzbek PDF stay as they are, and the file NAMES stay the same, so apply.py / reshape.py keep working.
#
# SAFE BY DESIGN
#   * the file on the server must be exactly the one published before (checked by md5), the new file must be exactly the
#     one in the repository (md5): otherwise the script stops before writing anything;
#   * apply first copies the two old files to a backup folder (a second apply is refused), then swaps each file atomically
#     (a visitor never gets a half-written PDF) and updates the stored file size;
#   * undo puts the old files back from that folder.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/doc-axborot-xati-2026-10-17/renumber_apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/doc-axborot-xati-2026-10-17/renumber_apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/doc-axborot-xati-2026-10-17/renumber_apply.py
#
# Note: the web server lets browsers keep a media file for up to 7 days, so someone who opened the old PDF in the last
# days can still see the old numbers until then; everyone else gets the new file at once.
import hashlib
import os
import shutil

from django.conf import settings

from apps.media_lib.models import Document

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django/axborot-xati-renumber-2026-11-17")
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "doc-axborot-xati-2026-10-17")
SUBDIR = "uploads/documents/2026/11"
# lang -> (md5 of the file published so far, md5 of the renumbered file in the repository)
FILES = {
    "ru": ("1b7c2c1ddcac14d5deaec4d4af3b9f2c", "2ab0b0985f9ff6b205219072b88dd3eb"),
    "en": ("17d305001c459e32d4b749c334c3395b", "b32f695492d82e0a7fc8721ded11eac6"),
}


def md5(path):
    h = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def hand_to_www_data(path):
    if os.geteuid() != 0:  # the site runs as www-data; never leave root-owned media behind
        return
    import grp
    import pwd

    os.chown(path, pwd.getpwnam("www-data").pw_uid, grp.getgrnam("www-data").gr_gid)


def swap(source, target):
    """Writes `source` over `target` without ever leaving a half-written file."""
    tmp = target + ".new"
    shutil.copyfile(source, tmp)
    hand_to_www_data(tmp)
    os.replace(tmp, target)


def name(lang):
    return "axborot-xati-2026-10-17-%s.pdf" % lang


def live_path(lang):
    return os.path.join(settings.MEDIA_ROOT, SUBDIR, name(lang))


def refresh_size(lang):
    document = Document.objects.filter(file="%s/%s" % (SUBDIR, name(lang))).first()
    if document is None:
        raise SystemExit("STOP: the Document row of the %s PDF is missing." % lang)
    document.save()  # Document.save() stores the current size of the file
    return document


print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isdir(BACKUP_DIR):
        raise SystemExit("STOP: no backup folder (%s): nothing to undo." % BACKUP_DIR)
    for lang, (old_md5, new_md5) in FILES.items():
        backup = os.path.join(BACKUP_DIR, name(lang))
        if not os.path.isfile(backup) or md5(backup) != old_md5:
            raise SystemExit("STOP: the backup of the %s PDF is missing or not the expected file. Nothing was changed." % lang)
    for lang in FILES:
        swap(os.path.join(BACKUP_DIR, name(lang)), live_path(lang))
        print("restored the old %s PDF, size %d bytes" % (lang, refresh_size(lang).file_size))
    shutil.move(BACKUP_DIR, BACKUP_DIR + ".undone")
    print("UNDONE: the two old PDFs are back. (the backup folder was kept as %s.undone)" % BACKUP_DIR)
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_DIR):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_DIR)

for lang, (old_md5, new_md5) in FILES.items():
    live, new = live_path(lang), os.path.join(SRC_DIR, name(lang))
    if not os.path.isfile(live):
        raise SystemExit("STOP: %s is not on the server. Nothing was changed." % live)
    if md5(live) != old_md5:
        raise SystemExit("STOP: the live %s PDF is not the file published before (md5 differs: replaced or edited?). Nothing was changed." % lang)
    if not os.path.isfile(new) or md5(new) != new_md5:
        raise SystemExit("STOP: the renumbered %s PDF in the repository is missing or not the expected file (git pull first?). Nothing was changed." % lang)
    print("%s: %s  %d bytes (md5 %s)  ->  %d bytes (md5 %s)" % (lang, name(lang), os.path.getsize(live), old_md5[:8], os.path.getsize(new), new_md5[:8]))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR)
for lang in FILES:
    shutil.copy2(live_path(lang), os.path.join(BACKUP_DIR, name(lang)))
print("\nbackup of the two old files:", BACKUP_DIR)
for lang in FILES:
    swap(os.path.join(SRC_DIR, name(lang)), live_path(lang))
    print("replaced the %s PDF, now %d bytes" % (lang, refresh_size(lang).file_size))
print("DONE. To put the old files back: MODE=undo with the same command.")
