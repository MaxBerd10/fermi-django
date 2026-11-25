# The four text pages of Institut haqida become typed blocks, the same structure in uz, ru and en (Missiya, USMLE, Ichki tartib qoidalari, Odob-axloq kodeksi):
# the one raw_html block per page (a different HTML for each language) is replaced by headings (level 2 = section or chapter, level 3 = article or step),
# paragraphs and lists; the pictures (the institute photo on Missiya, the USMLE photo, the cover of the Code) become `image` blocks on Image rows (the files of the media
# folder are used where they are; the institute photo is a file of the repository checkout, IMAGES_DIR, and its row is reused if script 40 made it).
# The texts are the reviewed texts of the pending scripts 36, 37, 38 (so this script REPLACES them: do not apply 36-38) plus the live texts of the other languages:
#   * Missiya: Uzbek from the live page, Russian and English from script 37 (nothing in them changed, only structure; the six values become level-3 headings);
#   * USMLE: Uzbek and Russian from script 36 (complete translations), English from the live page without the Wikipedia leftovers ("Step 3[edit]", "Main article");
#     every "USMLE Step N" paragraph becomes a level-3 heading + paragraph;
#   * Ichki tartib: the existing text only, structured; the Russian and English texts lacked the line "professor-oʻqituvchilar" (translated here, to be checked by a Russian
#     and English reader) and joined rule 2 to the line about students (split here); the stray language marker after the PDF link is dropped;
#   * Kodeks: all three languages from script 38 (complete translation of the Uzbek Code); its `document` block stays, now below the text.
#
# SAFE BY DESIGN: dry (default) writes nothing; a page is changed only if its raw_html block still has the fingerprints of plan.json (edited in the admin since -> SKIPPED
# and listed); apply is one transaction with a backup (a second apply is refused); undo puts the old HTML block back, only where the new blocks are still exactly what this
# script wrote, and then removes the Image rows this script made (the files of the media folder stay; the copy of the repository picture is removed with its row).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-41/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-41/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-41/apply.py
import collections
import json
import os

from apps.content.migration_tools import fingerprint_ok, image_from_media, replace_blocks, reuse_or_make_image, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image

NAME = "yillik-hisobot-2026-41"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
IMAGES_DIR = os.environ.get("IMAGES_DIR", "frontend/public/images")
LANGS = ("uz", "ru", "en")


def resolve_images(blocks, made):
    """The plan names a picture by its path in the media folder; the block needs the id of its Image row."""
    resolved = []
    for block in blocks:
        if block["block_type"] != "image":
            resolved.append(block)
            continue
        spec = block["data"]["uz"]
        before = set(Image.objects.values_list("pk", flat=True))
        if "repo_image" in spec:  # a file of the repository checkout
            image = reuse_or_make_image(os.path.join(IMAGES_DIR, spec["repo_image"]), spec["alt"])
        else:  # a file already in the media folder
            image = image_from_media(spec["image_media"], spec["alt"])
        if image.pk not in before:
            made["copied" if "repo_image" in spec else "rows"].append(image.pk)
        resolved.append({"block_type": "image", "data": {lang: {"image_id": image.pk, "alt": block["data"][lang]["alt"]} for lang in LANGS}})
    return resolved


def build(apply):
    rows = {"entries": [], "image_pks": [], "copied_pks": []}
    skipped = []
    for entry in PLAN:
        page = Page.objects.filter(slug=entry["slug"]).first()
        block = page.blocks.filter(order=entry["order"]).first() if page else None
        if block is None or block.block_type != "raw_html" or not fingerprint_ok(block, entry["fp"]):
            skipped.append((entry["slug"], "the HTML block is not the one of the plan (missing or edited since)"))
            continue
        kinds = collections.Counter(b["block_type"] for b in entry["blocks"])
        print("%s: the HTML block -> %d blocks (%s)" % (entry["slug"], len(entry["blocks"]), ", ".join("%s %d" % item for item in sorted(kinds.items()))))
        if not apply:
            continue
        new = resolve_images(entry["blocks"], {"rows": rows["image_pks"], "copied": rows["copied_pks"]})
        old = {"block_type": "raw_html", "data": block.data}
        pks = replace_blocks(page, entry["order"], 1, new)
        created = list(ContentBlock.objects.filter(pk__in=pks).order_by("order"))
        rows["entries"].append({"slug": entry["slug"], "old": old, "new": [{"pk": b.pk, "fp": sha(b.data["uz"])} for b in created]})
    for slug, why in skipped:
        print("SKIPPED %s: %s" % (slug, why))
    print("\n%d page(s) changed, %d skipped." % (len(PLAN) - len(skipped), len(skipped)))
    return rows


def undo(rows):
    restored = left = 0
    for entry in reversed(rows["entries"]):
        page = Page.objects.get(slug=entry["slug"])
        current = list(ContentBlock.objects.filter(pk__in=[n["pk"] for n in entry["new"]]).order_by("order"))
        wrote = {n["pk"]: n["fp"] for n in entry["new"]}
        if len(current) != len(wrote) or any(sha(b.data["uz"]) != wrote.get(b.pk) for b in current):
            left += 1
            print("left %s: the new blocks were edited or removed since" % entry["slug"])
            continue
        replace_blocks(page, current[0].order, len(current), [entry["old"]])
        restored += 1
    used = {(b.data.get("uz") or {}).get("image_id") for b in ContentBlock.objects.filter(block_type="image")}
    for image in Image.objects.filter(pk__in=rows["image_pks"]):
        if image.pk not in used:
            image.delete()  # the row only: the file belongs to the media folder and may be used elsewhere
    for image in Image.objects.filter(pk__in=rows.get("copied_pks", [])):
        if image.pk not in used:
            image.file.delete(save=False)  # the copy of the repository picture this script made
            image.delete()
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
