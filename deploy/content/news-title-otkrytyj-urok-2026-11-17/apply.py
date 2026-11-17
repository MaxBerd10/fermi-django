# One typo in a Russian news title: news "ochiq-dars-4" (Uzbek "Ochiq dars", English "Open lesson") has the Russian title
# "Открытий урок"; it must be "Открытый урок". Only title_ru of that one post changes (the text of the news has no such typo).
# (The Latin letter that used to stand for its first O was fixed earlier by homoglyph-fixes-2026-11-17.)
#
# dry (default) shows before/after and writes nothing; apply stops unless the title is exactly the expected old text, saves
# the old title to a backup file first (a second apply is refused); undo puts it back.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/news-title-otkrytyj-urok-2026-11-17/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/news-title-otkrytyj-urok-2026-11-17/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/news-title-otkrytyj-urok-2026-11-17/apply.py
import json
import os
from datetime import datetime

from apps.news.models import NewsPost

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "news-title-otkrytyj-urok-2026-11-17.json")
SLUG = "ochiq-dars-4"
OLD = "Открытий урок"  # Открытий урок
NEW = "Открытый урок"  # Открытый урок

print("MODE:", MODE)
post = NewsPost.objects.filter(slug=SLUG).first()
if post is None:
    raise SystemExit("STOP: news '%s' not found. Nothing was changed." % SLUG)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    saved = json.load(open(BACKUP_FILE, encoding="utf8"))
    post.title_ru = saved["title_ru"]
    post.save(update_fields=["title_ru"])
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: title_ru is back to %r. (the backup file was kept under a new name)" % post.title_ru)
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)
if post.title_ru != OLD:
    raise SystemExit("STOP: title_ru of '%s' is %r, expected %r (already fixed or edited?). Nothing was changed." % (SLUG, post.title_ru, OLD))

print("news %s (id %s): uz=%r en=%r" % (post.slug, post.pk, post.title_uz, post.title_en))
print("   title_ru: %r  ->  %r" % (post.title_ru, NEW))
if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
json.dump({"created": datetime.now().isoformat(), "pk": post.pk, "title_ru": post.title_ru}, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
post.title_ru = NEW
post.save(update_fields=["title_ru"])
print("DONE. To put it back: MODE=undo with the same command.")
print("(the site shows it within about 10 minutes at most)")
