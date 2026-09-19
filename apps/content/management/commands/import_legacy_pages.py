"""
Imports the ~235 static/informational pages from the old site's own nav
tree (bylaws, council/journal/newspaper archives, admission info, building
descriptions, ...) into standalone Page/ContentBlock rows -- the exact same
free-form-HTML-body shape as a department's or faculty's page, just with no
Department/Faculty wrapping it.

Unlike departments/faculties (each namespaces its Page.slug as
"department-{id}"/"faculty-{id}" to avoid colliding with its own public
slug), these ARE the public slug directly -- confirmed against the current
DB that none of the 235 collide with an existing Page/Department/Faculty
slug.

A page's optional `file` (almost always a PDF -- bylaws, archives) becomes
one extra `document` ContentBlock appended after the body content, so the
frontend's generic BlockRenderer needs no special "this page has a PDF"
case; it just renders whatever blocks are there.

Usage:
    python manage.py import_legacy_pages --dry-run
    python manage.py import_legacy_pages --dry-run --slug=institut-tarixi
    python manage.py import_legacy_pages --limit=10   # test run
    python manage.py import_legacy_pages
"""
from __future__ import annotations

import os
import unicodedata
from collections import defaultdict
from urllib.parse import unquote

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.content.legacy_import.fetch import fetch_page, fetch_page_slugs
from apps.content.legacy_import.html_extract import extract
from apps.content.legacy_import.media import DocumentDownloader, ImageDownloader
from apps.content.legacy_import.merge import LANGS, merge_languages
from apps.content.models import ContentBlock, Page


def _certificate_label(source: str | None) -> str:
    """The old certificate page displayed these five legacy image labels."""
    filename = unquote(source or "").casefold()
    if "ui" in filename:
        return "UI — 2025"
    if "dentistry" in filename:
        return "Stomatologiya"
    if "pediatrics" in filename:
        return "Pediatriya"
    if "pharmacy" in filename:
        return "Farmatsiya"
    if "akreditatsiya" in filename:
        return "Fargʻona jamoat salomatligi tibbiyot institutining davlat akkreditatsiyadan oʻtganligi toʻgʻrisida rasmiy hujjat sertifikati"
    return "Sertifikat"


def _document_key(value: str) -> str:
    """Make legacy URL/file names comparable across URL and Unicode variants."""
    decoded = unquote(os.path.basename(value))
    normalized = unicodedata.normalize("NFKD", decoded).casefold()
    return "".join(char for char in normalized if char.isalnum())


class LegacyDocumentFinder:
    """Find one unambiguous PDF in a supplied, retained legacy uploads tree."""

    def __init__(self, root: str):
        if not os.path.isdir(root):
            raise CommandError(f"--legacy-media-root is not a readable directory: {root}")
        self._by_name: dict[str, list[str]] = defaultdict(list)
        for directory, _, filenames in os.walk(root):
            for filename in filenames:
                if filename.casefold().endswith(".pdf"):
                    self._by_name[_document_key(filename)].append(os.path.join(directory, filename))

    def find(self, source: str | None) -> str | None:
        if not source:
            return None
        matches = self._by_name.get(_document_key(source), [])
        return matches[0] if len(matches) == 1 else None


