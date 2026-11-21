# Spelling of one name in the page "Moliya, oquv-uslubiy ishlar va raqamlashtirish" (table of the heads of the institute, 2018-2021):
# the user confirmed the right spelling is "Gʻafurjon" (the Russian text already says "Гафуржон"). The report PDF, and so the
# uz and en table cells, had "Gʻafurdjon". This changes "afurdjon" -> "afurjon" in every content block that holds it.
# Expected: exactly 2 text cells (uz: "Sultanov Gʻafurdjon", en: "Gʻafurdjon Sultanov") in one block. If the script finds more or
# fewer, it STOPS and lists them, so nothing unexpected is changed.
#
# SAFE BY DESIGN: dry (default) writes nothing; apply saves the old data of the changed block to a backup file (a second apply is
# refused) and writes in one transaction; undo puts the old data back, but only if the block still holds what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-12/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-12/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-12/apply.py
import copy
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.models import ContentBlock, Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-12.json")
OLD, NEW = "afurdjon", "afurjon"
EXPECTED_HITS = 2

print("MODE:", MODE)


def fix(value, hits, path=""):
    """Return value with OLD replaced by NEW in every string; hits collects (path, before, after)."""
    if isinstance(value, str):
        if OLD in value:
            after = value.replace(OLD, NEW)
            hits.append((path, value, after))
            return after
        return value
    if isinstance(value, list):
        return [fix(v, hits, "%s[%d]" % (path, i)) for i, v in enumerate(value)]
    if isinstance(value, dict):
        return {k: fix(v, hits, "%s/%s" % (path, k)) for k, v in value.items()}
    return value


if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    done = 0
    with transaction.atomic():
        for pk, row in backup["blocks"].items():
            block = ContentBlock.objects.get(pk=int(pk))
            if block.data == row["new"]:
                block.data = row["old"]
                block.save(update_fields=["data"])
                Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
                done += 1
            else:
                print("skipped block %s: it was edited after this script, left as it is" % pk)
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d blocks restored. (backup kept under a new name)" % done)
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

plan = {}
total = 0
for block in ContentBlock.objects.select_related("page"):
    hits = []
    new = fix(copy.deepcopy(block.data), hits)
    if hits:
        plan[block.pk] = {"page": block.page.slug, "order": block.order, "old": block.data, "new": new}
        total += len(hits)
        for path, before, after in hits:
            print("%s #%s  %s\n    NOW  : %s\n    AFTER: %s" % (block.page.slug, block.order, path, before, after))

print("\n%d text cells in %d blocks would change (expected %d)." % (total, len(plan), EXPECTED_HITS))
if total != EXPECTED_HITS:
    raise SystemExit("STOP: found a different number of places than expected. Nothing was changed; tell Claude what is listed above.")

if MODE == "dry":
    print("DRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
json.dump({"created_at": datetime.now().isoformat(), "blocks": {str(pk): {"old": r["old"], "new": r["new"], "page": r["page"], "order": r["order"]} for pk, r in plan.items()}},
          open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("backup saved:", BACKUP_FILE)
with transaction.atomic():
    for pk, r in plan.items():
        block = ContentBlock.objects.get(pk=pk)
        block.data = r["new"]
        block.save(update_fields=["data"])
        Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
print("DONE: %d blocks changed. To put everything back: MODE=undo with the same command." % len(plan))
print("(the site shows it within about 10 minutes at most)")
