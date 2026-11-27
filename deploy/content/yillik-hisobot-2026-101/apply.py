# Two pages of the Bakalavriat menu, as the user saw them ("shu bolim linklar va tableni qara hunuk"):
#  talabalar-turar-joyi-uchun-ariza-yuborish: the link of the my.gov.uz service was broken in uz/ru/en (the address was glued to a pasted "(" ... ")": http://%28https://...%29, it
#    pointed to a page of no site); a stray "(" in an Uzbek sentence ("ustuvorliklarga (ega talabgorlar"); the three percentages (55-65, 15-20, 20-25) stood as three loose lines
#    (now ONE list); the poster at the top stays at the top (a gallery of the style "plain": the article layout had moved it behind the text and made the next line its caption); the title of the decree No 376 was cut into two headings and a line (now ONE heading and the line, which links to the decree on lex.uz, the one the first paragraph names).
#  grantlar-taqsimoti: the two 11-column tables repeated a nine-line heading ("<period> - <kind of grant> - Jami") in every column; now three GROUP headings over three short columns
#    (Jami / oʻzbek / rus), the words are exactly those of the old headings; the two notes (* and **), run together in one line, are two lines.
# NEEDS the frontend and backend of this commit deployed first: the table block gets an optional `header_groups` (validated by the backend, drawn by the frontend). RUN AFTER scripts 39-100.
#
# SAFE BY DESIGN: dry (default) writes nothing; a place is changed only if its blocks still are EXACTLY what plan.json was made from (type and payload, all languages), otherwise the
# whole apply is cancelled (nothing is written); apply is one transaction with a backup (a second apply is refused); undo puts the old blocks back, only where the new blocks are still
# exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-101/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-101/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-101/apply.py
import json
import os

from apps.content.migration_tools import replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image

NAME = "yillik-hisobot-2026-101"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))


LANGS = ("uz", "ru", "en")


def picture_gallery(block):
    """The gallery block (style "plain") that shows the very same picture as the image block `block`, in every language."""
    return {"block_type": "gallery", "data": {lang: {"style": "plain", "items": [{"image_id": block.data[lang]["image_id"], "alt": block.data[lang].get("alt", "")}]} for lang in LANGS}}


def problem(op):
    page = Page.objects.filter(slug=op["slug"]).first()
    if page is None:
        return "the page does not exist"
    if "picture_tail" in op:
        block = page.blocks.filter(order=op["order"]).first()
        image = Image.objects.filter(pk=block.data["uz"].get("image_id")).first() if block is not None and block.block_type == "image" else None
        if image is None or image.file.name.rsplit("/", 1)[-1] != op["picture_tail"]:
            return "block %d is not the picture of the plan" % op["order"]
        return None
    for offset, old in enumerate(op["old"]):
        block = page.blocks.filter(order=op["order"] + offset).first()
        if block is None or block.block_type != old["block_type"] or block.data != old["data"]:
            return "block %d is not what the plan was made from (missing or edited since)" % (op["order"] + offset)
    return None


def build(apply):
    rows = {"ops": []}
    skipped = []
    # from the end of a page to its start, so that a change that adds or removes blocks does not move the places of the ones still to do
    for op in sorted(PLAN, key=lambda o: (o["slug"], -o["order"])):
        why = problem(op)
        if why:
            skipped.append((op["slug"], op["order"], why))
            continue
        print("%-42s #%-2d %d block(s) -> %s" % (op["slug"], op["order"], op["count"], "picture -> gallery (plain)" if "picture_tail" in op else "%d: %s" % (len(op["new"]), "/".join(b["block_type"] for b in op["new"]))))
        if not apply:
            continue
        page = Page.objects.get(slug=op["slug"])
        if "picture_tail" in op:
            picture = page.blocks.get(order=op["order"])
            old, new = [{"block_type": picture.block_type, "data": picture.data}], [picture_gallery(picture)]
        else:
            old, new = op["old"], op["new"]
        pks = replace_blocks(page, op["order"], op["count"], new)
        rows["ops"].append({"slug": op["slug"], "order": op["order"], "old": old, "new_pks": pks, "new_fps": [sha(ContentBlock.objects.get(pk=pk).data) for pk in pks]})
    for slug, order, why in skipped:
        print("SKIPPED %s #%d: %s" % (slug, order, why))
    print("\n%d change(s), %d skipped." % (len(PLAN) - len(skipped), len(skipped)))
    if apply and skipped:
        raise SystemExit("STOP: some places were skipped, nothing was written (the transaction is cancelled).")
    return rows


def undo(rows):
    restored = left = 0
    for op in reversed(rows["ops"]):
        current = list(ContentBlock.objects.filter(pk__in=op["new_pks"]).order_by("order"))
        if len(current) != len(op["new_pks"]) or [sha(b.data) for b in current] != op["new_fps"]:
            left += 1
            print("left %s #%d: the new blocks were edited or removed since" % (op["slug"], op["order"]))
            continue
        replace_blocks(Page.objects.get(slug=op["slug"]), current[0].order, len(current), op["old"])
        restored += 1
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
