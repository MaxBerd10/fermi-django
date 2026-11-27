# 17-goals-of-un-policies: three pictures stood at the top, then the 17 policy cards, and between the cards a big photo of the institute (the sign "FERGHANA MEDICAL INSTITUTE OF
# PUBLIC HEALTH 2020") sat before the last card. All four pictures become ONE gallery block of the style "plain" at the top, then a heading "Hujjatlar" and the 18 document cards
# in their old order, all together. 22 blocks become 20. The pictures and cards are the very same files and ids; nothing is added but the heading.
# RUN AFTER scripts 39-94 (the 'plain' gallery style of the frontend is deployed with script 94).
#
# SAFE BY DESIGN: dry (default) writes nothing; the page is changed only if its 22 blocks are still those of script 91 (see plan.json), otherwise nothing is written; apply is one
# transaction with a backup (a second apply is refused); undo puts the 22 old blocks back, only where the new blocks are still exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-95/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-95/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-95/apply.py
import copy
import json
import os

from apps.content.migration_tools import replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image

NAME = "yillik-hisobot-2026-95"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
LANGS = ("uz", "ru", "en")


def old_structure_problem(blocks):
    if sorted(blocks) != list(range(1, 23)):
        return "the page does not have the blocks 1-22 any more"
    for entry in PLAN["old"]:
        block = blocks[entry["order"]]
        if block.block_type != entry["type"]:
            return "block %d is not a %s any more" % (entry["order"], entry["type"])
        if entry["type"] == "image":
            image = Image.objects.filter(pk=block.data["uz"].get("image_id")).first()
            if image is None or image.file.name.rsplit("/", 1)[-1] != entry["file_tail"]:
                return "block %d is another picture" % entry["order"]
        elif entry["type"] == "document":
            if any(block.data[lang].get("caption") != entry["caption"][lang] for lang in LANGS):
                return "block %d has another caption" % entry["order"]
        elif any(sha(block.data[lang]) != entry["fp"][lang] for lang in LANGS):
            return "block %d was edited" % entry["order"]
    return None


def build(apply):
    page = Page.objects.filter(slug=PLAN["slug"]).first()
    blocks = {b.order: b for b in page.blocks.all()} if page else {}
    why = old_structure_problem(blocks) if page else "the page does not exist"
    if why:
        print("SKIPPED:", why)
        print("\n0 change(s), 1 problem(s).")
        if apply:
            raise SystemExit("STOP: the page is not what the plan was made from, nothing was written.")
        return {}
    print("%s: 22 blocks -> 20 (the four pictures one gallery at the top, then 'Hujjatlar' and the 18 cards together)" % PLAN["slug"])
    print("\n1 change(s), 0 skipped.")
    if not apply:
        return {}
    keep = lambda o: {"block_type": blocks[o].block_type, "data": copy.deepcopy(blocks[o].data)}  # noqa: E731

    def gallery(*orders):
        """The picture blocks `orders` as one gallery block: the same image ids, in the same order, in every language."""
        data = {lang: {"style": "plain", "items": [{"image_id": blocks[o].data[lang]["image_id"], "alt": blocks[o].data[lang].get("alt", "")} for o in orders]} for lang in LANGS}
        return {"block_type": "gallery", "data": data}

    new_blocks = [gallery(1, 2, 3, 21), PLAN["documents"]] + [keep(o) for o in range(4, 21)] + [keep(22)]
    assert len(new_blocks) == 20
    old_blocks = [keep(o) for o in range(1, 23)]
    pks = replace_blocks(page, 1, 22, new_blocks)
    return {"slug": PLAN["slug"], "old_blocks": old_blocks, "new_pks": pks, "new_fps": [sha(ContentBlock.objects.get(pk=pk).data) for pk in pks]}


def undo(rows):
    current = list(ContentBlock.objects.filter(pk__in=rows["new_pks"]).order_by("order"))
    if len(current) != len(rows["new_pks"]) or [sha(b.data) for b in current] != rows["new_fps"]:
        print("left %s: the new blocks were edited or removed since" % rows["slug"])
        return
    replace_blocks(Page.objects.get(slug=rows["slug"]), current[0].order, len(current), rows["old_blocks"])
    print("restored the 22 old blocks of %s" % rows["slug"])


run_modes(NAME, build, undo)
