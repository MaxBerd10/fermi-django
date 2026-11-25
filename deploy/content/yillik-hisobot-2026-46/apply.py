# "Institut konferensiyalari" (4 pages) from raw HTML to typed blocks: every linked title (a PDF of proceedings) becomes a `document` block whose caption is the
# title in each language (the three languages are paired by the file address); a link whose file no longer exists stays as a paragraph with the title; the YouTube
# embed of the first page stays one raw_html block (first); the two single-line pages get a paragraph. The PDF cards the pages already had stay below.
# Each PDF is copied from its old place in the media folder into the document library (uploads/documents/...) as a Document row: the old paths are longer than the
# 100 characters a Document file name may have, so a row cannot point at them. The old files stay where they are.
#
# SAFE BY DESIGN: dry (default) writes nothing and STOPS if a file is missing in the media folder; a page is changed only if its raw_html block still has the fingerprints
# of plan.json (edited in the admin since -> SKIPPED and listed); apply is one transaction with a backup (a second apply is refused); undo puts the old HTML block back,
# only where the new blocks are still exactly what this script wrote, and then removes the Document rows this script made and their copies (the old files stay).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-46/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-46/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-46/apply.py
import collections
import json
import os

from django.conf import settings

from apps.content.migration_tools import fingerprint_ok, make_document, replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document

NAME = "yillik-hisobot-2026-46"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
LANGS = ("uz", "ru", "en")


def media_files():
    return sorted({block["data"]["uz"]["media"] for entry in PLAN for block in entry["blocks"] if block["block_type"] == "document"})


def build(apply):
    missing = [p for p in media_files() if not os.path.isfile(os.path.join(str(settings.MEDIA_ROOT), p))]
    if missing:
        raise SystemExit("STOP: files not found in %s:\n  %s" % (settings.MEDIA_ROOT, "\n  ".join(missing)))
    rows = {"entries": [], "document_pks": []}
    copies = {}
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
        new = []
        for spec in entry["blocks"]:
            if spec["block_type"] != "document":
                new.append(spec)
                continue
            path = spec["data"]["uz"]["media"]
            if path not in copies:
                copies[path] = make_document(os.path.join(str(settings.MEDIA_ROOT), path), spec["data"]["uz"]["caption"])
                rows["document_pks"].append(copies[path].pk)
            document = copies[path]
            new.append({"block_type": "document", "data": {lang: {"style": "card", "document_id": document.pk, "caption": spec["data"][lang]["caption"]} for lang in LANGS}})
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
    used = {(b.data.get("uz") or {}).get("document_id") for b in ContentBlock.objects.filter(block_type="document")}
    for document in Document.objects.filter(pk__in=rows["document_pks"]):
        if document.pk not in used:
            document.file.delete(save=False)  # the copy this script made
            document.delete()
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
