# Faoliyat > Doktorantura (three pages): "Monografiya" (a cover and four PDFs), "Malakaviy imtihonlar" (twelve exam programmes as PDF links) and "Doktorantura maʻlumotlari" (numbers,
# the same twelve programmes, requirements, three lists of documents, regulations) become typed blocks: headings, paragraphs, lists, one picture and document cards (the card the page
# already had stays last and gets a caption). Uzbek is the base; the old English text of "Doktorantura maʻlumotlari" had other lists and is written again after the Uzbek and Russian text
# (see tarjima-kerak.md). The picture is an Image row pointing at the file already in the media folder; the document cards are copies made with make_document.
#
# SAFE BY DESIGN: dry (default) writes nothing and STOPS if a file is missing in the media folder; a page is changed only if its raw_html block still has the fingerprints of plan.json and
# its card the one of the plan (edited in the admin since -> SKIPPED and listed); apply is one transaction with a backup (a second apply is refused); undo puts the old HTML block and the
# old card data back, only where the new blocks are still exactly what this script wrote, and then removes the Document/Image rows this script made (never the files).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-60/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-60/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-60/apply.py
import collections
import json
import os

from django.conf import settings

from apps.content.migration_tools import fingerprint_ok, image_from_media, make_document, make_image, replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document, Image

NAME = "yillik-hisobot-2026-60"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
LANGS = ("uz", "ru", "en")


def db_data(block):
    return {lang: {k: v for k, v in block.data[lang].items() if k not in ("image", "document")} for lang in LANGS}


def media_files():
    found = set()
    for entry in PLAN:
        for spec in entry.get("blocks", []):
            if spec["block_type"] == "document":
                found.update(spec["data"][lang]["media"] for lang in LANGS)  # a card may point at another PDF in each language
            elif spec["block_type"] == "image":
                found.add(spec["data"]["uz"]["media"])
    return sorted(found)


def find_cards(page, entry):
    """The existing cards of the plan as blocks, or None if one of them is missing, edited or already has a caption."""
    found = []
    for existing in entry.get("existing_documents", []):
        block = page.blocks.filter(order=existing["order"]).first()
        if block is None or block.block_type != "document" or (block.data.get("uz") or {}).get("document_id") != existing["document_id"]:
            return None
        data = db_data(block)
        if any(sha(data[lang]) != existing["fp"][lang] for lang in LANGS) or (not entry.get("recaption") and any("caption" in data[lang] for lang in LANGS)):
            return None
        found.append((block, existing))
    return found


def build(apply):
    missing = [p for p in media_files() if not os.path.isfile(os.path.join(str(settings.MEDIA_ROOT), p))]
    if missing:
        raise SystemExit("STOP: files not found in %s:\n  %s" % (settings.MEDIA_ROOT, "\n  ".join(missing)))
    rows = {"entries": [], "document_pks": [], "image_pks": []}
    copies = {}
    skipped = []
    for entry in PLAN:
        page = Page.objects.filter(slug=entry["slug"]).first()
        if page is not None and "blocks" not in entry:  # only the captions of the cards
            cards = find_cards(page, entry)
            if cards is None:
                skipped.append((entry["slug"], "the document card is not the one of the plan (missing or edited since)"))
                continue
            print("%s: %d card(s) get a caption" % (entry["slug"], len(cards)))
            for note in entry.get("notes", []):
                print("    " + note)
            if apply:
                record = {"slug": entry["slug"], "old": None, "new": [], "cards": []}
                for card_block, existing in cards:
                    old_data = json.loads(json.dumps(card_block.data))
                    for lang in LANGS:
                        card_block.data[lang]["caption"] = existing["caption"][lang]
                    card_block.full_clean()
                    card_block.save()
                    record["cards"].append({"pk": card_block.pk, "old": old_data, "fp": sha(card_block.data)})
                rows["entries"].append(record)
            continue
        block = page.blocks.filter(order=entry["order"]).first() if page else None
        if block is None or block.block_type != "raw_html" or not fingerprint_ok(block, entry["fp"]):
            skipped.append((entry["slug"], "the HTML block is not the one of the plan (missing or edited since)"))
            continue
        cards = find_cards(page, entry)
        if cards is None:
            skipped.append((entry["slug"], "a document card is not the one of the plan (missing, edited or already has a caption)"))
            continue
        kinds = collections.Counter(b["block_type"] for b in entry["blocks"])
        print("%s: the HTML block -> %d blocks (%s)%s" % (entry["slug"], len(entry["blocks"]), ", ".join("%s %d" % item for item in sorted(kinds.items())),
                                                           "; %d card(s) get a caption" % len(cards) if cards else ""))
        for note in entry.get("notes", []):
            print("    " + note)
        if not apply:
            continue
        new = []
        for spec in entry["blocks"]:
            if spec["block_type"] == "document":
                data = {}
                for lang in LANGS:
                    path = spec["data"][lang]["media"]
                    if path not in copies:
                        copies[path] = make_document(os.path.join(str(settings.MEDIA_ROOT), path), spec["data"][lang]["caption"])
                        rows["document_pks"].append(copies[path].pk)
                    data[lang] = {"style": "card", "document_id": copies[path].pk, "caption": spec["data"][lang]["caption"]}
                new.append({"block_type": "document", "data": data})
            elif spec["block_type"] == "image":
                path = spec["data"]["uz"]["media"]
                before = set(Image.objects.values_list("pk", flat=True))
                if len(path) > 100:  # an Image row cannot hold a path this long (varchar 100): the picture is copied into the library (undo removes the row; the copy stays on disk)
                    image = make_image(os.path.join(str(settings.MEDIA_ROOT), path), spec["data"]["uz"]["alt"])
                else:
                    image = image_from_media(path, spec["data"]["uz"]["alt"])
                if image.pk not in before:
                    rows["image_pks"].append(image.pk)
                new.append({"block_type": "image", "data": {lang: {"image_id": image.pk, "alt": spec["data"][lang]["alt"]} for lang in LANGS}})
            else:
                new.append(spec)
        old = {"block_type": "raw_html", "data": block.data}
        old_cards = [(b.pk, json.loads(json.dumps(b.data)), existing) for b, existing in cards]
        pks = replace_blocks(page, entry["order"], 1, new)
        created = list(ContentBlock.objects.filter(pk__in=pks).order_by("order"))
        record = {"slug": entry["slug"], "old": old, "at": entry["order"], "new": [{"pk": b.pk, "fp": sha(b.data)} for b in created], "cards": []}
        for pk, old_data, existing in old_cards:
            card = ContentBlock.objects.get(pk=pk)
            for lang in LANGS:
                card.data[lang]["caption"] = existing["caption"][lang]
            card.full_clean()
            card.save()
            record["cards"].append({"pk": pk, "old": old_data, "fp": sha(card.data)})
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
        if entry["old"] is not None:
            if len(current) != len(wrote) or any(sha(b.data) != wrote.get(b.pk) for b in current):
                left += 1
                print("left %s: the new blocks were edited or removed since" % entry["slug"])
                continue
            replace_blocks(page, current[0].order if current else entry["at"], len(current), [entry["old"]])
        for card in entry.get("cards", []):
            block = ContentBlock.objects.filter(pk=card["pk"]).first()
            if block is not None and sha(block.data) == card["fp"]:
                block.data = card["old"]
                block.full_clean()
                block.save()
            else:
                print("left a card of %s: edited or removed since" % entry["slug"])
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
