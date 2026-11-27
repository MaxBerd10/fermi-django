# aholini-royxatga-olish-markazlashtirilgan-holda-amalga-oshiriladi: the introduction ends "... qonunning 3-moddasiga asosan," and the seven definitions that continue the
# sentence ("aholini roʻyxatga olish - ...;", "respondentlar - ...", "uy xoʻjaligi - ...") stood as seven loose paragraphs. They become ONE list block (the site draws a list as a
# row of boxes, as on the Ekofaol xodim page). The words are never changed, in uz, ru and en. RUN AFTER scripts 39-87 (a page that differs is SKIPPED and listed).
#
# SAFE BY DESIGN: dry (default) writes nothing; a block group is changed only if every block still has the fingerprints of plan.json; apply is one transaction with a
# backup (a second apply is refused); undo puts the old blocks back, only where the new blocks are still exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-89/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-89/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-89/apply.py
import json
import os

from apps.content.migration_tools import fingerprint_ok, replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page

NAME = "yillik-hisobot-2026-89"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))


def build(apply):
    rows = {"entries": []}
    skipped = []
    for entry in PLAN:
        page = Page.objects.filter(slug=entry["slug"]).first()
        old = list(page.blocks.filter(order__gte=entry["order"], order__lt=entry["order"] + entry["count"]).order_by("order")) if page else []
        if len(old) != entry["count"] or not all(fingerprint_ok(b, fp) for b, fp in zip(old, entry["fp"])):
            skipped.append((entry["slug"], entry["order"], "the blocks are not the ones of the plan (missing or edited since)"))
            continue
        print("%s #%d: %s -> %s" % (entry["slug"], entry["order"], "+".join(b.block_type for b in old), "+".join(b["block_type"] for b in entry["blocks"])))
        if not apply:
            continue
        pks = replace_blocks(page, entry["order"], entry["count"], entry["blocks"])
        created = list(ContentBlock.objects.filter(pk__in=pks).order_by("order"))
        rows["entries"].append({"slug": entry["slug"], "old": [{"block_type": b.block_type, "data": b.data} for b in old],
                                "new": [{"pk": b.pk, "fp": sha(b.data)} for b in created]})
    for slug, order, why in skipped:
        print("SKIPPED %s #%d: %s" % (slug, order, why))
    print("\n%d change(s), %d skipped." % (len(PLAN) - len(skipped), len(skipped)))
    return rows


def undo(rows):
    restored = left = 0
    for entry in reversed(rows["entries"]):
        page = Page.objects.get(slug=entry["slug"])
        current = list(ContentBlock.objects.filter(pk__in=[n["pk"] for n in entry["new"]]).order_by("order"))
        wrote = {n["pk"]: n["fp"] for n in entry["new"]}
        if len(current) != len(wrote) or any(sha(b.data) != wrote.get(b.pk) for b in current):
            left += 1
            print("left %s: the new blocks were edited or removed since" % entry["slug"])
            continue
        replace_blocks(page, current[0].order, len(current), entry["old"])
        restored += 1
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
