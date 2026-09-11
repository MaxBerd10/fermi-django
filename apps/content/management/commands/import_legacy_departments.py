"""
Imports departments (kafedra) from the old Yii2 site's own live public API
(https://api.fermi.uz/v1/departments) into the new content-block schema.

Read-only against the old site (a GET-only API client, see legacy_import/
fetch.py) and idempotent against the new one: re-running for a slug that's
already been imported replaces it, so this is safe to run repeatedly while
iterating instead of accumulating duplicates.

Usage:
    python manage.py import_legacy_departments --dry-run          # report only, no writes
    python manage.py import_legacy_departments --dry-run --slug=pediatriya-kafedrasi
    python manage.py import_legacy_departments                     # the real import
    python manage.py import_legacy_departments --slug=pediatriya-kafedrasi
"""
from __future__ import annotations

import base64
import os
import ssl
import urllib.parse
import urllib.request

import certifi
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.content.legacy_import.fetch import fetch_department, fetch_department_slugs
from apps.content.legacy_import.html_extract import extract
from apps.content.legacy_import.merge import LANGS, MergeResult, merge_languages
from apps.content.models import ContentBlock, Page
from apps.departments.models import Department, StaffMember
from apps.media_lib.models import Image

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
_HEAD_KEYWORDS = ("kafedra mudiri", "kafedra mudirasi", "заведующ")


class Command(BaseCommand):
    help = "Import departments from the old site's live API into Department/Page/ContentBlock/StaffMember."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch, extract, and report only -- writes nothing."
        )
        parser.add_argument("--slug", help="Import only this one department slug (for testing).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        only_slug = options.get("slug")
        self._image_cache: dict[str, Image | None] = {}

        slugs = [only_slug] if only_slug else fetch_department_slugs()
        self.stdout.write(f"{len(slugs)} department(s) to process.\n")

        done = 0
        for slug in slugs:
            dept = fetch_department(slug)
            results = {lang: extract(dept.content[lang]) for lang in LANGS}
            merged = merge_languages(results)

            self.stdout.write(
                f"[{dept.id}] {slug}: {len(merged.blocks)} blocks "
                f"({merged.fallback_block_count} needing translation review), "
                f"{len(merged.staff)} staff "
                f"({merged.fallback_staff_count} needing translation review)"
            )

            if dry_run:
                done += 1
                continue

            with transaction.atomic():
                self._import_one(dept, merged)
            done += 1

        verb = "Would import" if dry_run else "Imported"
        self.stdout.write(self.style.SUCCESS(f"\n{verb} {done} department(s)."))

    # -- media -----------------------------------------------------------

    def _get_or_download_image(self, src: str | None) -> Image | None:
        if not src:
            return None
        if src in self._image_cache:
            return self._image_cache[src]

        image: Image | None
        try:
            if src.startswith("data:"):
                # A handful of legacy images were pasted straight into the
                # editor as inline base64 rather than uploaded -- decode
                # instead of trying to fetch a "URL" that isn't one.
                header, _, b64_body = src.partition(",")
                content = base64.b64decode(b64_body)
                ext = "png" if "png" in header else "jpg"
                filename = f"inline.{ext}"
            else:
                url = src if src.startswith("http") else f"https://api.fermi.uz{src}"
                req = urllib.request.Request(url, headers={"User-Agent": "fermi-django-migration/0.1"})
                with urllib.request.urlopen(req, timeout=20, context=_SSL_CONTEXT) as resp:
                    content = resp.read()
                filename = urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(url).path)) or "image.jpg"
            image = Image(alt_text="")
            image.file.save(filename, ContentFile(content), save=False)
            image.full_clean()
            image.save()
        except Exception as exc:  # noqa: BLE001 -- a broken/missing legacy image must not abort the import
            self.stderr.write(self.style.WARNING(f"    could not load image {src[:80]}: {exc}"))
            image = None

        self._image_cache[src] = image
        return image

    # -- import ------------------------------------------------------------

    def _import_one(self, dept, merged: MergeResult) -> None:
        existing = Department.objects.filter(slug=dept.slug).first()
        if existing:
            page_id = existing.page_id
            existing.delete()
            Page.objects.filter(pk=page_id).delete()

        logo = self._get_or_download_image(dept.logo_url)
        page = Page.objects.create(slug=dept.slug)
        department = Department.objects.create(
            slug=dept.slug,
            name_uz=dept.title["uz"],
            name_ru=dept.title["ru"] or dept.title["uz"],
            name_en=dept.title["en"] or dept.title["uz"],
            logo=logo,
            page=page,
        )

        order = 1
        for block in merged.blocks:
            data = {}
            skip_block = False
            for lang in LANGS:
                payload = dict(block.payload_by_lang[lang])
                if block.block_type == "image":
                    img = self._get_or_download_image(payload.pop("image_src", None))
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

        for index, person in enumerate(merged.staff):
            photo = self._get_or_download_image(person.photo_src)
            is_head = any(
                kw in (person.title_by_lang["uz"] + " " + person.bio_by_lang["uz"]).lower()
                for kw in _HEAD_KEYWORDS
            )
            StaffMember.objects.create(
                department=department,
                full_name=person.full_name_by_lang["uz"],
                title_uz=person.title_by_lang["uz"],
                title_ru=person.title_by_lang["ru"],
                title_en=person.title_by_lang["en"],
                bio_uz=person.bio_by_lang["uz"],
                bio_ru=person.bio_by_lang["ru"],
                bio_en=person.bio_by_lang["en"],
                photo=photo,
                is_head=is_head,
                order=index,
            )
