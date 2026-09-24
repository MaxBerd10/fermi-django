"""Switches a document ContentBlock's style from "button" (a bare download
link) to "roadmap" (BlockRenderer's existing embedded-PDF-viewer template,
already used for "Institut yo'l xaritasi") for every page whose ENTIRE
content is just that one document block -- a page that's literally nothing
but a PDF attachment currently shows just a small button with a lot of
empty space next to it (reported live: 14.00.03.Endokrinologiya and
siblings under the Doktorantura menu). Scoped to exactly that pattern
(single document block, nothing else) so a page that legitimately uses a
download button alongside real body text elsewhere is left untouched --
this is a pure data change, no template/code change needed, since
BlockRenderer already fully implements the "roadmap" style.

Run with:
    set -a; source /etc/fermi-django.env; set +a
    .venv/bin/python switch_pdf_to_roadmap.py            # dry run
    .venv/bin/python switch_pdf_to_roadmap.py --apply     # actually writes
"""
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from apps.content.models import ContentBlock, Page

APPLY = "--apply" in sys.argv

print(f"Mode: {'APPLY (writing changes)' if APPLY else 'DRY RUN (no writes)'}\n")

candidates = []
for page in Page.objects.all():
    blocks = list(ContentBlock.objects.filter(page=page))
    if len(blocks) == 1 and blocks[0].block_type == "document":
        block = blocks[0]
        if block.data.get("uz", {}).get("style") == "button":
            candidates.append((page, block))

print(f"{len(candidates)} page(s) with only a single button-style document block:\n")
for page, block in candidates:
    filename = block.data.get("uz", {}).get("document", {}).get("filename", "?")
    print(f"  [{page.id}] {page.slug} -> {filename}")
    if APPLY:
        for lang in ("uz", "ru", "en"):
            if lang in block.data:
                block.data[lang]["style"] = "roadmap"
        block.full_clean()
        block.save()

print("\nFinished." if APPLY else "\nDry run complete -- pass --apply to write.")
