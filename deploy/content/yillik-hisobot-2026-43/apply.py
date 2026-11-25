# "Institut tarixi" (the page of the department institut-tarixi, Page slug department-42): its 59 blocks are put in the order the layout engine reads, in all three
# languages at once (the live blocks are parallel in uz, ru and en):
#   * the section labels ("Rivojlanish bosqichlari", "Oʻquv va ilmiy yoʻnalishlar rahbarlari", "Tarix sahifasi", "Xalqaro hamkorlik") become level-2 headings;
#   * the first list is split: the three prose items stay a list, the seven dated ones (1992–1997 — ...) become their own list (drawn as the chronology);
#     the one dated line under "Oʻquv va ilmiy yoʻnalishlar rahbarlari" becomes a one-item dated list;
#   * every one of the 13 people becomes: heading level 3 (the name), image (the portrait: an Image row of frontend/public/images/institute-history/<name>.webp,
#     the file the site already showed instead of the old upload), paragraphs (degree, years, biography). The names that stood in one paragraph with the first
#     sentences are split; Usmanov has no text (as before). The "Tarix sahifasi" picture is archive.webp; the last picture keeps its Image row.
# After this the history is edited in the admin like any other page, and the frontend has no history-only code.
#
# SAFE BY DESIGN: dry (default) writes nothing and STOPS if a portrait file is missing; the page is changed only if EVERY one of its blocks still has the fingerprints of
# plan.json (edited in the admin since -> nothing is written and the differences are listed); apply is one transaction with a backup (a second apply is refused); undo puts
# the 59 old blocks back, only if the new blocks are still exactly what this script wrote, and then removes the Image rows this script made (and their files).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-43/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-43/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-43/apply.py
import collections
import json
import os

from apps.content.migration_tools import replace_blocks, reuse_or_make_image, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image

NAME = "yillik-hisobot-2026-43"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
IMAGES_DIR = os.environ.get("IMAGES_DIR", "frontend/public/images/institute-history")
LANGS = ("uz", "ru", "en")


def portrait_files():
    return sorted({block["data"]["uz"]["repo_image"] for block in PLAN["blocks"] if block["block_type"] == "image" and "repo_image" in block["data"]["uz"]})


def differences(page):
    """The orders whose block is not the one of the plan (or all of them if the number of blocks differs)."""
    blocks = list(page.blocks.order_by("order"))
    if [str(b.order) for b in blocks] != sorted(PLAN["fp"], key=int):
        return ["the page has %d blocks, the plan %d" % (len(blocks), len(PLAN["fp"]))]
    bad = []
    for block in blocks:
        data = {lang: {k: v for k, v in block.data[lang].items() if k not in ("image", "document")} for lang in LANGS}
        if any(sha(data[lang]) != PLAN["fp"][str(block.order)][lang] for lang in LANGS):
            bad.append("block %d (%s) was edited since" % (block.order, block.block_type))
    return bad


def resolve_images(blocks, made):
    resolved = []
    for block in blocks:
        if block["block_type"] != "image" or "repo_image" not in block["data"]["uz"]:
            resolved.append(block)
            continue
        file = block["data"]["uz"]["repo_image"]
        before = set(Image.objects.values_list("pk", flat=True))
        image = reuse_or_make_image(os.path.join(IMAGES_DIR, file), block["data"]["uz"]["alt"])
        if image.pk not in before:
            made.append(image.pk)
        resolved.append({"block_type": "image", "data": {lang: {"image_id": image.pk, "alt": block["data"][lang]["alt"]} for lang in LANGS}})
    return resolved


def build(apply):
    missing = [f for f in portrait_files() if not os.path.isfile(os.path.join(IMAGES_DIR, f))]
    if missing:
        raise SystemExit("STOP: picture files not found in %s: %s" % (IMAGES_DIR, ", ".join(missing)))
    rows = {"entries": [], "image_pks": []}
    page = Page.objects.filter(slug=PLAN["slug"]).first()
    if page is None:
        print("SKIPPED %s: no such page" % PLAN["slug"])
        return rows
    bad = differences(page)
    if bad:
        print("SKIPPED %s: not the page of the plan:" % PLAN["slug"])
        for line in bad:
            print("  " + line)
        return rows
    kinds = collections.Counter(b["block_type"] for b in PLAN["blocks"])
    print("%s: %d blocks -> %d (%s)" % (PLAN["slug"], len(PLAN["fp"]), len(PLAN["blocks"]), ", ".join("%s %d" % i for i in sorted(kinds.items()))))
    if not apply:
        return rows
    old = [{"order": b.order, "block_type": b.block_type, "data": b.data} for b in page.blocks.order_by("order")]
    new = resolve_images(PLAN["blocks"], rows["image_pks"])
    pks = replace_blocks(page, 1, len(old), new)
    created = list(ContentBlock.objects.filter(pk__in=pks).order_by("order"))
    rows["entries"].append({"slug": PLAN["slug"], "old": old, "new": [{"pk": b.pk, "fp": sha(b.data)} for b in created]})
    return rows


def undo(rows):
    restored = left = 0
    for entry in rows["entries"]:
        page = Page.objects.get(slug=entry["slug"])
        current = list(ContentBlock.objects.filter(pk__in=[n["pk"] for n in entry["new"]]).order_by("order"))
        wrote = {n["pk"]: n["fp"] for n in entry["new"]}
        if len(current) != len(wrote) or any(sha(b.data) != wrote.get(b.pk) for b in current) or page.blocks.count() != len(current):
            left += 1
            print("left %s: the page was edited since" % entry["slug"])
            continue
        replace_blocks(page, 1, len(current), [{"block_type": o["block_type"], "data": o["data"]} for o in entry["old"]])
        restored += 1
    used = {(b.data.get("uz") or {}).get("image_id") for b in ContentBlock.objects.filter(block_type="image")}
    for image in Image.objects.filter(pk__in=rows["image_pks"]):
        if image.pk not in used:
            image.file.delete(save=False)  # the copy this script made
            image.delete()
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
