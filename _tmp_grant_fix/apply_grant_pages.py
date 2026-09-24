import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, "/Users/maxberd/Desktop/fermi-django")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from django.db import transaction

from apps.content.legacy_import.fetch import fetch_page
from apps.content.legacy_import.html_extract import extract
from apps.content.legacy_import.merge import LANGS, merge_languages
from apps.content.models import ContentBlock, Page

APPLY = "--apply" in sys.argv
SLUGS = ["grantlar-taqsimoti", "grant-taqsimoti"]

print(f"Mode: {'APPLY (writing changes)' if APPLY else 'DRY RUN (no writes)'}\n")

for slug in SLUGS:
    print(f"=== {slug} ===")
    page = fetch_page(slug)
    results = {lang: extract(page.content[lang]) for lang in LANGS}
    merged = merge_languages(results)

    content_page = Page.objects.filter(slug=slug).first()
    if content_page is None:
        print("  no existing Page -- skipped\n")
        continue

    old_count = ContentBlock.objects.filter(page=content_page).count()
    table_count = sum(1 for b in merged.blocks if b.block_type == "table")
    print(f"  replacing {old_count} existing block(s) with {len(merged.blocks)} new block(s) ({table_count} table)")

    if not APPLY:
        print()
        continue

    with transaction.atomic():
        ContentBlock.objects.filter(page=content_page).delete()
        order = 1
        for block in merged.blocks:
            data = {lang: dict(block.payload_by_lang[lang]) for lang in LANGS}
            cb = ContentBlock(page=content_page, order=order, block_type=block.block_type, data=data)
            cb.full_clean()
            cb.save()
            order += 1
    print(f"  done -- page now has {ContentBlock.objects.filter(page=content_page).count()} block(s)\n")

print("Finished." if APPLY else "Dry run complete -- pass --apply to write.")
