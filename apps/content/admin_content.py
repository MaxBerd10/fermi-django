"""
Bridges the admin panel's single rich-text-HTML-per-language editing model
onto this project's real content storage (Page -> ContentBlock, structured
and per-language -- see models.py). The admin UI (RichTextEditor,
inherited from fjstiWeb-main) was built against the old Yii2 site's flat
`content_uz`/`content_ru`/`content_en` columns; rewriting that UI into a
block-by-block editor was ruled out (too large a UI change, see the
decision this module implements) in favor of converting at the boundary,
reusing the exact same HTML<->blocks pipeline the legacy importers already
use and already have real test coverage for (html_extract.py + merge.py).

Round-trip, not lossless: a block rendered back to HTML and re-extracted
won't byte-for-byte match what a human originally typed (whitespace,
attribute order, ...) -- expected and harmless, same as any WYSIWYG editor.
"""
from __future__ import annotations

from django.conf import settings
from django.db import transaction

from apps.content.legacy_import.html_extract import ExtractionResult, extract
from apps.content.legacy_import.media import ImageDownloader
from apps.content.legacy_import.merge import LANGS
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document, Image


def blocks_to_html(page: Page | None, lang: str, request=None) -> str:
    """Renders one language's worth of a page's blocks back into editable
    HTML -- the inverse of write_blocks_from_html below, for populating the
    rich text editor when an existing news post / page is opened."""
    if page is None:
        return ""

    def absolute(url: str) -> str:
        return request.build_absolute_uri(url) if request is not None else url

    parts: list[str] = []
    for block in page.blocks.all():
        payload = block.data.get(lang) or block.data.get("uz") or {}
        if block.block_type == "heading":
            parts.append(f"<h2>{payload.get('text', '')}</h2>")
        elif block.block_type == "paragraph":
            parts.append(f"<p>{payload.get('text', '')}</p>")
        elif block.block_type == "list":
            items = "".join(f"<li>{item}</li>" for item in payload.get("items", []))
            parts.append(f"<ul>{items}</ul>")
        elif block.block_type == "image":
            image_id = payload.get("image_id")
            image = Image.objects.filter(pk=image_id).first() if image_id else None
            if image:
                parts.append(f'<p><img src="{absolute(image.file.url)}" alt="{payload.get("alt", "")}" /></p>')
        elif block.block_type == "document":
            document_id = payload.get("document_id")
            document = Document.objects.filter(pk=document_id).first() if document_id else None
            if document:
                parts.append(f'<p><a href="{absolute(document.file.url)}">{document.title or document.filename}</a></p>')
        # staff_card/video/gallery/table blocks aren't produced by this
        # editing path (extract() has no shape for them) -- a page that
        # already has one (imported from the old site) just keeps it;
        # re-saving that page through the admin drops it, which is a real,
        # known limitation of round-tripping rich structure through plain
        # HTML, not something silently mishandled here.
    return "\n".join(parts)


def _resolve_admin_image(src: str | None) -> Image | None:
    """An <img> inserted by the admin's own RichTextEditor/MediaPicker
    already points at a media file we host (see insertImage() in
    RichTextEditor.tsx) -- look it up directly instead of re-downloading it
    over HTTP the way the legacy importers do for genuinely external URLs."""
    if not src:
        return None
    media_url = settings.MEDIA_URL
    idx = src.find(media_url)
    if idx == -1:
        return ImageDownloader().get_or_download(src)
    relative = src[idx + len(media_url):]
    return Image.objects.filter(file=relative).first()


def _positional_pairs(results: dict[str, ExtractionResult]) -> list[tuple[str, dict[str, dict]]]:
    """Pairs each language's extracted blocks by plain index, not
    merge.py's fuzzy cross-language alignment: merge.py's algorithm was
    built for the old site's independently-authored, structurally-drifted
    uz/ru/en documents (see its own docstring), and its length-bucket
    symbol matching is tuned for that -- for admin-typed content, uz/ru/en
    are three tabs of ONE form, written in parallel by one person, so block
    N really is block N in every language; positional pairing is both
    simpler and more reliable here (confirmed: fuzzy matching spuriously
    discarded correct, structurally-identical Russian translations purely
    because a paragraph's length landed one bucket over from Uzbek's).
    A uz block with no counterpart in a shorter language falls back to
    uz's own text for that position, same end behavior as merge.py."""
    uz_blocks = results["uz"].blocks
    pairs = []
    for i, uz_block in enumerate(uz_blocks):
        payload_by_lang = {"uz": uz_block.payload}
        for lang in ("ru", "en"):
            lang_blocks = results[lang].blocks
            same_type = i < len(lang_blocks) and lang_blocks[i].block_type == uz_block.block_type
            payload_by_lang[lang] = lang_blocks[i].payload if same_type else uz_block.payload
        pairs.append((uz_block.block_type, payload_by_lang))
    return pairs


@transaction.atomic
def write_blocks_from_html(page: Page, html_by_lang: dict[str, str]) -> None:
    """Replaces `page`'s blocks with ones extracted from html_by_lang (one
    HTML string per uz/ru/en) -- reuses extract() (the legacy importers'
    own, tested HTML parser) but pairs the three languages' blocks
    positionally instead of through merge.py's fuzzy alignment; see
    _positional_pairs for why."""
    results = {lang: extract(html_by_lang.get(lang) or "") for lang in LANGS}
    pairs = _positional_pairs(results)

    ContentBlock.objects.filter(page=page).delete()

    order = 1
    for block_type, payload_by_lang in pairs:
        data = {}
        skip_block = False
        for lang in LANGS:
            payload = dict(payload_by_lang[lang])
            if block_type == "image":
                image = _resolve_admin_image(payload.pop("image_src", None))
                if image is None:
                    skip_block = True
                    break
                payload["image_id"] = image.id
                payload.setdefault("alt", "")
            data[lang] = payload
        if skip_block:
            continue
        content_block = ContentBlock(page=page, order=order, block_type=block_type, data=data)
        content_block.full_clean()
        content_block.save()
        order += 1
