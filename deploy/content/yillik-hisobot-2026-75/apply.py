# The 19 annexes of the Ministry of Health's anti-corruption policy (page ssv-korrupsiyaga-qarshi-kurashish-siyosati) were cards named only "1-ilova" ...
# "14-ilova" (ru "Приложение 1", en "Annex 1"). Each card now says what the document is: "1-ilova: Sogʻliqni saqlash vazirligining korrupsiyaga qarshi
# kurashish boʻyicha siyosati". The names come from the first page of every PDF (the Uzbek ones were checked against the PDF text); the Russian and English
# are translations (listed in tarjima-kerak.md for a native reader).
# RUN AFTER scripts 39-74 (plan made from their result).
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if every language still is exactly what the plan was made from (edited in the admin since ->
# SKIPPED); apply is one transaction with a backup (a second apply is refused); undo puts the old texts back where the block still is what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-75/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-75/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-75/apply.py
import json
import os

from django.utils import timezone

from apps.content.migration_tools import fingerprint_ok, run_modes, sha
from apps.content.models import ContentBlock, Page

NAME = "yillik-hisobot-2026-75"
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
