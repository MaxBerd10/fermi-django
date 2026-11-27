# mutaxassisliklar-boyicha-testlar-toplami ("Fanlardan test toʻplamlari"): the page mixed three kinds of file lines: 19 document cards, 39 plain link lines ("name PDF (uzb)")
# and a picture that the article layout moved into the middle of the first department. Every link line becomes a document card like the other 19 (same style "card",
# the caption is the old link text and its language tag, e.g. "Farmakologiya (uzb)"); the line "Oʻzbek va xorijiy tillar kafedrasi" (plain text, the only department without a
# heading) becomes a heading of the level of the other departments (ru/en: the texts it already had); the picture becomes a gallery block of the style "plain", so it stays at
# the top of the page. The blocks keep their places: 41 blocks are replaced one for one, nothing moves. The PDF files are ALREADY in the media folder (migrated/img/...); a
# file name there is too long for a Document (100 characters) or has Cyrillic, so each Document row gets a COPY under uploads/documents/<year>/<month>/ (as every other
# document); the old files stay where they are. RUN AFTER scripts 39-99.
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if it still is exactly the block of plan.json AND (for a link line) the file is in the media folder,
# otherwise it is SKIPPED and the apply is cancelled as a whole; apply is one transaction with a backup (a second apply is refused); undo puts the old blocks back, only
# where the new block is still what this script wrote, and removes the Document rows it made (the copied files stay in uploads/documents: harmless).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-100/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-100/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-100/apply.py
import json
import os

from django.conf import settings

from apps.content.migration_tools import make_document, replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document, Image

NAME = "yillik-hisobot-2026-100"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
LANGS = ("uz", "ru", "en")


def problem(block, entry):
    """Why the block is not the one the plan was made from (None when it is)."""
    if block is None:
        return "the block is missing"
    if entry["kind"] == "picture":
        image = Image.objects.filter(pk=block.data["uz"].get("image_id")).first()
        if block.block_type != "image" or image is None or image.file.name.rsplit("/", 1)[-1] != entry["file_tail"]:
            return "it is not the picture of the plan"
        return None
    if block.block_type != "paragraph":
        return "it is not a paragraph any more"
    if entry["kind"] == "pdf":
        if any(block.data[lang].get("text") != entry["text"] for lang in LANGS):
            return "the line was edited since"
        if not os.path.isfile(os.path.join(str(settings.MEDIA_ROOT), entry["media_path"])):
            return "the file %s is not in the media folder" % entry["media_path"]
    elif any(block.data[lang].get("text") != entry["text"][lang] for lang in LANGS):
        return "the line was edited since"
    return None


def build(apply):
    rows = {"entries": []}
    skipped = []
    page = Page.objects.filter(slug=PLAN["slug"]).first()
    if page is None:
        raise SystemExit("STOP: the page %s does not exist." % PLAN["slug"])
    for entry in PLAN["entries"]:
        block = page.blocks.filter(order=entry["order"]).first()
        why = problem(block, entry)
        if why:
            skipped.append((entry["order"], why))
            continue
        print("#%d: %s -> %s" % (entry["order"], {"picture": "picture", "pdf": "link line", "heading": "plain line"}[entry["kind"]],
                                 {"picture": "gallery (plain)", "pdf": "document card %r" % entry.get("caption"), "heading": "heading"}[entry["kind"]]))
        if not apply:
            continue
        old = {"block_type": block.block_type, "data": block.data}
        document_pk = None
        if entry["kind"] == "picture":
            data = {lang: {"style": "plain", "items": [{"image_id": block.data[lang]["image_id"], "alt": block.data[lang].get("alt", "")}]} for lang in LANGS}
            new = {"block_type": "gallery", "data": data}
        elif entry["kind"] == "pdf":
            document = make_document(os.path.join(str(settings.MEDIA_ROOT), entry["media_path"]), title=entry["caption"])
            document_pk = document.pk
            new = {"block_type": "document", "data": {lang: {"style": "card", "caption": entry["caption"], "document_id": document.pk} for lang in LANGS}}
        else:
            new = {"block_type": "heading", "data": {lang: {"text": entry["text"][lang], "level": 3} for lang in LANGS}}
        (pk,) = replace_blocks(page, entry["order"], 1, [new])
        rows["entries"].append({"order": entry["order"], "old": old, "new_pk": pk, "new_fp": sha(ContentBlock.objects.get(pk=pk).data), "document_pk": document_pk})
    for order, why in skipped:
        print("SKIPPED #%d: %s" % (order, why))
    print("\n%d block(s) changed, %d skipped." % (len(PLAN["entries"]) - len(skipped), len(skipped)))
    if apply and skipped:
        raise SystemExit("STOP: some blocks were skipped, nothing was written (the transaction is cancelled).")
    return rows


def undo(rows):
    restored = left = 0
    page = Page.objects.get(slug=PLAN["slug"])
    for entry in reversed(rows["entries"]):
        block = ContentBlock.objects.filter(pk=entry["new_pk"]).first()
        if block is None or sha(block.data) != entry["new_fp"]:
            left += 1
            print("left #%d: the block was edited or removed since" % entry["order"])
            continue
        replace_blocks(page, entry["order"], 1, [entry["old"]])
        if entry["document_pk"]:
            Document.objects.filter(pk=entry["document_pk"]).delete()  # the row only: deleting a row does not delete the file
        restored += 1
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