class Command(BaseCommand):
    help = "Import the old site's static pages into standalone Page/ContentBlock rows."

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true", help="Fetch, extract, and report only -- writes nothing."
        )
        parser.add_argument("--slug", help="Import only this one page slug (for testing).")
        parser.add_argument("--limit", type=int, help="Import only the first N pages (for testing).")
        parser.add_argument(
            "--preserve-layout",
            action="store_true",
            help="Keep legacy HTML as one sanitized block so its media layout remains unchanged.",
        )
        parser.add_argument(
            "--document-source",
            help="Exact path to a recovered local PDF to attach instead of the old API file URL.",
        )
        parser.add_argument(
            "--legacy-media-root",
            help="Retained legacy uploads directory used only to recover uniquely named PDF attachments.",
        )

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        only_slug = options.get("slug")
        limit = options.get("limit")
        preserve_layout = options["preserve_layout"]
        document_source = options.get("document_source")
        legacy_media_root = options.get("legacy_media_root")
        if document_source and not only_slug:
            raise ValueError("--document-source requires --slug so it cannot be attached to multiple pages")
        images = ImageDownloader(
            on_error=lambda src, exc: self.stderr.write(self.style.WARNING(f"    could not load image {src[:80]}: {exc}"))
        )
        documents = DocumentDownloader(
            on_error=lambda src, exc: self.stderr.write(self.style.WARNING(f"    could not load document {src[:80]}: {exc}"))
        )
        recovered_documents = LegacyDocumentFinder(legacy_media_root) if legacy_media_root else None
        if recovered_documents:
            recovered_count = sum(len(paths) for paths in recovered_documents._by_name.values())
            self.stdout.write(f"Indexed {recovered_count} legacy PDF file(s) for recovery.\n")

        slugs = [only_slug] if only_slug else fetch_page_slugs()
        if limit:
            slugs = slugs[:limit]
        self.stdout.write(f"{len(slugs)} page(s) to process.\n")

        done = 0
        skipped = 0
        for slug in slugs:
            try:
                page = fetch_page(slug)
            except Exception as exc:  # noqa: BLE001 -- one bad slug must not abort the whole run
                self.stderr.write(self.style.WARNING(f"[{slug}] fetch failed: {exc}"))
                skipped += 1
                continue

            results = {lang: extract(page.content[lang]) for lang in LANGS}
            merged = merge_languages(results)

            self.stdout.write(
                f"[{page.id}] {slug}: {len(merged.blocks)} blocks "
                f"({merged.fallback_block_count} needing translation review)"
                f"{' + PDF' if page.file_url else ''}"
                f"{' [preserve layout]' if preserve_layout else ''}"
            )

            if dry_run:
                done += 1
                continue

            with transaction.atomic():
                self._import_one(
                    slug, page, merged, images, documents, preserve_layout, document_source, recovered_documents
                )
            done += 1

        verb = "Would import" if dry_run else "Imported"
        self.stdout.write(self.style.SUCCESS(f"\n{verb} {done} page(s) ({skipped} skipped)."))

    def _import_one(
        self,
        slug,
        page,
        merged,
        images: ImageDownloader,
        documents: DocumentDownloader,
        preserve_layout: bool,
        document_source: str | None,
        recovered_documents: LegacyDocumentFinder | None,
    ) -> None:
        Page.objects.filter(slug=slug).delete()
        content_page = Page.objects.create(slug=slug)

        if preserve_layout:
            if slug == "institut-tuzilmasi":
                # This is not an ordinary article on the legacy site: it is a
                # horizontally scrollable/zoomable organisation chart followed
                # by a simple download action.  Preserve those two components
                # as structured blocks so the new page uses the same template
                # rather than treating the chart as a narrow article image.
                order = 1
                for block in merged.blocks:
                    if block.block_type != "image":
                        continue
                    data = {}
                    for lang in LANGS:
                        source = block.payload_by_lang[lang].get("image_src")
                        image = images.get_or_download(source)
                        if image is None:
                            data = {}
                            break
                        data[lang] = {
                            "image_id": image.id,
                            "alt": "Institut tuzilmasi sxemasi",
                            "style": "diagram",
                        }
                    if not data:
                        continue
                    content_block = ContentBlock(
                        page=content_page,
                        order=order,
                        block_type=ContentBlock.BlockType.IMAGE,
                        data=data,
                    )
                    content_block.full_clean()
                    content_block.save()
                    order += 1

                if page.file_url:
                    document = self._load_document(documents, page.file_url, recovered_documents)
                    if document is not None:
                        content_block = ContentBlock(
                            page=content_page,
                            order=order,
                            block_type=ContentBlock.BlockType.DOCUMENT,
                            data={lang: {"document_id": document.id, "style": "button"} for lang in LANGS},
                        )
                        content_block.full_clean()
                        content_block.save()
                return

            if slug == "institut-sertifikatlari":
                # This legacy page keeps its certificate images outside the
                # article HTML.  A raw HTML block would therefore preserve
                # only the short description and discard the actual gallery.
                # Keep the non-image blocks in source order and collect the
                # images into the card gallery used by the old page.
                order = 1
                gallery_items = {lang: [] for lang in LANGS}

                def save_gallery():
                    nonlocal order
                    if not all(gallery_items[lang] for lang in LANGS):
                        return
                    content_block = ContentBlock(
                        page=content_page,
                        order=order,
                        block_type=ContentBlock.BlockType.GALLERY,
                        data={
                            lang: {"items": gallery_items[lang], "style": "certificate"}
                            for lang in LANGS
                        },
                    )
                    content_block.full_clean()
                    content_block.save()
                    order += 1

                for block in merged.blocks:
                    if block.block_type == "image":
                        for lang in LANGS:
                            source = block.payload_by_lang[lang].get("image_src")
                            image = images.get_or_download(source)
                            if image is not None:
                                gallery_items[lang].append({"image_id": image.id, "alt": _certificate_label(source)})
                        continue

                    save_gallery()
                    gallery_items = {lang: [] for lang in LANGS}
                    content_block = ContentBlock(
                        page=content_page,
                        order=order,
                        block_type=block.block_type,
                        data={lang: dict(block.payload_by_lang[lang]) for lang in LANGS},
                    )
                    content_block.full_clean()
                    content_block.save()
                    order += 1

                save_gallery()
                if page.file_url:
                    document = self._load_document(documents, page.file_url, recovered_documents, document_source)
                    if document is not None:
                        content_block = ContentBlock(
                            page=content_page,
                            order=order,
                            block_type=ContentBlock.BlockType.DOCUMENT,
                            data={lang: {"document_id": document.id, "style": "button"} for lang in LANGS},
                        )
                        content_block.full_clean()
                        content_block.save()
                return

            if slug == "institut-yol-xaritasi-2025" and document_source:
                # The legacy API URL for this attachment is gone, but the
                # recovered original file can be attached explicitly.  The
                # old page was an embedded PDF viewer rather than the editor
                # image currently returned by the API, so prefer that source
                # when it is available.
                document = documents.get_or_copy(document_source)
                if document is not None:
                    content_block = ContentBlock(
                        page=content_page,
                        order=1,
                        block_type=ContentBlock.BlockType.DOCUMENT,
                        data={
                            lang: {
                                "document_id": document.id,
                                "caption": "Institut yo‘l xaritasi – 2026",
                                "style": "roadmap",
                            }
                            for lang in LANGS
                        },
                    )
                    content_block.full_clean()
                    content_block.save()
                    return

            # A few old pages are attachment-only or have an empty translation
            # slot.  Keep the visual source from the first non-empty language
            # instead of aborting the full import halfway through; for pages
            # with no body at all, continue below so their document block can
            # still be imported.
            fallback_html = next((page.content[lang] for lang in LANGS if page.content[lang].strip()), None)
            if fallback_html:
                content_block = ContentBlock(
                    page=content_page,
                    order=1,
                    block_type=ContentBlock.BlockType.RAW_HTML,
                    data={lang: {"html": page.content[lang] or fallback_html, "slug": slug} for lang in LANGS},
                )
                content_block.full_clean()
                content_block.save()
                order = 2
            else:
                order = 1

            if page.file_url:
                document = self._load_document(documents, page.file_url, recovered_documents, document_source)
                if document is not None:
                    content_block = ContentBlock(
                        page=content_page,
                        order=order,
                        block_type=ContentBlock.BlockType.DOCUMENT,
                        data={lang: {"document_id": document.id, "style": "button"} for lang in LANGS},
                    )
                    content_block.full_clean()
                    content_block.save()
            return

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
            content_block = ContentBlock(page=content_page, order=order, block_type=block.block_type, data=data)
            content_block.full_clean()
            content_block.save()
            order += 1

        if page.file_url:
            document = self._load_document(documents, page.file_url, recovered_documents, document_source)
            if document is not None:
                data = {lang: {"document_id": document.id, "style": "button"} for lang in LANGS}
                content_block = ContentBlock(page=content_page, order=order, block_type="document", data=data)
                content_block.full_clean()
                content_block.save()

    @staticmethod
    def _load_document(
        documents: DocumentDownloader,
        source: str | None,
        recovered_documents: LegacyDocumentFinder | None,
        explicit_source: str | None = None,
    ):
        if explicit_source:
            return documents.get_or_copy(explicit_source)
        recovered_path = recovered_documents.find(source) if recovered_documents else None
        return documents.get_or_copy(recovered_path) if recovered_path else documents.get_or_download(source)
