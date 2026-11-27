# Language check of the three sections Tanlovlar, Yashil Universitet and Kongress (their 8 pages and 9 news articles), by two independent reviewers reading uz, ru and en side by
# side: (1) on the news article "yashil-universitet-yashil-makon-2" five blocks held the text of ANOTHER block in ru or en (block 9 ru, blocks 14 ru/en, 15 en, 16 en: a sentence of
# one block stood under another, the heading of the 2025 year had an unrelated English heading); they get the translation of their own Uzbek line; (2) the Russian word
# "экочемпионат" (eco-championship) was written "экоклемпион" / "экочемпион"; (3) the name of the institute lost "медицинский" / "Medical" in five places; (4) the English card
# captions of the 17-goals page were garbled ("Policy aims to terminate poverty", "... in Line with the Sustainable") or carried the institute's name as an addition; the captions of
# the Kongress documents carried words/dates the Uzbek caption does not have or lacked them; (5) "Эко-чистый махалля" -> "Эко-чистая махалля". NOT taken over (they need a fact the
# Uzbek text does not give): the Ministry's order of 6 April 2026 on the ekofaol-yoshlar-loyihasi page and two garbled Uzbek sentences: listed for the staff. A correction is a
# whole line (or caption) that becomes another whole line. RUN AFTER scripts 39-95.
# RUN AFTER scripts 39-95.
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if every wording of the plan is found in it exactly once (and the Uzbek start of the block is the
# one of the plan); otherwise it is SKIPPED and the apply is cancelled as a whole; apply is one transaction with a backup (a second apply is refused); undo puts the old
# texts back where the block still is what this script wrote. The blocks hold only text (no media ids).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-96/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-96/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-96/apply.py
import collections
import copy
import json
import os

from django.utils import timezone

from apps.content.migration_tools import run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.news.models import NewsPost

NAME = "yillik-hisobot-2026-96"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))


def texts(data):
    return data["items"] if "items" in data else None


def field_of(part):
    return "items" if "items" in part else "text" if "text" in part else "caption"


def pieces_of(part):
    key = field_of(part)
    return list(part[key]) if key == "items" else [part[key]]


def corrected(block, fixes):
    """The new payload of `block`, or None when a wording is not found exactly once (or the block is not the one of the plan)."""
    data = copy.deepcopy(block.data)
    first_uz = pieces_of(data["uz"])[0]
    if not first_uz.startswith(fixes[0]["anchor"]):
        return None
    for fix in fixes:
        part = data[fix["lang"]]
        pieces = pieces_of(part)
        if sum(piece.count(fix["old"]) for piece in pieces) != 1:
            return None
        pieces = [piece.replace(fix["old"], fix["new"]) for piece in pieces]
        key = field_of(part)
        part[key] = pieces if key == "items" else pieces[0]
    return data


def page_of(entry):
    if "page" in entry:
        return Page.objects.filter(slug=entry["page"]).first()
    post = NewsPost.objects.filter(slug=entry["news"]).first()
    return post.page if post else None


def build(apply):
    rows = {"blocks": []}
    groups = collections.OrderedDict()
    for fix in PLAN:
        groups.setdefault((fix.get("page") or "news:" + fix["news"], fix["order"]), []).append(fix)
    skipped = []
    for (slug, order), fixes in groups.items():
        page = page_of(groups[(slug, order)][0])
        block = ContentBlock.objects.filter(page=page, order=order).first() if page else None
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
