"""
Shared image-download-and-cache helper for every legacy import command
(departments, faculties, news) -- factored out once duplicated across two
of them, so a fix (like data: URI support) only needs to happen in one
place.
"""
from __future__ import annotations

import base64
import os
import ssl
import urllib.parse
import urllib.request

import certifi
from django.core.files.base import ContentFile

from apps.media_lib.models import Document, Image

_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


class ImageDownloader:
    """Downloads a legacy image src (an absolute URL, a site-relative path,
    or an inline data: URI) into a real Image row, caching by src so the
    same photo referenced from multiple places (e.g. a person's photo
    appearing in uz/ru/en bodies) is only fetched once."""

    def __init__(self, on_error=None):
        self._cache: dict[str, Image | None] = {}
        self._on_error = on_error or (lambda src, exc: None)

    def get_or_download(self, src: str | None) -> Image | None:
        if not src:
            return None
        if src in self._cache:
            return self._cache[src]

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
            self._on_error(src, exc)
            image = None

        self._cache[src] = image
        return image


class DocumentDownloader:
    """Same idea as ImageDownloader, for the files referenced by a page's
    `file` field (bylaws, council/journal archives, schedule spreadsheets,
    ...) -- downloads once, caches by src, and a broken/missing legacy file
    is skipped rather than aborting the whole import."""

    def __init__(self, on_error=None, allowed_extensions: tuple[str, ...] = ("pdf",)):
        self._cache: dict[str, Document | None] = {}
        self._on_error = on_error or (lambda src, exc: None)
        self._allowed_extensions = allowed_extensions

    def get_or_download(self, src: str | None) -> Document | None:
        if not src:
            return None
        if src in self._cache:
            return self._cache[src]

        document: Document | None
        try:
            url = src if src.startswith("http") else f"https://api.fermi.uz{src}"
            req = urllib.request.Request(url, headers={"User-Agent": "fermi-django-migration/0.1"})
            with urllib.request.urlopen(req, timeout=20, context=_SSL_CONTEXT) as resp:
                content = resp.read()
            default_name = f"document.{self._allowed_extensions[0]}"
            filename = urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(url).path)) or default_name
            if not filename.lower().endswith(tuple(f".{ext}" for ext in self._allowed_extensions)):
                # Document's FileExtensionValidator only accepts a known set
                # of extensions -- a legacy "file" outside that set (a stray
                # .docx/.jpg link) has nowhere to go here, so it's skipped
                # rather than crashing the whole import.
                raise ValueError(f"unsupported file type: {filename}")
            document = Document(title="")
            document.file.save(filename, ContentFile(content), save=False)
            document.full_clean()
            document.save()
        except Exception as exc:  # noqa: BLE001 -- a broken/missing legacy document must not abort the import
            self._on_error(src, exc)
            document = None

        self._cache[src] = document
        return document

    def get_or_copy(self, path: str | None) -> Document | None:
        """Copy a recovered legacy file into Django storage.

        Some old API URLs have been deleted while the original Yii upload is
        still present on the same server.  This keeps recovery explicit: the
        caller supplies the exact file path rather than the importer scanning
        arbitrary server directories.
        """
        if not path:
            return None
        cache_key = f"file://{path}"
        if cache_key in self._cache:
            return self._cache[cache_key]

        document: Document | None
        try:
            filename = os.path.basename(path)
            if not filename.lower().endswith(tuple(f".{ext}" for ext in self._allowed_extensions)):
                raise ValueError(f"unsupported file type: {filename}")
            with open(path, "rb") as source:
                content = source.read()
            document = Document(title="")
            document.file.save(filename, ContentFile(content), save=False)
            document.full_clean()
            document.save()
        except Exception as exc:  # noqa: BLE001 -- an invalid backup must not abort the import
            self._on_error(path, exc)
            document = None

        self._cache[cache_key] = document
        return document
