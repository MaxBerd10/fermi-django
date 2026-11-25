# The captions of the five certificates on "Institut sertifikatlari" were Uzbek in all three languages (they are shown under every certificate): the Russian and the English
# captions of the three faculties (Stomatologiya, Pediatriya, Farmatsiya) and of the accreditation certificate are translated. "UI — 2025" stays as it is (an abbreviation).
#
# SAFE BY DESIGN: dry (default) writes nothing; an item is changed only if its ru/en caption is still the old Uzbek text of plan.json (edited in the admin since -> SKIPPED and listed);
# apply is one transaction with a backup (a second apply is refused); undo puts the old captions back only where they are still exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-53/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-53/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-53/apply.py
import json
import os

from apps.content.migration_tools import run_modes
from apps.content.models import ContentBlock

NAME = "yillik-hisobot-2026-53"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))


def build(apply):
    rows = {"entries": []}
    skipped = []
    for entry in PLAN:
        block = ContentBlock.objects.filter(page__slug=entry["slug"], order=entry["order"], block_type=entry["block_type"]).first()
        for item in entry["items"]:
            for lang, new in item["new"].items():
                items = (block.data.get(lang) or {}).get("items") if block else None
                current = items[item["index"]].get("alt") if items and len(items) > item["index"] else None
                if current != item["old"]:
                    skipped.append("%s %s item %d" % (entry["slug"], lang, item["index"]))
                    continue
                print("%s %s item %d: %s -> %s" % (entry["slug"], lang, item["index"], item["old"][:30], new[:50]))
                if apply:
                    items[item["index"]]["alt"] = new
                    rows["entries"].append({"pk": block.pk, "lang": lang, "index": item["index"], "old": item["old"], "new": new})
        if apply and block is not None:
            block.full_clean()
            block.save()
    for what in skipped:
        print("SKIPPED %s: the caption is not the old one (edited since)" % what)
    print("\n%d caption(s) changed, %d skipped." % (sum(len(i["new"]) for e in PLAN for i in e["items"]) - len(skipped), len(skipped)))
    return rows


def undo(rows):
    restored = left = 0
    for entry in reversed(rows["entries"]):
        block = ContentBlock.objects.filter(pk=entry["pk"]).first()
        items = (block.data.get(entry["lang"]) or {}).get("items") if block else None
        if not items or items[entry["index"]].get("alt") != entry["new"]:
            left += 1
            print("left block %s %s item %d: edited or removed since" % (entry["pk"], entry["lang"], entry["index"]))
            continue
        items[entry["index"]]["alt"] = entry["old"]
        block.full_clean()
        block.save()
        restored += 1
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
