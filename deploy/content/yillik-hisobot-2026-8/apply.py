# Small fix to the Russian text of two report pages (part 7): two Indian personal names that stayed in Latin, and the abbreviations
# of the Uzbek universities in the olympiad table, written the way they are normally written in Russian:
#   Dr. M. Mahajan -> Д-р М. Махаджан;  Dr. L.K. Tripathi -> Д-р Л. К. Трипати
#   TDTU -> ТГМУ (Ташкентский государственный медицинский университет), UrDU -> УрГУ, ADTI -> АГМИ, TDSI -> ТГСИ, OʻshDU -> ОшГУ
# Only the Russian table cells listed below change; the Uzbek and English text is not touched.
#
# SAFE BY DESIGN: dry (default) writes nothing; apply saves the old data of the two blocks to a backup file (a second apply is
# refused) and writes in one transaction; undo puts the old data back (a block edited after apply is skipped and listed).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-8/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-8/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-8/apply.py
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.block_schemas import validate_block_data
from apps.content.models import Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-8.json")

# (page slug, block order, old text in a Russian table cell, new text, how many times it must occur in the block)
EDITS = [
    ("xalqaro-hamkorlik-va-investitsiyalar", 15, "Dr. M. Mahajan", "Д-р М. Махаджан", 1),
    ("xalqaro-hamkorlik-va-investitsiyalar", 15, "Dr. L.K. Tripathi", "Д-р Л. К. Трипати", 1),
    ("manaviy-marifiy-ishlar-va-olimpiadalar", 5, "(TDTU)", "(ТГМУ)", 5),
    ("manaviy-marifiy-ishlar-va-olimpiadalar", 5, "(UrDU)", "(УрГУ)", 1),
    ("manaviy-marifiy-ishlar-va-olimpiadalar", 5, "(ADTI)", "(АГМИ)", 1),
    ("manaviy-marifiy-ishlar-va-olimpiadalar", 5, "(TDSI)", "(ТГСИ)", 1),
    ("manaviy-marifiy-ishlar-va-olimpiadalar", 5, "(OʻshDU)", "(ОшГУ)", 1),
]


def same(a, b):
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    restored, skipped = 0, []
    with transaction.atomic():
        for key, rec in backup["blocks"].items():
            page = Page.objects.filter(slug=rec["slug"]).first()
            block = page.blocks.filter(order=rec["order"]).first() if page else None
            if block is None or not same(block.data, rec["new"]):
                skipped.append(key)
                continue
            block.data = rec["old"]
            block.save(update_fields=["data"])
            restored += 1
        Page.objects.filter(slug__in=backup["slugs"]).update(updated_at=timezone.now())
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d blocks are back as they were. Skipped (edited since apply): %s. (backup kept under a new name)" % (restored, skipped or "none"))
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

blocks = {}  # (slug, order) -> [block, old_data, new_data]
for slug, order, old, new, count in EDITS:
    key = (slug, order)
    if key not in blocks:
        page = Page.objects.filter(slug=slug).first()
        block = page.blocks.filter(order=order).first() if page else None
        if block is None or block.block_type != "table":
            raise SystemExit("STOP: %s block #%d (a table) not found. Nothing was changed." % (slug, order))
        blocks[key] = [block, json.loads(json.dumps(block.data)), json.loads(json.dumps(block.data))]
    ru = blocks[key][2]["ru"]
    found = sum(cell.count(old) for row in ru["rows"] for cell in row)
    if found != count:
        raise SystemExit("STOP: %r occurs %d times in %s #%d, expected %d (already changed, or edited in the admin?). Nothing was changed." % (old, found, slug, order, count))
    ru["rows"] = [[cell.replace(old, new) for cell in row] for row in ru["rows"]]
    print("   %-40s #%-2d %r -> %r  (%d)" % (slug, order, old, new, count))

for key, (block, old_data, new_data) in blocks.items():
    validate_block_data(block.block_type, new_data)
    print("\nRussian table after the change, %s #%d:" % key)
    for row in new_data["ru"]["rows"]:
        if any(("ТГМУ" in c or "УрГУ" in c or "АГМИ" in c or "ТГСИ" in c or "ОшГУ" in c or "Махаджан" in c or "Трипати" in c) for c in row):
            print("   ", " | ".join(row))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
slugs = sorted({k[0] for k in blocks})
backup = {"created_at": datetime.now().isoformat(), "slugs": slugs,
          "blocks": {"%s#%d" % k: {"slug": k[0], "order": k[1], "old": v[1], "new": v[2]} for k, v in blocks.items()}}
json.dump(backup, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    for key, (block, old_data, new_data) in blocks.items():
        block.data = new_data
        block.save(update_fields=["data"])
    Page.objects.filter(slug__in=slugs).update(updated_at=timezone.now())
print("DONE: %d blocks changed. To put everything back: MODE=undo with the same command." % len(blocks))
print("(the site shows it within about 10 minutes at most)")
