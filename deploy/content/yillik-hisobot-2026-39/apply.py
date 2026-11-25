# The report pages (Yillik hisobot 2026 and its eight sub-pages): their pictures leave the repository and the old HTML.
#   * every <img src="/images/hisobot/..."> of a raw_html block becomes one `image` block (consecutive pictures stay consecutive blocks, the layout engine
#     groups them); the 98 files become Image rows in the media library (alt text per language kept in the block, the Uzbek one on the Image row);
#   * the report PDF (a raw_html link in the middle of "Yillik hisobot 2026") becomes a `document` block at the END of that page, the file a Document row;
#   * one raw_html line of links ("Sunʻiy intellekt tizimlari") becomes a paragraph with the three addresses.
# Nothing is left as raw_html on these pages. The new blocks are plain typed blocks, so the admin editor shows and keeps them.
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if it still is the raw_html block with the fingerprints of plan.json (a block edited in the
# admin since is SKIPPED and listed); apply is one transaction with a backup (a second apply is refused); undo puts the old HTML block back, only where the new
# blocks are still exactly what this script wrote, and then removes the Image/Document rows that nothing uses any more.
# Files are read from the repository checkout: IMAGES_DIR (default frontend/public/images/hisobot) and FILES_DIR (default frontend/public/files).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-39/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-39/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-39/apply.py
import collections
import json
import os

from apps.content.migration_tools import fingerprint_ok, make_document, make_image, replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document, Image

NAME = "yillik-hisobot-2026-39"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
IMAGES_DIR = os.environ.get("IMAGES_DIR", "frontend/public/images/hisobot")
FILES_DIR = os.environ.get("FILES_DIR", "frontend/public/files")
LANGS = ("uz", "ru", "en")


def by_page():
    pages = collections.OrderedDict()
    for entry in PLAN:
        pages.setdefault(entry["slug"], []).append(entry)
    for entries in pages.values():
        entries.sort(key=lambda e: -e["order"])  # from the end of the page, so the orders above are not shifted yet
    return pages


def build(apply):
    rows = {"entries": [], "image_pks": [], "document_pks": []}
    images = {}
    skipped = []
    pictures = blocks = 0
    for slug, entries in by_page().items():
        page = Page.objects.filter(slug=slug).first()
        for entry in entries:
            block = page.blocks.filter(order=entry["order"]).first() if page else None
            if block is None or block.block_type != "raw_html" or not fingerprint_ok(block, entry["fp"]):
                skipped.append((slug, entry["order"], "not the raw_html block of the plan (missing or edited since)"))
                continue
            old = {"block_type": "raw_html", "data": block.data}
            if entry["kind"] == "images":
                print("%s #%d: %d pictures -> %d image blocks" % (slug, entry["order"], len(entry["images"]), len(entry["images"])))
                pictures += len(entry["images"])
                blocks += len(entry["images"])
                if not apply:
                    continue
                new = []
                for item in entry["images"]:
                    image = images.get(item["file"])
                    if image is None:
                        image = images[item["file"]] = make_image(os.path.join(IMAGES_DIR, item["file"]), item["alt"]["uz"])
                        rows["image_pks"].append(image.pk)
                    new.append({"block_type": "image", "data": {lang: {"image_id": image.pk, "alt": item["alt"][lang]} for lang in LANGS}})
                pks = replace_blocks(page, entry["order"], 1, new)
            elif entry["kind"] == "links":
                print("%s #%d: one line of links -> a paragraph (%s)" % (slug, entry["order"], entry["text"]))
                blocks += 1
                if not apply:
                    continue
                pks = replace_blocks(page, entry["order"], 1, [{"block_type": "paragraph", "data": {lang: {"text": entry["text"]} for lang in LANGS}}])
            else:  # pdf: the old block goes, the report file becomes the last block of the page
                print("%s #%d: the report PDF link -> a document block at the end of the page (%s)" % (slug, entry["order"], entry["file"]))
                blocks += 1
                if not apply:
                    continue
                document = make_document(os.path.join(FILES_DIR, entry["file"]), entry["caption"]["uz"])
                rows["document_pks"].append(document.pk)
                replace_blocks(page, entry["order"], 1, [])
                last = max(b.order for b in page.blocks.all()) + 1
                data = {lang: {"document_id": document.pk, "caption": entry["caption"][lang]} for lang in LANGS}
                pks = replace_blocks(page, last, 0, [{"block_type": "document", "data": data}])
            created = list(ContentBlock.objects.filter(pk__in=pks).order_by("order"))
            rows["entries"].append({"slug": slug, "order": entry["order"], "kind": entry["kind"], "old": old,
                                    "new": [{"pk": b.pk, "fp": sha(b.data["uz"])} for b in created]})
    print("\n%d pictures in %d blocks; %d skipped." % (pictures, blocks, len(skipped)))
    for slug, order, why in skipped:
        print("SKIPPED %s #%s: %s" % (slug, order, why))
    return rows


def undo(rows):
    restored = left = 0
    for entry in sorted(rows["entries"], key=lambda e: (e["slug"], e["order"])):  # the reverse of the order they were applied in
        page = Page.objects.get(slug=entry["slug"])
        current = list(ContentBlock.objects.filter(pk__in=[n["pk"] for n in entry["new"]]).order_by("order"))
        wrote = {n["pk"]: n["fp"] for n in entry["new"]}
        untouched = len(current) == len(wrote) and all(sha(b.data["uz"]) == wrote.get(b.pk) for b in current)
        if not untouched:
            left += 1
            print("left %s #%s: the new blocks were edited or removed since" % (entry["slug"], entry["order"]))
            continue
        if entry["kind"] == "pdf":
            replace_blocks(page, current[0].order, 1, [])
            replace_blocks(page, entry["order"], 0, [entry["old"]])
        else:
            replace_blocks(page, current[0].order, len(current), [entry["old"]])
        restored += 1
    used = {(b.data.get("uz") or {}).get("image_id") for b in ContentBlock.objects.filter(block_type="image")}
    for image in Image.objects.filter(pk__in=rows["image_pks"]):
        if image.pk not in used:
            image.file.delete(save=False)
            image.delete()
    in_use = {(b.data.get("uz") or {}).get("document_id") for b in ContentBlock.objects.filter(block_type="document")}
    for document in Document.objects.filter(pk__in=rows["document_pks"]):
        if document.pk not in in_use:
            document.file.delete(save=False)
            document.delete()
    print("restored %d blocks, left %d." % (restored, left))


run_modes(NAME, build, undo)
