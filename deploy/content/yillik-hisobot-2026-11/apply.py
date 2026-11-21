# Fix for two wrong menu labels (Abiturient -> Doktorantura):
#   id 2094  "14.00.01 - Akusherlik va ginekologiya": the English label is Russian text -> "14.00.01 - Obstetrics and gynecology"
#            (same style as the neighbouring English labels of this menu: " - " and a small first letter after the first word)
#   id 2103  "14.00.05-Ichki kasalliklar": the Russian and the English labels are swapped (ru holds "Internal diseases", en holds
#            "Внутренние болезни") -> they are put the right way round. No new translation is made here.
# Nothing else in the menu changes.
#
# SAFE BY DESIGN: dry (default) writes nothing; each item is found by id AND url AND its current labels (anything else = STOP);
# apply saves the old labels to a backup file (a second apply is refused) and writes in one transaction; undo puts the old labels
# back, but only for an item that still holds exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-11/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-11/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-11/apply.py
import json
import os
from datetime import datetime

from django.db import transaction

from apps.menu.models import MenuItem

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-11.json")

RU_14 = "14.00.05 - Internal diseases"
EN_14 = "14.00.05 - Внутренние болезни"  # 14.00.05 - Внутренние болезни
RU_01 = "14.00.01 – Акушерство и гинекология"  # 14.00.01 – Акушерство и гинекология

# id, url, current (ru, en), new (ru, en)
EDITS = [
    (2094, "/blog/2093/140001-akusherlik-va-ginekologiya", (RU_01, RU_01), (RU_01, "14.00.01 - Obstetrics and gynecology")),
    (2103, "/blog/2093/140005-ichki-kasalliklar", (RU_14, EN_14), (EN_14, RU_14)),
]

print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    done = 0
    with transaction.atomic():
        for pk, row in backup["items"].items():
            item = MenuItem.objects.get(pk=int(pk))
            if (item.label_ru, item.label_en) == tuple(row["new"]):
                item.label_ru, item.label_en = row["old"]
                item.save(update_fields=["label_ru", "label_en"])
                done += 1
            else:
                print("skipped item %s: it was edited after this script, left as it is" % pk)
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d menu items restored. (backup kept under a new name)" % done)
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

plan = {}
for pk, url, cur, new in EDITS:
    try:
        item = MenuItem.objects.get(pk=pk)
    except MenuItem.DoesNotExist:
        raise SystemExit("STOP: menu item %d not found." % pk)
    if item.url != url:
        raise SystemExit("STOP: menu item %d has another url (%r)." % (pk, item.url))
    if (item.label_ru, item.label_en) != cur:
        raise SystemExit("STOP: menu item %d does not have the expected labels (already fixed or edited in the admin?): ru=%r en=%r" % (pk, item.label_ru, item.label_en))
    plan[pk] = {"uz": item.label_uz, "old": list(cur), "new": list(new)}
    print("\nitem %d  %s" % (pk, item.label_uz))
    print("   ru NOW  :", cur[0])
    print("   ru AFTER:", new[0])
    print("   en NOW  :", cur[1])
    print("   en AFTER:", new[1])

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
json.dump({"created_at": datetime.now().isoformat(), "items": {str(k): v for k, v in plan.items()}}, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    for pk, row in plan.items():
        item = MenuItem.objects.get(pk=pk)
        item.label_ru, item.label_en = row["new"]
        item.save(update_fields=["label_ru", "label_en"])
print("DONE: %d menu items changed. To put everything back: MODE=undo with the same command." % len(plan))
print("(the site shows it within about 10 minutes at most)")
