# department-35 #10 (Yusupova Rano Turdiyevna): the years of her work as associate professor of the department were written 1944-2019 in
# Uzbek, Russian and English. She was born in 1944 (see block #11, and department-26 #17 which says 1994-2019), so the first year must be
# 1994. Confirmed by the site owner. Only the first year changes, in all three languages of this one block.
#
# SAFE BY DESIGN: dry (default) writes nothing; the block is found by page slug + order and every old fragment must occur exactly once
# (anything else = STOP); apply saves the old data to a backup file (a second apply is refused) and writes in one transaction; undo puts
# the old data back, but only for a block that still holds exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-22/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-22/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-22/apply.py
import copy
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.models import ContentBlock, Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-22.json")

# (page slug, order, language, old fragment, new fragment)  -- written with \u escapes on purpose
EDITS = [
    ("department-35", 10, "uz", "1944\u20132019-yillarda", "1994\u20132019-yillarda"),
    ("department-35", 10, "ru", "1944\u20132019 \u0433\u043e\u0434\u0430\u0445", "1994\u20132019 \u0433\u043e\u0434\u0430\u0445"),
    ("department-35", 10, "en", "in 1944-2019", "in 1994-2019"),
]

print("MODE:", MODE)

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
for slug, order, lang, old, new in EDITS:
    qs = ContentBlock.objects.filter(page__slug=slug, order=order)
    if qs.count() != 1:
        raise SystemExit("STOP: expected exactly one block %s#%s, found %d." % (slug, order, qs.count()))
    block = qs.get()
    if block.block_type != "paragraph":
        raise SystemExit("STOP: block %s#%s is not a paragraph." % (slug, order))
    row = plan.setdefault(block.pk, {"page": slug, "order": order, "old": copy.deepcopy(block.data), "new": copy.deepcopy(block.data)})
    text = row["new"][lang]["text"]
    if text.count(old) != 1:
        raise SystemExit("STOP: block %s#%s (%s): expected exactly one %r, found %d (already fixed or edited in the admin?)." % (slug, order, lang, old, text.count(old)))
    row["new"][lang]["text"] = text.replace(old, new)
    i = text.index(old)
    print("\n%s #%s [%s]\n   NOW  : ...%s...\n   AFTER: ...%s..." % (slug, order, lang, text[max(0, i - 25):i + len(old) + 25], row["new"][lang]["text"][max(0, i - 25):i + len(new) + 25]))

if MODE == "dry":
    print("\n%d edits in %d blocks. DRY RUN: nothing was changed. Run again with MODE=apply." % (len(EDITS), len(plan)))
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
json.dump({"created_at": datetime.now().isoformat(), "blocks": {str(pk): r for pk, r in plan.items()}}, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    for pk, r in plan.items():
        block = ContentBlock.objects.get(pk=pk)
        block.data = r["new"]
        block.save(update_fields=["data"])
        Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
print("DONE: %d edits in %d blocks. To put everything back: MODE=undo with the same command." % (len(EDITS), len(plan)))
print("(the site shows it within about 10 minutes at most)")
