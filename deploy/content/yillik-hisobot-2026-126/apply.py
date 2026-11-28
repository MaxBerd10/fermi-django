# Short blocks of the department pages (the user, 2026-11-28: 'do 3'): the audit of 1261 short texts (headings, names, list items) of the 30 department pages in three languages found
# (a) four texts of another block in ru/en: department-29 #31 en (a name instead of 'associate professor of the department'), #50 en (a heading of another block instead of 'the teaching system ...
# approved documents:'), department-20 #78 en (a name instead of 'Dissertation Defenses'), department-19 #46 ru (a text about technical resources instead of the 'approved documents' line);
# (b) 10 Uzbek typos where a word was broken by a space or glued: 'kafedra a ssistenti' x3 (department-11), 'KAFEDRA OC HIQ DARSLARI' x4 (departments 3, 17, 20, 35), the names 'SIDDIQOVObidjonSiddiqovich'
# (department-26), 'Max buba' (department-4), 'D exkanova ... .' (department-7). See make_plan.py. RUN AFTER scripts 39-125.
#
# SAFE BY DESIGN: dry (default) writes nothing; a text is changed only if it still is EXACTLY the text of plan.json, otherwise the whole apply is cancelled (nothing is written); apply is one
# transaction with a backup (a second apply is refused); undo puts the old texts back, only where the text still is exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-126/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-126/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-126/apply.py
import copy
import json
import os

from django.utils import timezone

from apps.content.migration_tools import run_modes
from apps.content.models import ContentBlock, Page

NAME = "yillik-hisobot-2026-126"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))


def build(apply):
    rows = {"fixes": []}
    skipped = []
    blocks = {}
    for fix in PLAN:
        block = blocks.get((fix["slug"], fix["order"])) or ContentBlock.objects.filter(page__slug=fix["slug"], order=fix["order"]).first()
        blocks[(fix["slug"], fix["order"])] = block
        current = (block.data.get(fix["lang"]) or {}).get(fix["field"]) if block is not None else None
        if current is not None and "index" in fix:
            current = current[fix["index"]]
        if current != fix["old"]:
            skipped.append((fix["slug"], fix["order"], fix["lang"], "the text is not the one of the plan (missing or edited since)"))
            continue
        print("%-28s #%-3d %s %-7s %r -> %r" % (fix["slug"][:28], fix["order"], fix["lang"], fix["field"], fix["old"][:34], fix["new"][:40]))
        if apply:
            data = copy.deepcopy(block.data)
            if "index" in fix:
                data[fix["lang"]][fix["field"]][fix["index"]] = fix["new"]
            else:
                data[fix["lang"]][fix["field"]] = fix["new"]
            block.data = data
            rows["fixes"].append({"pk": block.pk, "lang": fix["lang"], "field": fix["field"], "index": fix.get("index"), "old": fix["old"], "new": fix["new"]})
    if apply and not skipped:
        for block in {b.pk: b for b in blocks.values()}.values():
            block.full_clean()
            block.save(update_fields=["data"])
            Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
    for slug, order, lang, why in skipped:
        print("SKIPPED %s #%d %s: %s" % (slug, order, lang, why))
    print("\n%d text(s) changed, %d skipped." % (len(PLAN) - len(skipped), len(skipped)))
    if apply and skipped:
        raise SystemExit("STOP: some texts were skipped, nothing was written (the transaction is cancelled).")
    return rows


def undo(rows):
    restored = left = 0
    blocks = {}
    for fix in rows["fixes"]:
        block = blocks.get(fix["pk"]) or ContentBlock.objects.filter(pk=fix["pk"]).first()
        blocks[fix["pk"]] = block
        now = (block.data.get(fix["lang"]) or {}).get(fix["field"]) if block is not None else None
        if now is not None and fix.get("index") is not None:
            now = now[fix["index"]]
        if block is None or now != fix["new"]:
            left += 1
            print("left block %s %s: the text was edited or removed since" % (fix["pk"], fix["lang"]))
            continue
        data = copy.deepcopy(block.data)
        if fix.get("index") is not None:
            data[fix["lang"]][fix["field"]][fix["index"]] = fix["old"]
        else:
            data[fix["lang"]][fix["field"]] = fix["old"]
        block.data = data
        restored += 1
    for block in blocks.values():
        if block is not None:
            block.save(update_fields=["data"])
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
