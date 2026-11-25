# Eight pages of Institut binolari (Rektorat, Oʻquv binolari, 2-Oʻquv kampusi, Vivariy, Simulatsiya markazi, Kongress zallari, Sport majmualari, Talabalar turar joylari) that are
# only pictures in one raw_html block. Each block becomes one `image` block per picture (a run of several is drawn as a gallery) on Image rows of the files that already lie in
# the media folder (the rows point at them, nothing is copied). The UZ pictures are the base for all three languages; where ru or en showed another set of pictures (2-Oʻquv
# kampusi en, Vivariy en, Kongress zallari ru order and en) the difference is printed. Alt text of every picture = the menu label of its page, per language, numbered.
#
# SAFE BY DESIGN: dry (default) writes nothing and STOPS if a picture file is missing; a page is changed only if its raw_html block still has the fingerprints of plan.json
# (edited in the admin since -> SKIPPED and listed); apply is one transaction with a backup (a second apply is refused); undo puts the old HTML block back, only where the new
# blocks are still exactly what this script wrote, and then removes the Image rows this script made (never the files).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-47/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-47/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-47/apply.py
import json
import os

from django.conf import settings

from apps.content.migration_tools import fingerprint_ok, image_from_media, replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image

NAME = "yillik-hisobot-2026-47"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
LANGS = ("uz", "ru", "en")


def missing_files():
    return sorted({item["media"] for entry in PLAN for item in entry["images"]
                   if not Image.objects.filter(file=item["media"]).exists() and not os.path.isfile(os.path.join(str(settings.MEDIA_ROOT), item["media"]))})


def build(apply):
    missing = missing_files()
    if missing:
        raise SystemExit("STOP: picture files not found in %s:\n  %s" % (settings.MEDIA_ROOT, "\n  ".join(missing)))
    rows = {"entries": [], "image_pks": []}
    skipped = []
    for entry in PLAN:
        page = Page.objects.filter(slug=entry["slug"]).first()
        block = page.blocks.filter(order=entry["order"]).first() if page else None
        if block is None or block.block_type != "raw_html" or not fingerprint_ok(block, entry["fp"]):
            skipped.append((entry["slug"], "the HTML block is not the one of the plan (missing or edited since)"))
            continue
        print("%s: the HTML block -> %d image block(s)" % (entry["slug"], len(entry["images"])))
        for lang, diff in entry.get("diff", {}).items():
            kind = "the same pictures in another order" if not diff["missing"] and not diff["extra"] else "another set: missing %s | extra %s" % (diff["missing"] or "-", diff["extra"] or "-")
            print("    %s showed %s -> now the uz pictures in the uz order" % (lang, kind))
        if not apply:
            continue
        new = []
        for item in entry["images"]:
            before = set(Image.objects.values_list("pk", flat=True))
            image = image_from_media(item["media"], item["alt"]["uz"])
            if image.pk not in before:
                rows["image_pks"].append(image.pk)
            new.append({"block_type": "image", "data": {lang: {"image_id": image.pk, "alt": item["alt"][lang]} for lang in LANGS}})
        old = {"block_type": "raw_html", "data": block.data}
        pks = replace_blocks(page, entry["order"], 1, new)
        created = list(ContentBlock.objects.filter(pk__in=pks).order_by("order"))
        rows["entries"].append({"slug": entry["slug"], "old": old, "new": [{"pk": b.pk, "fp": sha(b.data)} for b in created]})
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
        if len(current) != len(wrote) or any(sha(b.data) != wrote.get(b.pk) for b in current):
            left += 1
            print("left %s: the new blocks were edited or removed since" % entry["slug"])
            continue
        replace_blocks(page, current[0].order, len(current), [entry["old"]])
        restored += 1
    used = {(b.data.get("uz") or {}).get("image_id") for b in ContentBlock.objects.filter(block_type="image")}
    for image in Image.objects.filter(pk__in=rows["image_pks"]):
        if image.pk not in used:
            image.delete()  # the row only: the file belongs to the media folder
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
