# The English pages of the three journal archives (jcpm-2023, jcpm-2024, jcpm-2025) listed the articles under their RUSSIAN titles (the English caption was a copy of the
# Russian one): 157 captions. They now carry an English title. The Uzbek and Russian captions are not touched (the articles are Russian-language; the journal lists them
# in Russian). The English titles are translations (titles_en.json); the ones that are garbled in the source are listed in tarjima-kerak.md.
# RUN AFTER scripts 39-76 (plan made from their result).
#
# SAFE BY DESIGN: dry (default) writes nothing; a caption is changed only if it still is exactly the old one (edited in the admin since -> SKIPPED, and then the apply is
# cancelled as a whole); apply is one transaction with a backup (a second apply is refused); undo puts the old captions back where they still are what this script wrote.
# Only the English caption text is compared: the block also holds the id of its Document row, which differs from database to database.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-77/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-77/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-77/apply.py
import json
import os

from django.utils import timezone

from apps.content.migration_tools import run_modes
from apps.content.models import ContentBlock, Page

NAME = "yillik-hisobot-2026-77"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))


def build(apply):
    rows = {"blocks": []}
    skipped = []
    pages = set()
    for entry in PLAN:
        block = ContentBlock.objects.filter(page__slug=entry["slug"], order=entry["order"]).first()
        if block is None or block.block_type != "document" or block.data["en"].get("caption") != entry["old"]:
            skipped.append((entry["slug"], entry["order"]))
            continue
        pages.add(entry["slug"])
        if apply:
            data = block.data
            data["en"]["caption"] = entry["new"]
            block.data = data
            block.full_clean()
            block.save(update_fields=["data"])
            rows["blocks"].append({"pk": block.pk, "old": entry["old"], "new": entry["new"]})
    for slug in sorted(pages):
        print("%-12s %d captions" % (slug, sum(1 for e in PLAN if e["slug"] == slug)))
    for slug, order in skipped:
        print("SKIPPED %s #%d: the English caption is not the one of the plan (block missing or edited since)" % (slug, order))
    print("\n%d caption(s) changed, %d skipped." % (len(PLAN) - len(skipped), len(skipped)))
    if apply and skipped:
        raise SystemExit("STOP: some captions were skipped, nothing was written (the transaction is cancelled).")
    if apply:
        Page.objects.filter(slug__in=pages).update(updated_at=timezone.now())
    return rows


def undo(rows):
    restored = left = 0
    for entry in rows["blocks"]:
        block = ContentBlock.objects.filter(pk=entry["pk"]).first()
        if block is None or block.data["en"].get("caption") != entry["new"]:
            left += 1
            print("left block %s: it was edited or removed since" % entry["pk"])
            continue
        data = block.data
        data["en"]["caption"] = entry["old"]
        block.data = data
        block.save(update_fields=["data"])
        restored += 1
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
