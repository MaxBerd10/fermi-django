# Fix for part 4: the photos of the report pages did not appear. The site's page renderer removes the width and height of an
# image and then a picture marked loading="lazy" stays 0 x 0 pixels and is never fetched. This removes ` loading="lazy"` from the
# photo blocks of part 4 (the blocks whose html holds /images/hisobot/), so the pictures load normally. Nothing else changes.
#
# SAFE BY DESIGN: dry (default) writes nothing; apply saves the old html of every changed block to a backup file (a second apply is
# refused) and writes in one transaction; undo puts the old html back byte for byte.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-5/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-5/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-5/apply.py
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.models import ContentBlock, Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-5.json")
LAZY = ' loading="lazy"'

print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    with transaction.atomic():
        for pk, data in backup["old_data"].items():
            ContentBlock.objects.filter(pk=int(pk)).update(data=data)
        Page.objects.filter(pk__in=backup["pages"]).update(updated_at=timezone.now())
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: the photo blocks are back as they were. (backup kept under a new name)")
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

changes = []  # (block, new_data)
for block in ContentBlock.objects.filter(block_type="raw_html").select_related("page"):
    new = {lang: dict(payload) for lang, payload in block.data.items()}
    changed = False
    for lang, payload in new.items():
        html = payload.get("html", "")
        if "/images/hisobot/" in html and LAZY in html:
            payload["html"] = html.replace(LAZY, "")
            changed = True
    if changed:
        changes.append((block, new))

pages = sorted({b.page.slug for b, _ in changes})
print("\n%d photo blocks in %d pages would lose loading=\"lazy\":" % (len(changes), len(pages)))
for slug in pages:
    print("   %s: %d" % (slug, sum(1 for b, _ in changes if b.page.slug == slug)))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
backup = {"created_at": datetime.now().isoformat(), "pages": sorted({b.page_id for b, _ in changes}), "old_data": {str(b.pk): b.data for b, _ in changes}}
json.dump(backup, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    for block, new in changes:
        block.data = new
        block.save(update_fields=["data"])
    Page.objects.filter(pk__in=backup["pages"]).update(updated_at=timezone.now())
print("DONE: %d photo blocks changed. To put everything back: MODE=undo with the same command." % len(changes))
print("(the site shows it within about 10 minutes at most)")
