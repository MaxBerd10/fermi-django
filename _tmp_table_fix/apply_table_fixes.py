"""Applies the verified-safe table-block conversion to the 8 candidate pages
from table_candidates.json / verify_results.json: re-extracts each page's
content with the now-table-aware extract() and replaces its ContentBlocks
with the result, while preserving any existing non-content blocks (image/
document/video/gallery -- these come from page.file_url, not the "content"
HTML field extract() reads, so a fresh extraction never produces them).

Only ever touches these specific, individually-verified slugs -- never the
forbidden import_legacy_* management commands, and never a bulk "reimport
everything" pass. Each page is one atomic transaction; a failure on one
page doesn't affect the others already done.

Run with:
    set -a; source /etc/fermi-django.env; set +a
    .venv/bin/python apply_table_fixes.py            # dry run: prints the plan, writes nothing
    .venv/bin/python apply_table_fixes.py --apply     # actually writes
"""
import json
import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.db import transaction

from apps.content.legacy_import.fetch import fetch_page
from apps.content.legacy_import.html_extract import extract
from apps.content.legacy_import.media import ImageDownloader
from apps.content.legacy_import.merge import LANGS, merge_languages
from apps.content.models import ContentBlock, Page

APPLY = "--apply" in sys.argv

SLUGS = [
    "meyoriy-hujjatlar",
    "tibbiy-talimga-tadqiq-etilgan-ilmiy-tadqiqot-ishlari",
    "hujjat-turlari",
    "ordinaturaga-hujjat-topshirish-2025",
    "xorijiy-talabalar-uchun-tolov-kontrakatlar-miqdori",
    # Deliberately NOT included: vrachlar-malakasini-oshirish-sertifikati.
    # Its real content turns out to be several separate course/certificate
    # sections (each its own image+table+heading), not the one clean table
    # this pass was built and verified against -- extraction under-captures
    # it (3 blocks instead of the real content). Its current DB content was
    # already minimal (169 chars) before this, so leaving it alone is not a
    # regression, just not yet a fix; needs its own follow-up look.
    #
    # Deliberately NOT included: grantlar-taqsimoti, grant-taqsimoti. Both
    # have a real 2-level header (a year label spanning 3 sub-columns each)
    # that _build_table_grid's "last fully-bold row wins" rule can't
    # represent without losing which year group each "Jami/o'zbek/rus"
    # triple belongs to -- a real information loss, not just a redundant
    # label like the other pages' grouping rows. Left as their current
    # (correct, if unstyled) flattened paragraphs until the extractor grows
    # real support for combining a multi-level header into one label.
]

images = ImageDownloader(on_error=lambda src, exc: print(f"    WARNING: could not load image {src[:80]}: {exc}"))

print(f"Mode: {'APPLY (writing changes)' if APPLY else 'DRY RUN (no writes)'}\n")

for slug in SLUGS:
    print(f"=== {slug} ===")
    try:
        page = fetch_page(slug)
        results = {lang: extract(page.content[lang]) for lang in LANGS}
        merged = merge_languages(results)
    except Exception as exc:  # noqa: BLE001
        print(f"  FETCH/EXTRACT ERROR: {exc} -- skipped\n")
        continue

    content_page = Page.objects.filter(slug=slug).first()
    if content_page is None:
        print("  no existing Page for this slug -- skipped (expected an existing page to update)\n")
        continue

    preserved = list(
        ContentBlock.objects.filter(page=content_page, block_type__in=["image", "document", "video", "gallery"])
        .order_by("order")
    )
    old_count = ContentBlock.objects.filter(page=content_page).count()
    table_count = sum(1 for b in merged.blocks if b.block_type == "table")

    print(
        f"  replacing {old_count} existing block(s) with {len(merged.blocks)} new block(s) "
        f"({table_count} table), preserving {len(preserved)} image/document/video/gallery block(s)"
    )

    if not APPLY:
        print()
        continue

    with transaction.atomic():
        preserved_data = [(b.block_type, b.data) for b in preserved]
        ContentBlock.objects.filter(page=content_page).delete()

        order = 1
        for block in merged.blocks:
            data = {}
            skip_block = False
            for lang in LANGS:
                payload = dict(block.payload_by_lang[lang])
                if block.block_type == "image":
                    img = images.get_or_download(payload.pop("image_src", None))
                    if img is None:
                        skip_block = True
                        break
                    payload["image_id"] = img.id
                    payload.setdefault("alt", "")
                data[lang] = payload
            if skip_block:
                continue
            cb = ContentBlock(page=content_page, order=order, block_type=block.block_type, data=data)
            cb.full_clean()
            cb.save()
            order += 1

        for block_type, data in preserved_data:
            cb = ContentBlock(page=content_page, order=order, block_type=block_type, data=data)
            cb.full_clean()
            cb.save()
            order += 1

    print(f"  done -- page now has {ContentBlock.objects.filter(page=content_page).count()} block(s)\n")

print("Finished." if APPLY else "Dry run complete -- pass --apply to write.")
