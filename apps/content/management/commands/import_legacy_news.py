"""
Imports news posts from the old site's live public API into
NewsPost/Page/ContentBlock.

News content is structurally the same free-form HTML as a department's
body -- reuses the same extraction + language-alignment pipeline (see
html_extract.py / merge.py). Unlike departments, a news post has no staff
bios, so extract()'s staff-detection heuristic finding something here is
never used; it isn't wired into NewsPost.

The old site has ~500+ posts and returning content in three languages per
post means three API calls each, so --limit exists to fetch only the N
most recent ones (newest first) rather than the whole archive on every
test run. The old API also serves some slugs from an entirely separate
Telegram-import pipeline (see the old frontend's isTelegramNewsSlug) with
a different data shape; those are out of scope here and simply fail to
fetch a normal detail response, which this command skips over rather than
crashing the whole batch on one bad slug.

Usage:
    python manage.py import_legacy_news --dry-run --limit=20
    python manage.py import_legacy_news --limit=20
    python manage.py import_legacy_news              # the full archive
"""
from __future__ import annotations

from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.content.legacy_import.fetch import fetch_news_post, fetch_news_slugs
from apps.content.legacy_import.html_extract import extract
from apps.content.legacy_import.media import ImageDownloader
from apps.content.legacy_import.merge import LANGS, merge_languages
from apps.content.models import ContentBlock, Page
from apps.news.models import NewsPost

_EXCERPT_MAX = 500


class Command(BaseCommand):
    help = "Import news posts from the old site's live API into NewsPost/Page/ContentBlock."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch, extract, and report only -- writes nothing."
        )
        parser.add_argument("--slug", help="Import only this one news slug (for testing).")
        parser.add_argument("--limit", type=int, help="Import only the N most recent posts.")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        only_slug = options.get("slug")
        limit = options.get("limit")
        self._images = ImageDownloader(
            on_error=lambda src, exc: self.stderr.write(self.style.WARNING(f"    could not load image {src[:80]}: {exc}"))
        )

        slugs = [only_slug] if only_slug else fetch_news_slugs(limit=limit)
        self.stdout.write(f"{len(slugs)} news post(s) to process.\n")

        done = skipped = 0
        for slug in slugs:
            try:
                post = fetch_news_post(slug)
            except Exception as exc:  # noqa: BLE001 -- a Telegram-sourced or otherwise odd slug shouldn't abort the batch
                self.stderr.write(self.style.WARNING(f"[skip] {slug}: could not fetch ({exc})"))
                skipped += 1
                continue

            results = {lang: extract(post.content[lang]) for lang in LANGS}
            merged = merge_languages(results)

            self.stdout.write(
                f"[{post.id}] {slug}: {len(merged.blocks)} blocks "
                f"({merged.fallback_block_count} needing translation review)"
            )

            if dry_run:
                done += 1
                continue

            with transaction.atomic():
                self._import_one(post, merged)
            done += 1

        verb = "Would import" if dry_run else "Imported"
        self.stdout.write(self.style.SUCCESS(f"\n{verb} {done} news post(s) ({skipped} skipped)."))

    # -- helpers -------------------------------------------------------

    @staticmethod
    def _excerpt(merged) -> dict[str, str]:
        out = {}
        for lang in LANGS:
            text = ""
            for block in merged.blocks:
                if block.block_type in ("heading", "paragraph"):
                    text = block.payload_by_lang[lang].get("text", "")
                    if text:
                        break
            out[lang] = text[:_EXCERPT_MAX]
        return out

    @staticmethod
    def _published_at(raw: str | None):
        if not raw:
            return timezone.now()
        try:
            naive = datetime.strptime(raw, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            return timezone.now()
        return timezone.make_aware(naive)

    # -- import ----------------------------------------------------------

    def _import_one(self, post, merged) -> None:
        existing = NewsPost.objects.filter(slug=post.slug).first()
        if existing:
            page_id = existing.page_id
            existing.delete()
            Page.objects.filter(pk=page_id).delete()

        cover = self._images.get_or_download(post.cover_url)
        excerpt = self._excerpt(merged)
        # Page.slug is a separate, purely-internal join key -- never used
        # for URLs (NewsPost.slug is) -- see import_legacy_departments.py
        # for why it's namespaced by content type + id rather than reusing
        # the public slug (a real collision: this exact post's slug is
        # also a faculty's slug).
        page = Page.objects.create(slug=f"news-{post.id}")
        NewsPost.objects.create(
            slug=post.slug,
            title_uz=post.title["uz"],
            title_ru=post.title["ru"] or post.title["uz"],
            title_en=post.title["en"] or post.title["uz"],
            excerpt_uz=excerpt["uz"],
            excerpt_ru=excerpt["ru"] or excerpt["uz"],
            excerpt_en=excerpt["en"] or excerpt["uz"],
            cover=cover,
            page=page,
            published_at=self._published_at(post.published_at),
        )

        order = 1
        for block in merged.blocks:
            data = {}
            skip_block = False
            for lang in LANGS:
                payload = dict(block.payload_by_lang[lang])
                if block.block_type == "image":
                    img = self._images.get_or_download(payload.pop("image_src", None))
                    if img is None:
                        skip_block = True
                        break
                    payload["image_id"] = img.id
                    payload.setdefault("alt", "")
                data[lang] = payload
            if skip_block:
                continue
            content_block = ContentBlock(page=page, order=order, block_type=block.block_type, data=data)
            content_block.full_clean()
            content_block.save()
            order += 1
