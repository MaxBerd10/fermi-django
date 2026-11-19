# Removes the "Soʻx modeli" card from the home page section "Bizning loyihalar" (the card added in part 2). Nothing else changes:
# the "Soʻx modeli" page (/sox-modeli), its menu entry (Institut -> FJSTI Ilmiy jurnali) and the iShifo card stay.
#
# SAFE BY DESIGN: dry (default) writes nothing; apply saves the whole card (every field) to a backup file (a second apply is
# refused) and deletes only that one card; undo creates the card again from the backup (same place, same texts, same picture).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-6/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-6/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-6/apply.py
import json
import os
from datetime import datetime

from apps.site_settings.models import HomeItem

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-6.json")
URL = "/sox-modeli"
FIELDS = ["section", "order", "is_active", "title_uz", "title_ru", "title_en", "subtitle_uz", "subtitle_ru", "subtitle_en", "text_uz", "text_ru", "text_en", "value", "url", "icon", "image_path"]

print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    row = json.load(open(BACKUP_FILE, encoding="utf8"))["card"]
    if HomeItem.objects.filter(section=HomeItem.PROJECT, url=URL).exists():
        raise SystemExit("STOP: the card is already there. Nothing was changed.")
    item = HomeItem.objects.create(**row)
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: the Soʻx modeli card is back (id %s). (backup kept under a new name)" % item.pk)
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

cards = list(HomeItem.objects.filter(section=HomeItem.PROJECT, url=URL))
if len(cards) != 1:
    raise SystemExit("STOP: expected exactly one project card with the link %s, found %d. Nothing was changed." % (URL, len(cards)))
card = cards[0]
print("\nThe card to remove: id %s, %r / %r / %r, link %s, order %s" % (card.pk, card.title_uz, card.title_ru, card.title_en, card.url, card.order))
print("The other project cards stay:", [c.title_uz for c in HomeItem.objects.filter(section=HomeItem.PROJECT).exclude(pk=card.pk).order_by("order", "id")])

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
json.dump({"created_at": datetime.now().isoformat(), "card": {f: getattr(card, f) for f in FIELDS}}, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
card.delete()
print("DONE: the Soʻx modeli card is removed. To put it back: MODE=undo with the same command.")
print("(the site shows it within about 10 minutes at most)")
