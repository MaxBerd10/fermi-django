# Russian and English text for the 9 annual-report pages (the Uzbek text was copied into ru/en when the pages were created, so
# the admin flags those blocks "needs translation"). The translations are in translations.json (next to this file), written
# from the Uzbek text of the live blocks. Image captions (alt) of the photo blocks are translated too. Uzbek is never touched.
#
# A block is translated only if its Uzbek text is exactly the one that was translated (sha256) AND its ru/en are still the plain
# Uzbek copy. A block someone has edited in the admin since is skipped and listed, never overwritten.
#
# SAFE BY DESIGN: dry (default) writes nothing; apply saves the old data of every changed block to a backup file (a second apply
# is refused) and writes in one transaction; undo puts the old data back (a block edited after apply is skipped and listed).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-7/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-7/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-7/apply.py
import hashlib
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.block_schemas import validate_block_data
from apps.content.models import ContentBlock, Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-7.json")
DATA_FILE = os.environ.get("TRANSLATIONS", "deploy/content/yillik-hisobot-2026-7/translations.json")


def sha(payload):
    return hashlib.sha256(json.dumps(payload, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def same(a, b):
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    restored, skipped = 0, []
    with transaction.atomic():
        for pk, rec in backup["blocks"].items():
            block = ContentBlock.objects.filter(pk=int(pk)).first()
            if block is None or not same(block.data, rec["new"]):
                skipped.append(pk)
                continue
            block.data = rec["old"]
            block.save(update_fields=["data"])
            restored += 1
        Page.objects.filter(pk__in=backup["pages"]).update(updated_at=timezone.now())
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d blocks are back to the Uzbek copy. Skipped (edited since apply): %s. (backup kept under a new name)" % (restored, skipped or "none"))
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)
if not os.path.isfile(DATA_FILE):
    raise SystemExit("STOP: %s not found. Run the command from /home/fermi-django." % DATA_FILE)

PLAN = json.load(open(DATA_FILE, encoding="utf8"))
changes = []  # (block, new_data)
skipped = []
print()
for slug, blocks in PLAN.items():
    page = Page.objects.filter(slug=slug).first()
    if page is None:
        raise SystemExit("STOP: page %s does not exist. Nothing was changed." % slug)
    by_order = {b.order: b for b in page.blocks.all()}
    todo = 0
    for order, rec in blocks.items():
        block = by_order.get(int(order))
        if block is None:
            skipped.append("%s #%s: block is gone" % (slug, order))
            continue
        uz = block.data.get("uz")
        if sha(uz) != rec["sha"]:
            skipped.append("%s #%s: Uzbek text was edited since (not translated)" % (slug, order))
            continue
        if not (same(block.data.get("ru"), uz) and same(block.data.get("en"), uz)):
            skipped.append("%s #%s: ru/en already differ from the Uzbek copy (left as they are)" % (slug, order))
            continue
        new = {"uz": uz, "ru": rec["ru"], "en": rec["en"]}
        validate_block_data(block.block_type, new)
        changes.append((block, new))
        todo += 1
    print("   %-48s %3d blocks to translate (of %d in the plan)" % (slug, todo, len(blocks)))

print("\nTotal: %d blocks to translate, %d skipped." % (len(changes), len(skipped)))
for s in skipped:
    print("   skipped:", s)

print("\nExamples (Uzbek -> Russian / English):")
shown = 0
for block, new in changes:
    if block.block_type in ("heading", "paragraph") and shown < 4:
        print("  [%s #%d]\n     uz: %s\n     ru: %s\n     en: %s" % (block.page.slug, block.order, new["uz"]["text"][:110], new["ru"]["text"][:110], new["en"]["text"][:110]))
        shown += 1

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
pages = sorted({b.page_id for b, _ in changes})
backup = {"created_at": datetime.now().isoformat(), "pages": pages, "blocks": {str(b.pk): {"old": b.data, "new": new} for b, new in changes}}
json.dump(backup, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    for block, new in changes:
        block.data = new
        block.save(update_fields=["data"])
    Page.objects.filter(pk__in=pages).update(updated_at=timezone.now())
print("DONE: %d blocks translated into Russian and English. To put everything back: MODE=undo with the same command." % len(changes))
print("(the site shows it within about 10 minutes at most)")
