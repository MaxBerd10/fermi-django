# ilmiy-konferensiyalar (conference proceedings) and kop-berilayotgan-savollar: the language audit of the pages changed in this clean-up found
#  * ilmiy-konferensiyalar: the English caption of the second collection was the translation of the THIRD one (a shift: it moves to its own collection, #3), the Russian caption of
#    the second had a Latin "a" and spaces inside "Достижения"; its Uzbek caption was the Russian title (now an Uzbek translation of it, and an English one: MY translations of the
#    Russian title, to be checked by the user); two collections (#5, #20) had the Uzbek caption in all three languages (ru, en translated by me); about 25 plain letter errors in the
#    captions ("Актувльные", "диангостики", "Пепспективы", "иммунодефитцитов", "diagnossis", "issies", "kasallikalr", "Dermatoveneralogiya", "konfrensiyasi", ...) and one English
#    heading ("The role innovation in ..." -> "The role of innovation in ... medicine and education").
#  * kop-berilayotgan-savollar: in the Uzbek text the words "fermi.uz" linked to the page itself (/blog/241/kop-berilayotgan-savollar); ru and en link to https://fermi.uz, now uz does too.
# The documents, their order and every other text stay as they are. RUN AFTER scripts 39-103.
#
# SAFE BY DESIGN: dry (default) writes nothing; a text is changed only if it still is EXACTLY the text of plan.json, otherwise the whole apply is cancelled (nothing is written); apply is one
# transaction with a backup (a second apply is refused); undo puts the old texts back, only where the text still is exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-104/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-104/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-104/apply.py
import copy
import json
import os

from django.utils import timezone

from apps.content.migration_tools import run_modes
from apps.content.models import ContentBlock, Page

NAME = "yillik-hisobot-2026-104"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))


def build(apply):
    rows = {"fixes": []}
    skipped = []
    blocks = {}
    for fix in PLAN:
        block = blocks.get((fix["slug"], fix["order"])) or ContentBlock.objects.filter(page__slug=fix["slug"], order=fix["order"]).first()
        blocks[(fix["slug"], fix["order"])] = block
        current = (block.data.get(fix["lang"]) or {}).get(fix["field"]) if block is not None else None
        if current != fix["old"]:
            skipped.append((fix["slug"], fix["order"], fix["lang"], "the text is not the one of the plan (missing or edited since)"))
            continue
        print("%-28s #%-3d %s %-7s %r -> %r" % (fix["slug"][:28], fix["order"], fix["lang"], fix["field"], fix["old"][:34], fix["new"][:40]))
        if apply:
            data = copy.deepcopy(block.data)
            data[fix["lang"]][fix["field"]] = fix["new"]
            block.data = data
            rows["fixes"].append({"pk": block.pk, "lang": fix["lang"], "field": fix["field"], "old": fix["old"], "new": fix["new"]})
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
        if block is None or (block.data.get(fix["lang"]) or {}).get(fix["field"]) != fix["new"]:
            left += 1
            print("left block %s %s: the text was edited or removed since" % (fix["pk"], fix["lang"]))
            continue
        data = copy.deepcopy(block.data)
        data[fix["lang"]][fix["field"]] = fix["old"]
        block.data = data
        restored += 1
    for block in blocks.values():
        if block is not None:
            block.save(update_fields=["data"])
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
