"""
Fetches every department from the live old-site API, runs the HTML
extraction + language merge, and prints a summary report -- no database
writes. Run directly:
    python -m apps.content.legacy_import.dry_run
(or, from apps/content/legacy_import/: `python dry_run.py`, since this
module only imports stdlib + bs4, no Django needed yet.)
"""
from __future__ import annotations

import sys

try:
    from .fetch import fetch_all_departments
    from .html_extract import extract
    from .merge import merge_languages
except ImportError:
    from fetch import fetch_all_departments
    from html_extract import extract
    from merge import merge_languages

LANGS = ("uz", "ru", "en")


def main() -> None:
    print("Fetching department list + uz/ru/en content from api.fermi.uz ...")
    departments = fetch_all_departments()
    print(f"Fetched {len(departments)} departments.\n")

    total_blocks = total_block_fallbacks = 0
    total_staff = total_staff_fallbacks = 0
    for dept in departments:
        results = {lang: extract(dept.content[lang]) for lang in LANGS}
        merged = merge_languages(results)

        raw_counts = {lang: (len(results[lang].blocks), len(results[lang].staff)) for lang in LANGS}
        print(f"[{dept.id:>3}] {dept.slug}")
        print(f"      raw (blocks, staff) per language: {raw_counts}")
        print(
            f"      merged: {len(merged.blocks)} blocks "
            f"({merged.fallback_block_count} used uz fallback for some language), "
            f"{len(merged.staff)} staff "
            f"({merged.fallback_staff_count} used uz fallback for some language)"
        )
        if merged.staff:
            names = ", ".join(s.full_name_by_lang["uz"] for s in merged.staff[:3])
            more = "" if len(merged.staff) <= 3 else f" (+{len(merged.staff) - 3} more)"
            print(f"      staff preview: {names}{more}")
        print()

        total_blocks += len(merged.blocks)
        total_block_fallbacks += merged.fallback_block_count
        total_staff += len(merged.staff)
        total_staff_fallbacks += merged.fallback_staff_count

    print(
        f"Done. {len(departments)} departments -- "
        f"{total_blocks} blocks total ({total_block_fallbacks} with a uz fallback), "
        f"{total_staff} staff total ({total_staff_fallbacks} with a uz fallback)."
    )


if __name__ == "__main__":
    sys.exit(main())
