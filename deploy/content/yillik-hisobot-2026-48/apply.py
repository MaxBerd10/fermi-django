# "Institut kengashi" (5 pages: council, composition, agenda, decisions, avtoreferatlar) from raw HTML to typed blocks:
#   institut-ilmiy-kengashi  the text becomes a paragraph, a heading, two lists of duties and the lead-in paragraph between them (the English page lacked five duties: translated);
#   ilmiy-kengash-tarkibi, kengash-kun-tartibi, ilmiy-kengash  the scan becomes an `image` block (kun-tartibi/ilmiy-kengash keep the old "registered users" line as a paragraph);
#   ilmiy-kengash  the 2022-2023 decisions without a file become a list, the 2024 PDFs become `document` cards (ru/en get the same list and cards: they had none);
#   avtoreferatlar  13 defences, four blocks each: the council line, the author (heading), the thesis title, the PDF card (the site draws them as one card per defence).
# The `document` cards already on the pages stay; the ones of ilmiy-kengash-tarkibi, kengash-kun-tartibi and ilmiy-kengash get a caption (they showed a file name).
# Each PDF is copied from its old place in the media folder into the document library (uploads/documents/...) as a Document row; the old files stay where they are.
# The scans are Image rows that point at the files already in the media folder (nothing is copied).
#
# SAFE BY DESIGN: dry (default) writes nothing and STOPS if a file is missing in the media folder; a page is changed only if its raw_html block still has the fingerprints
# of plan.json and its card the ones of the plan (edited in the admin since -> SKIPPED and listed); apply is one transaction with a backup (a second apply is refused);
# undo puts the old HTML block and the old card data back, only where the new blocks are still exactly what this script wrote, and then removes the Document rows this
# script made and their copies and the Image rows it made (never the old files).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-48/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-48/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-48/apply.py
import collections
import json
import os

from django.conf import settings

from apps.content.migration_tools import fingerprint_ok, image_from_media, make_document, replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document, Image

NAME = "yillik-hisobot-2026-48"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
LANGS = ("uz", "ru", "en")


def db_data(block):
    return {lang: {k: v for k, v in block.data[lang].items() if k not in ("image", "document")} for lang in LANGS}


def media_files():
    found = set()
    for entry in PLAN:
        for spec in entry["blocks"]:
            if spec["block_type"] in ("document", "image"):
                found.add(spec["data"]["uz"]["media"])
    return sorted(found)


def card_ok(page, existing):
    block = page.blocks.filter(order=existing["order"]).first()
    if block is None or block.block_type != "document" or (block.data.get("uz") or {}).get("document_id") != existing["document_id"]:
        return None
    data = db_data(block)
    if any(sha(data[lang]) != existing["fp"][lang] for lang in LANGS) or any("caption" in data[lang] for lang in LANGS):
        return None
    return block


def build(apply):
    missing = [p for p in media_files() if not os.path.isfile(os.path.join(str(settings.MEDIA_ROOT), p))]
    if missing:
        raise SystemExit("STOP: files not found in %s:\n  %s" % (settings.MEDIA_ROOT, "\n  ".join(missing)))
    rows = {"entries": [], "document_pks": [], "image_pks": []}
    copies = {}
    skipped = []
    for entry in PLAN:
        page = Page.objects.filter(slug=entry["slug"]).first()
        block = page.blocks.filter(order=entry["order"]).first() if page else None
        if block is None or block.block_type != "raw_html" or not fingerprint_ok(block, entry["fp"]):
            skipped.append((entry["slug"], "the HTML block is not the one of the plan (missing or edited since)"))
            continue
        existing = entry.get("existing_document")
        card = card_ok(page, existing) if existing else None
        if existing and card is None:
            skipped.append((entry["slug"], "the document card is not the one of the plan (missing, edited or already has a caption)"))
            continue
        kinds = collections.Counter(b["block_type"] for b in entry["blocks"])
        print("%s: the HTML block -> %d blocks (%s)%s" % (entry["slug"], len(entry["blocks"]), ", ".join("%s %d" % item for item in sorted(kinds.items())),
                                                           "; the card gets the caption \"%s\"" % existing["caption"]["uz"] if existing else ""))
        if not apply:
            continue
        new = []
        for spec in entry["blocks"]:
            if spec["block_type"] == "document":
                path = spec["data"]["uz"]["media"]
                if path not in copies:
                    copies[path] = make_document(os.path.join(str(settings.MEDIA_ROOT), path), spec["data"]["uz"]["caption"])
                    rows["document_pks"].append(copies[path].pk)
                new.append({"block_type": "document", "data": {lang: {"style": "card", "document_id": copies[path].pk, "caption": spec["data"][lang]["caption"]} for lang in LANGS}})
            elif spec["block_type"] == "image":
                path = spec["data"]["uz"]["media"]
                before = set(Image.objects.values_list("pk", flat=True))
                image = image_from_media(path, spec["data"]["uz"]["alt"])
                if image.pk not in before:
                    rows["image_pks"].append(image.pk)
                new.append({"block_type": "image", "data": {lang: {"image_id": image.pk, "alt": spec["data"][lang]["alt"]} for lang in LANGS}})
            else:
                new.append(spec)
        old = {"block_type": "raw_html", "data": block.data}
        old_card = json.loads(json.dumps(card.data)) if card else None
        pks = replace_blocks(page, entry["order"], 1, new)
        created = list(ContentBlock.objects.filter(pk__in=pks).order_by("order"))
        record = {"slug": entry["slug"], "old": old, "new": [{"pk": b.pk, "fp": sha(b.data)} for b in created]}
        if card:
            card.refresh_from_db()
            for lang in LANGS:
                card.data[lang]["caption"] = existing["caption"][lang]
            card.full_clean()
            card.save()
            record["card"] = {"pk": card.pk, "old": old_card, "fp": sha(card.data)}
        rows["entries"].append(record)
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
        card = entry.get("card")
        if card:
            block = ContentBlock.objects.filter(pk=card["pk"]).first()
            if block is not None and sha(block.data) == card["fp"]:
                block.data = card["old"]
                block.full_clean()
                block.save()
            else:
                print("left the card of %s: edited or removed since" % entry["slug"])
        restored += 1
    used_documents = {(b.data.get("uz") or {}).get("document_id") for b in ContentBlock.objects.filter(block_type="document")}
    for document in Document.objects.filter(pk__in=rows["document_pks"]):
        if document.pk not in used_documents:
            document.file.delete(save=False)  # the copy this script made
            document.delete()
    used_images = {(b.data.get("uz") or {}).get("image_id") for b in ContentBlock.objects.filter(block_type="image")}
    for image in Image.objects.filter(pk__in=rows["image_pks"]):
        if image.pk not in used_images:
            image.delete()  # the row only: the file belongs to the media folder
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
