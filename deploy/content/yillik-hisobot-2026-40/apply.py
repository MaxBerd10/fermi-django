# "Institut xaqida": the page's dead HTML block (25 KB the site never showed) becomes what the page shows, as typed blocks:
#   heading (the institute's name) + two paragraphs (the texts that lived in the frontend translation files) + the photo (an Image row from
#   frontend/public/images/institut-about.jpg); the ECAQA document block it already has gets its title as a caption (also from the translation files).
# After this the page is edited in the admin like any other and the frontend has no special code for it.
#
# SAFE BY DESIGN: dry (default) writes nothing; the HTML block is replaced only if it still has the fingerprints of plan.json (edited in the admin since
# -> SKIPPED and listed); the caption is set only on a document block that has no caption yet; apply is one transaction with a backup (a second apply is
# refused); undo puts the old HTML block back and removes the caption, only where the new blocks are still exactly what this script wrote.
# The photo is read from the repository checkout: IMAGES_DIR (default frontend/public/images).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-40/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-40/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-40/apply.py
import json
import os

from apps.content.migration_tools import fingerprint_ok, make_image, replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image

NAME = "yillik-hisobot-2026-40"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
IMAGES_DIR = os.environ.get("IMAGES_DIR", "frontend/public/images")
LANGS = ("uz", "ru", "en")


def build(apply):
    rows = {"entries": [], "image_pks": []}
    skipped = []
    for entry in PLAN:
        page = Page.objects.filter(slug=entry["slug"]).first()
        if entry["kind"] == "about":
            block = page.blocks.filter(order=entry["order"]).first() if page else None
            if block is None or block.block_type != "raw_html" or not fingerprint_ok(block, entry["fp"]):
                skipped.append((entry["slug"], "the HTML block is not the one of the plan (missing or edited since)"))
                continue
            print("%s #%d: the old HTML block -> heading + 2 paragraphs + the photo" % (entry["slug"], entry["order"]))
            if not apply:
                continue
            image = make_image(os.path.join(IMAGES_DIR, entry["image"]["file"]), entry["image"]["alt"]["uz"])
            rows["image_pks"].append(image.pk)
            new = [
                {"block_type": "heading", "data": {lang: {"text": entry["heading"][lang], "level": 2} for lang in LANGS}},
                *[{"block_type": "paragraph", "data": {lang: {"text": text[lang]} for lang in LANGS}} for text in entry["paragraphs"]],
                {"block_type": "image", "data": {lang: {"image_id": image.pk, "alt": entry["image"]["alt"][lang]} for lang in LANGS}},
            ]
            old = {"block_type": "raw_html", "data": block.data}
            pks = replace_blocks(page, entry["order"], 1, new)
            created = list(ContentBlock.objects.filter(pk__in=pks).order_by("order"))
            rows["entries"].append({"kind": "about", "slug": entry["slug"], "old": old,
                                    "new": [{"pk": b.pk, "fp": sha(b.data)} for b in created]})
        else:  # caption
            block = None
            if page:
                block = next((b for b in page.blocks.filter(block_type="document")
                              if (b.data.get("uz") or {}).get("document_id") == entry["document_id"]), None)
            if block is None or any("caption" in (block.data.get(lang) or {}) for lang in LANGS):
                skipped.append((entry["slug"], "no document block %s without a caption (missing or captioned since)" % entry["document_id"]))
                continue
            print("%s: the document %s gets its title as caption" % (entry["slug"], entry["document_id"]))
            if not apply:
                continue
            old = json.loads(json.dumps(block.data))
            for lang in LANGS:
                block.data[lang]["caption"] = entry["caption"][lang]
            block.full_clean()
            block.save()
            rows["entries"].append({"kind": "caption", "pk": block.pk, "old": old, "fp": sha(block.data)})
    for slug, why in skipped:
        print("SKIPPED %s: %s" % (slug, why))
    print("\n%d change(s), %d skipped." % (len(PLAN) - len(skipped), len(skipped)))
    return rows


def undo(rows):
    restored = left = 0
    if True:  # (run_modes already wraps undo in one transaction)
        for entry in reversed(rows["entries"]):
            if entry["kind"] == "caption":
                block = ContentBlock.objects.filter(pk=entry["pk"]).first()
                if block is None or sha(block.data) != entry["fp"]:
                    left += 1
                    print("left the caption: edited or removed since")
                    continue
                block.data = entry["old"]
                block.save()
            else:
                page = Page.objects.get(slug=entry["slug"])
                current = list(ContentBlock.objects.filter(pk__in=[n["pk"] for n in entry["new"]]).order_by("order"))
                wrote = {n["pk"]: n["fp"] for n in entry["new"]}
                if len(current) != len(wrote) or any(sha(b.data) != wrote.get(b.pk) for b in current):
                    left += 1
                    print("left %s: the new blocks were edited or removed since" % entry["slug"])
                    continue
                replace_blocks(page, current[0].order, len(current), [entry["old"]])
            restored += 1
        used = {(b.data.get("uz") or {}).get("image_id") for b in ContentBlock.objects.filter(block_type="image")}
        for image in Image.objects.filter(pk__in=rows["image_pks"]):
            if image.pk not in used:
                image.file.delete(save=False)
                image.delete()
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
