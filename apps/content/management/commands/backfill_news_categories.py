"""
Backfills NewsCategory + NewsPost.category for posts already imported by
import_legacy_news -- a lighter pass than re-running that command (which
would re-download every cover image and re-create every ContentBlock).
Every post's own detail response already carries its category (id/slug
per language-invariant, title per language), so this just re-fetches each
existing post once per language and sets its category, touching nothing
else.

Usage:
    python manage.py backfill_news_categories --dry-run --limit=20
    python manage.py backfill_news_categories
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.legacy_import.fetch import fetch_news_post
from apps.news.models import NewsCategory, NewsPost


class Command(BaseCommand):
    help = "Backfill NewsCategory + NewsPost.category for already-imported posts."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch and report only -- writes nothing."
        )
        parser.add_argument("--limit", type=int, help="Only the first N posts (for testing).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options.get("limit")

        slugs = list(NewsPost.objects.order_by("id").values_list("slug", flat=True))
        if limit:
            slugs = slugs[:limit]
        self.stdout.write(f"{len(slugs)} post(s) to process.\n")

        done = skipped = 0
        for slug in slugs:
            try:
                post = fetch_news_post(slug)
            except Exception as exc:  # noqa: BLE001 -- one bad slug must not abort the whole run
                self.stderr.write(self.style.WARNING(f"[skip] {slug}: could not fetch ({exc})"))
                skipped += 1
                continue

            cat = post.category_by_lang.get("uz") or {}
            cat_slug = cat.get("slug")
            if not cat_slug:
                skipped += 1
                continue

            self.stdout.write(f"{slug} -> {cat_slug}")
            if dry_run:
                done += 1
                continue

            with transaction.atomic():
                category, _ = NewsCategory.objects.update_or_create(
                    slug=cat_slug,
                    defaults={
                        "name_uz": (post.category_by_lang.get("uz") or {}).get("title") or cat_slug,
                        "name_ru": (post.category_by_lang.get("ru") or {}).get("title") or cat_slug,
                        "name_en": (post.category_by_lang.get("en") or {}).get("title") or cat_slug,
                    },
                )
                NewsPost.objects.filter(slug=slug).update(category=category)
            done += 1

        verb = "Would update" if dry_run else "Updated"
        self.stdout.write(self.style.SUCCESS(f"\n{verb} {done} post(s) ({skipped} skipped)."))
