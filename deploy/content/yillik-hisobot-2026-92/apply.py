# The Kongress page ("kongress-2022-2024", menu "Kongress dasturi") was a flat run of 15 blocks: ten pictures of three different conferences with no heading, two YouTube
# videos as legacy <iframe> HTML, two PDF files as plain "Yuklab olish uchun bosing >>>>>> link" lines and one document called just "Kongress". It gets a structure, by the
# conference (the dates are those printed on the posters, the videos are identified by their YouTube titles):
#   IV conference, 10-11 May 2024:  pictures 1-3, the video, the proceedings document (caption "Konferensiya materiallari toʻplami, 2024-yil may" = its file name)
#   III conference, 6 May 2023:     pictures 5-8
#   II conference, 6 May 2022:      pictures 9-11, the video, the two PDF files as document cards (captions = the texts of the old links)
# Nothing is written that is not on the page already, except the headings (ordinal and date of the poster) and the captions named above. The menu label "Konrgress dasturi"
# (a typo) becomes "Kongress dasturi". Needs the 'embed' block type (migration 0009) to be deployed first. RUN AFTER scripts 39-91.
#
# SAFE BY DESIGN: dry (default) writes nothing; the page is changed only if its 15 blocks are still exactly those of plan.json, the two PDF files lie in the media folder and the
# menu label is still the typo, otherwise nothing is written; apply is one transaction with a backup (a second apply is refused); undo puts the 15 old blocks and the old
# label back, only where the new blocks are still exactly what this script wrote, and removes the Document rows it made (never the files).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-92/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-92/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-92/apply.py
import copy
import json
import os

from django.conf import settings

from apps.content.migration_tools import make_document, replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document, Image
from apps.menu.models import MenuItem

NAME = "yillik-hisobot-2026-92"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
LANGS = ("uz", "ru", "en")


def old_structure_problem(blocks):
    """None when the page is still the one of the plan, else a sentence saying what differs."""
    if sorted(blocks) != list(range(1, 16)):
        return "the page does not have the blocks 1-15 any more"
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
    problems = []
    why = old_structure_problem(blocks) if page else "the page does not exist"
    if why:
        problems.append(why)
    for document in PLAN["documents"]:
        if not os.path.isfile(os.path.join(str(settings.MEDIA_ROOT), document["media_path"])):
            problems.append("the file %s is not in the media folder" % document["media_path"])
    menu = list(MenuItem.objects.filter(label_uz=PLAN["menu"]["old_label_uz"]))
    if len(menu) != 1:
        problems.append("the menu label %r is found %d times, not once" % (PLAN["menu"]["old_label_uz"], len(menu)))
    for problem in problems:
        print("SKIPPED:", problem)
    if problems:
        print("\n0 change(s), %d problem(s)." % len(problems))
        if apply:
            raise SystemExit("STOP: the page is not what the plan was made from, nothing was written.")
        return {}
    print("%s: 15 blocks -> 18 (3 headings, 2 videos as 'embed', 2 PDF cards); menu label %r -> %r" % (PLAN["slug"], PLAN["menu"]["old_label_uz"], PLAN["menu"]["new_label_uz"]))
    print("\n1 change(s), 0 skipped.")
    if not apply:
        return {}
    keep = lambda order: {"block_type": blocks[order].block_type, "data": copy.deepcopy(blocks[order].data)}  # noqa: E731
    proceedings = keep(15)
    for lang in LANGS:
        proceedings["data"][lang]["caption"] = PLAN["proceedings_caption"][lang]
        proceedings["data"][lang]["style"] = "attachment"
    created = []
    cards = []
    for spec in PLAN["documents"]:
        document = make_document(os.path.join(str(settings.MEDIA_ROOT), spec["media_path"]), title=spec["captions"]["uz"])
        created.append(document.pk)
        cards.append({"block_type": "document", "data": {lang: {"style": "attachment", "caption": spec["captions"][lang], "document_id": document.pk} for lang in LANGS}})
    new_blocks = (
        [PLAN["heading"]["2024"], keep(1), keep(2), keep(3), PLAN["video_2024"], proceedings]
        + [PLAN["heading"]["2023"], keep(5), keep(6), keep(7), keep(8)]
        + [PLAN["heading"]["2022"], keep(9), keep(10), keep(11), PLAN["video_2022"]]
        + cards
    )
    assert len(new_blocks) == 18
    old_blocks = [keep(order) for order in range(1, 16)]
    pks = replace_blocks(page, 1, 15, new_blocks)
    new_fps = [sha(ContentBlock.objects.get(pk=pk).data) for pk in pks]
    item = menu[0]
    old_label = item.label_uz
    item.label_uz = PLAN["menu"]["new_label_uz"]
    item.save(update_fields=["label_uz"])
    return {"slug": PLAN["slug"], "old_blocks": old_blocks, "new_pks": pks, "new_fps": new_fps, "documents": created, "menu_pk": item.pk, "old_label": old_label,
            "new_label": item.label_uz}


def undo(rows):
    current = list(ContentBlock.objects.filter(pk__in=rows["new_pks"]).order_by("order"))
    if len(current) != len(rows["new_pks"]) or [sha(b.data) for b in current] != rows["new_fps"]:
        print("left %s: the new blocks were edited or removed since" % rows["slug"])
    else:
        replace_blocks(Page.objects.get(slug=rows["slug"]), current[0].order, len(current), rows["old_blocks"])
        Document.objects.filter(pk__in=rows["documents"]).delete()  # the rows only: a deleted row does not delete its file
        print("restored the 15 old blocks of %s" % rows["slug"])
    item = MenuItem.objects.filter(pk=rows["menu_pk"]).first()
    if item is not None and item.label_uz == rows["new_label"]:
        item.label_uz = rows["old_label"]
        item.save(update_fields=["label_uz"])
        print("restored the menu label")
    else:
        print("left the menu label (it was edited since)")


run_modes(NAME, build, undo)
