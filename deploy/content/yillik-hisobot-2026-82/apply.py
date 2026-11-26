# Two typos of the UZBEK text, both obvious: "Nukus shakar" -> "Nukus shahar" (the user gave the right word; the college address list) and "saqlasʻh" -> "saqlash"
# (a stray modifier apostrophe inside the word, Ministry of Health, in the history of the Fargona technical school). Other typos found in the Uzbek source are NOT touched
# here, because the right wording is a guess ("25.0.2001" has no month, "ush fuqarolar", "OTTda"): they go to the staff.
# RUN AFTER scripts 39-81.
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if every wording of the plan is found in it exactly once (and the Uzbek start of the block is the
# one of the plan); otherwise it is SKIPPED and the apply is cancelled as a whole; apply is one transaction with a backup (a second apply is refused); undo puts the old
# texts back where the block still is what this script wrote. The blocks hold only text (no media ids).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-82/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-82/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-82/apply.py
import collections
import copy
import json
import os

from django.utils import timezone

from apps.content.migration_tools import run_modes, sha
from apps.content.models import ContentBlock, Page

NAME = "yillik-hisobot-2026-82"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))


def texts(data):
    return data["items"] if "items" in data else None


def corrected(block, fixes):
    """The new payload of `block`, or None when a wording is not found exactly once (or the block is not the one of the plan)."""
    data = copy.deepcopy(block.data)
    uz = data["uz"]
    first_uz = (uz["items"][0] if "items" in uz else uz.get("text", ""))
    if not first_uz.startswith(fixes[0]["anchor"]):
        return None
    for fix in fixes:
        part = data[fix["lang"]]
        pieces = part["items"] if "items" in part else [part.get("text", "")]
        if sum(piece.count(fix["old"]) for piece in pieces) != 1:
            return None
        pieces = [piece.replace(fix["old"], fix["new"]) for piece in pieces]
        if "items" in part:
            part["items"] = pieces
        else:
            part["text"] = pieces[0]
    return data


def build(apply):
    rows = {"blocks": []}
    groups = collections.OrderedDict()
    for fix in PLAN:
        groups.setdefault((fix["slug"], fix["order"]), []).append(fix)
    skipped = []
    for (slug, order), fixes in groups.items():
        block = ContentBlock.objects.filter(page__slug=slug, order=order).first()
        new = corrected(block, fixes) if block is not None else None
        if new is None:
            skipped.append((slug, order))
            continue
        print("%-50s #%-3d %d correction(s): %s" % (slug[:50], order, len(fixes), "; ".join(f["lang"] for f in fixes)))
        if apply:
            old = block.data
            block.data = new
            block.full_clean()
            block.save(update_fields=["data"])
            Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
            rows["blocks"].append({"pk": block.pk, "old": old, "new_fp": sha(block.data)})
    for slug, order in skipped:
        print("SKIPPED %s #%d: the wording is not the one of the plan (block missing or edited since)" % (slug, order))
    print("\n%d block(s) changed (%d corrections), %d skipped." % (len(groups) - len(skipped), len(PLAN), len(skipped)))
    if apply and skipped:
        raise SystemExit("STOP: some blocks were skipped, nothing was written (the transaction is cancelled).")
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
