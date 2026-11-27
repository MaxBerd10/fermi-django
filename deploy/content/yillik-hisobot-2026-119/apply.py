# prezident-farmon-va-qarorlari: the LEX.UZ cards and the PDF cards were mixed (LEX x5, PDF x5, LEX, PDF): the one LEX.UZ card that stood among the PDFs (#11) moves up to the other LEX.UZ cards,
# so all LEX.UZ cards stand together and all PDFs (the President's decree of 3 December 2020, the last block, included) together. Only the ORDER of the blocks changes: the blocks keep their ids and
# texts. See make_plan.py. RUN AFTER scripts 39-118.
#
# SAFE BY DESIGN: dry (default) writes nothing; the order is changed only if every block is still at the place the plan expects (the beginning of its text), otherwise nothing is written; apply is one
# transaction with a backup (a second apply is refused); undo puts the old order back, only where the blocks still stand where this script put them.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-119/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-119/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-119/apply.py
import json
import os

from django.utils import timezone

from apps.content.migration_tools import run_modes
from apps.content.models import ContentBlock, Page

NAME = "yillik-hisobot-2026-119"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
TEMP = 10000


def text_of(block):
    return ((block.data.get("uz") or {}).get("text") or "") if block is not None else ""


def problems():
    page = Page.objects.filter(slug=PLAN["slug"]).first()
    if page is None:
        return None, ["the page does not exist"]
    bad = []
    for move in PLAN["moves"]:
        block = page.blocks.filter(order=move["old"]).first()
        if block is None or not text_of(block).startswith(move["sig"]):
            bad.append("block %d is not the one of the plan (missing or edited since)" % move["old"])
    for order, kind in PLAN["unmoved_check"].items():
        block = page.blocks.filter(order=int(order)).first()
        if block is None or block.block_type != kind:
            bad.append("block %s is not a %s any more" % (order, kind))
    return page, bad


def build(apply):
    page, bad = problems()
    for move in PLAN["moves"]:
        print("%-32s #%-2d -> #%-2d  %s" % (PLAN["slug"], move["old"], move["new"], move["sig"][:48]))
    for why in bad:
        print("SKIPPED:", why)
    print("\n%d move(s), %d problem(s)." % (len(PLAN["moves"]), len(bad)))
    if apply and bad:
        raise SystemExit("STOP: the page is not what the plan was made from, nothing was written.")
    if not apply:
        return {}
    pks = {move["old"]: page.blocks.get(order=move["old"]).pk for move in PLAN["moves"]}
    for move in PLAN["moves"]:  # everything out of the way first, so that no two blocks ever hold the same place
        ContentBlock.objects.filter(pk=pks[move["old"]]).update(order=TEMP + move["old"])
    for move in PLAN["moves"]:
        ContentBlock.objects.filter(pk=pks[move["old"]]).update(order=move["new"])
    Page.objects.filter(pk=page.pk).update(updated_at=timezone.now())
    return {"moves": [{"pk": pks[m["old"]], "old": m["old"], "new": m["new"]} for m in PLAN["moves"]]}


def undo(rows):
    moved = rows["moves"]
    left = [m for m in moved if ContentBlock.objects.filter(pk=m["pk"], order=m["new"]).count() != 1]
    if left:
        print("left: %d block(s) are not where this script put them (edited or moved since); nothing was undone." % len(left))
        return
    for m in moved:
        ContentBlock.objects.filter(pk=m["pk"]).update(order=TEMP + m["old"])
    for m in moved:
        ContentBlock.objects.filter(pk=m["pk"]).update(order=m["old"])
    page = ContentBlock.objects.get(pk=moved[0]["pk"]).page
    Page.objects.filter(pk=page.pk).update(updated_at=timezone.now())
    print("restored the old order of %d block(s)." % len(moved))


run_modes(NAME, build, undo)
