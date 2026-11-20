# Fix: the English photo captions (alt text) of two blocks on the page "2027-yil-vazifalari-batafsil" were written with straight
# double quotes INSIDE the alt="..." attribute, e.g. alt=""Fergana Health Park" (concept visualisation), 1". The browser then cuts the
# attribute at the first inner quote, so these 11 pictures lose their description (and carry stray attributes). This replaces the inner
# straight quotes by typographic quotes (“ ”). Only the English html of the two blocks changes; uz and ru are not touched.
#
# SAFE BY DESIGN: dry (default) writes nothing; apply saves the old data of the two blocks to a backup file (a second apply is refused)
# and writes in one transaction; undo puts the old html back, but only if the block still holds exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-10/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-10/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-10/apply.py
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.models import ContentBlock, Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-10.json")
SLUG = "2027-yil-vazifalari-batafsil"
LQ, RQ = "“", "”"

# (order, old fragment, new fragment, how many times it must occur)
EDITS = [
    (28, 'alt="The "Artificial Intelligence in Medicine" programme"',
         'alt="The ' + LQ + 'Artificial Intelligence in Medicine' + RQ + ' programme"', 1),
    (32, 'alt=""Fergana Health Park" (concept',
         'alt="' + LQ + 'Fergana Health Park' + RQ + ' (concept', 10),
]

print("MODE:", MODE)
try:
    page = Page.objects.get(slug=SLUG)
except Page.DoesNotExist:
    raise SystemExit("STOP: page %s not found." % SLUG)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    done = 0
    with transaction.atomic():
        for pk, row in backup["blocks"].items():
            block = ContentBlock.objects.get(pk=int(pk))
            if block.data.get("en", {}).get("html") == row["new_html"]:
                block.data["en"]["html"] = row["old_html"]
                block.save(update_fields=["data"])
                done += 1
            else:
                print("skipped block %s: it was edited after this script, left as it is" % pk)
        Page.objects.filter(pk=page.pk).update(updated_at=timezone.now())
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d blocks restored. (backup kept under a new name)" % done)
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

plan = {}  # pk -> {old_html, new_html}
for order, old, new, count in EDITS:
    qs = ContentBlock.objects.filter(page=page, order=order)
    if qs.count() != 1:
        raise SystemExit("STOP: expected exactly one block %s#%s, found %d." % (SLUG, order, qs.count()))
    block = qs.get()
    if block.block_type != "raw_html":
        raise SystemExit("STOP: block %s#%s is not raw_html." % (SLUG, order))
    html = block.data["en"]["html"]
    found = html.count(old)
    if found != count:
        raise SystemExit("STOP: block %s#%s: expected %d x %r, found %d (already fixed or edited in the admin?)." % (SLUG, order, count, old, found))
    plan[block.pk] = {"order": order, "old_html": html, "new_html": html.replace(old, new)}
    print("block %s#%s (pk %s): %d captions would be fixed" % (SLUG, order, block.pk, found))

if MODE == "dry":
    for pk, row in plan.items():
        print("\n--- block", pk, "NOW:\n", row["old_html"][:230], "\n--- block", pk, "AFTER:\n", row["new_html"][:230])
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
backup = {"created_at": datetime.now().isoformat(), "page": SLUG, "blocks": {str(pk): row for pk, row in plan.items()}}
json.dump(backup, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    for pk, row in plan.items():
        block = ContentBlock.objects.get(pk=pk)
        block.data["en"]["html"] = row["new_html"]
        block.save(update_fields=["data"])
    Page.objects.filter(pk=page.pk).update(updated_at=timezone.now())
print("DONE: %d blocks changed (11 English captions). To put everything back: MODE=undo with the same command." % len(plan))
print("(the site shows it within about 10 minutes at most)")
