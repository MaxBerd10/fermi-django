"""
Imports the public photo gallery from the old site's live public API into
GalleryPhoto. Flat and uncaptioned on the old site (confirmed: every entry's
title is empty in every language) -- so this only downloads each photo and
records its original listing order, nothing more.

Idempotent: re-running clears and rebuilds every GalleryPhoto row, same as
the other legacy importers -- safe to run repeatedly while iterating.

Usage:
    python manage.py import_legacy_gallery --dry-run
    python manage.py import_legacy_gallery
    python manage.py import_legacy_gallery --limit=20   # for a quick test run
"""
from __future__ import annotations

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.legacy_import.fetch import fetch_all_gallery_photos
from apps.content.legacy_import.media import ImageDownloader
from apps.media_lib.models import GalleryPhoto


class Command(BaseCommand):
    help = "Import the public photo gallery from the old site's live API into GalleryPhoto."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch and report only -- writes nothing."
        )
        parser.add_argument("--limit", type=int, help="Import only the first N photos (for testing).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options.get("limit")
        images = ImageDownloader(
            on_error=lambda src, exc: self.stderr.write(self.style.WARNING(f"    could not load image {src[:80]}: {exc}"))
        )

        photos = fetch_all_gallery_photos()
        if limit:
            photos = photos[:limit]
        self.stdout.write(f"{len(photos)} gallery photo(s) to process.\n")

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Would import {len(photos)} gallery photo(s)."))
            return

        imported = 0
        with transaction.atomic():
            GalleryPhoto.objects.all().delete()
            # The old site's listing is newest-first by id; GalleryPhoto.order
            # mirrors that (higher = more recent), matching Meta.ordering.
            total = len(photos)
            for index, photo in enumerate(photos):
                image = images.get_or_download(photo.img)
                if image is None:
                    continue
                GalleryPhoto.objects.create(image=image, order=total - index)
                imported += 1

        self.stdout.write(self.style.SUCCESS(f"\nImported {imported} gallery photo(s)."))
