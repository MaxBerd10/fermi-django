# Five small text fixes found while checking the pages (the words, no structure):
#   * magistratura-qabul-hujjatlari-toplami: "1-iyuldan 31-iyulgacha" -> "30-iyulgacha" (uz, ru, en). The Ministry of Higher Education announced that
#     documents for 2025/2026 are accepted until 30 July (that day included); the same page and the page on the online registration already say 30.
#   * xalqaro-qabul-hujjatlar-toplami: two Uzbek sentences were glued ("...nomiga arizaAbituriyent..."): split, and the line that introduces the list.
#   * buxgalteriya-bolimi (2 lists): "Akademiya" / "Академия" / "Academy" -> "Institut" / "Институт" / "Institute" (words of another institution).
#   * fuqarolar-murojaatlari-statistikasi: the Uzbek title of the report lacked its last word ("... taxliliy yozma" -> "... taxliliy yozma axborot").
# RUN AFTER scripts 39-73 (plan made from their result).
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if every language still is exactly what the plan was made from (edited in the admin since ->
# SKIPPED); apply is one transaction with a backup (a second apply is refused); undo puts the old texts back where the block still is what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-74/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-74/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-74/apply.py
import json
import os

from django.utils import timezone

from apps.content.migration_tools import fingerprint_ok, run_modes, sha
from apps.content.models import ContentBlock, Page

NAME = "yillik-hisobot-2026-74"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))


def build(apply):
    rows = {"blocks": []}
    skipped = []
    for entry in PLAN:
        block = ContentBlock.objects.filter(page__slug=entry["slug"], order=entry["order"]).first()
        if block is None or not fingerprint_ok(block, entry["fp"]):
            skipped.append((entry["slug"], entry["order"]))
            continue
        print("%-52s #%-3d %s" % (entry["slug"][:52], entry["order"], entry["why"]))
        if apply:
            old = block.data
            block.data = entry["data"]
            block.full_clean()
            block.save(update_fields=["data"])
            Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
            rows["blocks"].append({"pk": block.pk, "old": old, "new_fp": sha(block.data)})
    for slug, order in skipped:
        print("SKIPPED %s #%d: the block is not the one of the plan (missing or edited since)" % (slug, order))
    print("\n%d block(s) changed, %d skipped." % (len(PLAN) - len(skipped), len(skipped)))
    return rows


def undo(rows):
    restored = left = 0
    for entry in rows["blocks"]:
        block = ContentBlock.objects.filter(pk=entry["pk"]).first()
        if block is None or sha(block.data) != entry["new_fp"]:
            left += 1
            print("left block %s: it was edited or removed since" % entry["pk"])
            continue
        block.data = entry["old"]
        block.save(update_fields=["data"])
        restored += 1
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
