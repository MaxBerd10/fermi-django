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

The bridge is *structure-preserving*, which is the whole point of the two
mechanisms below -- before them, merely opening a page in the admin and
pressing "Saqlash" (touching nothing) silently deleted its tables and turned
its embedded PDFs into bare links, because plain HTML has no way to say "this
is a table block" or "this paragraph is bold":

1. Blocks the editor cannot express at all (table, document, gallery, video,
   staff_card, raw_html) travel as opaque *placeholders*:
   `<div data-preserved-block="<id>" ...>Jadval</div>`. The editor treats one
   as an atomic, movable, deletable chip (see PreservedBlock in
   RichTextEditor.tsx). On save a placeholder that is still present keeps its
   block untouched (and wherever it was dragged to); one that was deleted from
   the editor deletes the block -- that is the editor's intent, not an accident.

2. Blocks the editor *can* express but with hidden attributes the HTML cannot
   carry (paragraph `bold`, heading `level`, image `style`) are reconciled
   against the page's existing blocks on save: a block whose visible text is
   unchanged keeps its row and every attribute; an edited block carries its
   hidden attributes over from the block it replaced.

Round trip, not lossless in the byte sense: whitespace and attribute order may
differ from what a human originally typed -- expected and harmless, same as any
WYSIWYG editor. test_admin_content.py pins the property that matters: saving
an untouched page changes none of its blocks.
"""
from __future__ import annotations

import difflib
import html as html_lib
import re
from types import SimpleNamespace

from django.conf import settings
from django.db import transaction

from apps.content.legacy_import.html_extract import ExtractionResult, extract
from apps.content.legacy_import.media import ImageDownloader
from apps.content.legacy_import.merge import LANGS
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image

# Block types the rich-text editor has no HTML for.
PRESERVED_TYPES = frozenset({"table", "document", "gallery", "video", "staff_card", "raw_html"})

# Per type: the payload fields a human can see and edit in the editor. Anything
# else in a block's payload (bold, level, style, ...) is a hidden attribute.
_VISIBLE_FIELDS = {
    "heading": ("text",),
    "paragraph": ("text",),
    "list": ("items",),
    # alt is deliberately not "visible": extract() never reads an <img>'s alt, so
    # it can only ever be carried over from the existing block, not edited here.
    "image": ("image_id",),
}

# A placeholder, matched loosely on purpose: the editor's translate button sends the uz HTML through
# Google Translate for ru/en, which may re-quote or re-order attributes -- every variant still has to
# be recognised (and stripped from ru/en) or its label would be read as a stray paragraph.
_PRESERVED_RE = re.compile(
    r"""<div\b[^>]*?(?:data-preserved-block|class\s*=\s*["']preserved-block)[^>]*>.*?</div>""", re.S | re.I
)
_PRESERVED_ID_RE = re.compile(r"""data-preserved-block\s*=\s*["']?(\d+)""", re.I)


def _esc(text) -> str:
    return html_lib.escape(str(text or ""), quote=False)


def _attr(text) -> str:
    return html_lib.escape(str(text or ""), quote=True)


def _placeholder_label(block: ContentBlock, payload: dict) -> str:
    kind = block.block_type
    if kind == "table":
        return f"Jadval ({len(payload.get('rows') or [])} qator) — tahrirlanmaydi"
    if kind == "document":
        title = payload.get("caption") or ""
        return f"Hujjat (PDF/fayl) {title} — tahrirlanmaydi".replace("  ", " ")
    if kind == "gallery":
        return f"Rasmlar galereyasi ({len(payload.get('items') or [])} ta) — tahrirlanmaydi"
    if kind == "video":
        return "Video — tahrirlanmaydi"
    if kind == "staff_card":
        return f"Xodim: {payload.get('full_name') or ''} — tahrirlanmaydi".replace("  ", " ")
    return "Maxsus (eski sayt) blok — tahrirlanmaydi"


def blocks_to_html(page: Page | None, lang: str, request=None, skip_types=()) -> str:
    """Renders one language's worth of a page's blocks back into editable
    HTML -- the inverse of write_blocks_from_html below, for populating the
    rich text editor when an existing news post / page is opened.

    `skip_types` omits block types a caller edits through its own control
    instead (a news post's photo gallery has a dedicated GalleryPicker)."""
    if page is None:
        return ""

    def absolute(url: str) -> str:
        return request.build_absolute_uri(url) if request is not None else url

    parts: list[str] = []
    for block in page.blocks.all():
        payload = block.data.get(lang) or block.data.get("uz") or {}
        kind = block.block_type
        if kind in skip_types:
            continue
        if kind == "heading":
            tag = "h3" if payload.get("level") == 3 else "h2"
            parts.append(f"<{tag}>{_esc(payload.get('text'))}</{tag}>")
        elif kind == "paragraph":
            # Never <strong> for a bold paragraph: extract() reads a fully-bold <p>
            # as a heading, so that would silently change the block's type. Its
            # `bold` flag is carried over by the reconciliation in
            # write_blocks_from_html instead.
            parts.append(f"<p>{_esc(payload.get('text'))}</p>")
        elif kind == "list":
            items = "".join(f"<li>{_esc(item)}</li>" for item in payload.get("items", []))
            parts.append(f"<ul>{items}</ul>")
        elif kind == "image":
            image_id = payload.get("image_id")
            image = Image.objects.filter(pk=image_id).first() if image_id else None
            if image:
                parts.append(f'<p><img src="{_attr(absolute(image.file.url))}" alt="{_attr(payload.get("alt", ""))}" /></p>')
        elif kind in PRESERVED_TYPES:
            parts.append(
                f'<div data-preserved-block="{block.id}" data-block-type="{kind}" class="preserved-block">'
                f"{_esc(_placeholder_label(block, payload))}</div>"
            )
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


def _split_preserved(uz_html: str) -> tuple[list[str], list[int]]:
    """Cuts the uz HTML at its preserved-block placeholders: returns the
    HTML segments between them and the placeholder ids in document order
    (a pasted/duplicated chip repeating an id counts once)."""
    seen: set[int] = set()

    def drop_repeats(match):
        found = _PRESERVED_ID_RE.search(match.group(0))
        if not found or int(found.group(1)) in seen:
            return ""
        seen.add(int(found.group(1)))
        return match.group(0)

    uz_html = _PRESERVED_RE.sub(drop_repeats, uz_html)
    segments, ids, last = [], [], 0
    for match in _PRESERVED_RE.finditer(uz_html):
        segments.append(uz_html[last:match.start()])
        ids.append(int(_PRESERVED_ID_RE.search(match.group(0)).group(1)))
        last = match.end()
    segments.append(uz_html[last:])
    return segments, ids


def _visible(block_type: str, payload: dict) -> tuple:
    return tuple((field, repr(payload.get(field))) for field in _VISIBLE_FIELDS.get(block_type, ()))


def _block_key(block_type: str, data: dict) -> tuple:
    return (block_type, tuple(_visible(block_type, data.get(lang) or {}) for lang in LANGS))


def _carry_hidden_attributes(block_type: str, old_data: dict, new_data: dict) -> dict:
    """A block that was edited in place keeps its formatting: copies every
    non-visible payload field (bold, level, style, ...) from the block it
    replaced onto the freshly extracted one."""
    visible = _VISIBLE_FIELDS.get(block_type, ())
    merged = {}
    for lang in LANGS:
        payload = dict(new_data[lang])
        for key, value in (old_data.get(lang) or {}).items():
            if key not in visible and payload.get(key) in (None, ""):
                payload[key] = value
        merged[lang] = payload
    return merged


@transaction.atomic
def write_blocks_from_html(page: Page, html_by_lang: dict[str, str]) -> None:
    """Replaces `page`'s blocks with ones extracted from html_by_lang (one
    HTML string per uz/ru/en) -- reuses extract() (the legacy importers'
    own, tested HTML parser) but pairs the three languages' blocks
    positionally instead of through merge.py's fuzzy alignment; see
    _positional_pairs for why.

    Existing blocks survive an edit wherever the editor could not have
    changed them -- see the module docstring: preserved-block placeholders
    keep their block (and move with the chip), and unchanged or in-place
    edited text blocks keep their row and hidden attributes."""
    uz_segments, placeholder_ids = _split_preserved(html_by_lang.get("uz") or "")

    existing = list(ContentBlock.objects.filter(page=page).order_by("order"))
    by_id = {block.id: block for block in existing}
    kept_ids = [i for i in placeholder_ids if i in by_id and by_id[i].block_type in PRESERVED_TYPES]

    # uz is the structural authority (its placeholders say what stays and where);
    # ru/en are just their text, so their placeholders are stripped before parsing.
    uz_blocks, positions = [], []
    for index, segment in enumerate(uz_segments):
        uz_blocks.extend(extract(segment).blocks)
        if index < len(placeholder_ids):
            positions.append((len(uz_blocks), placeholder_ids[index]))
    results = {"uz": SimpleNamespace(blocks=uz_blocks)}
    for lang in ("ru", "en"):
        results[lang] = extract(_PRESERVED_RE.sub("", html_by_lang.get(lang) or ""))
    pairs = _positional_pairs(results)

    # Build the final sequence of slots: new/edited blocks and kept placeholders.
    new_slots: list[tuple[str, dict]] = []   # (block_type, data) for non-preserved blocks, in order
    slot_layout: list[tuple] = []            # ("new", index into new_slots) | ("keep", block_id)
    pending = [(pos, block_id) for pos, block_id in positions if block_id in kept_ids]
    for index, (block_type, payload_by_lang) in enumerate(pairs):
        while pending and pending[0][0] <= index:
            slot_layout.append(("keep", pending.pop(0)[1]))
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
        new_slots.append((block_type, data))
        slot_layout.append(("new", len(new_slots) - 1))
    for _, block_id in pending:
        slot_layout.append(("keep", block_id))

    # Reconcile new text blocks against the page's existing text blocks.
    olds = [b for b in existing if b.block_type not in PRESERVED_TYPES]
    matcher = difflib.SequenceMatcher(
        a=[_block_key(b.block_type, b.data) for b in olds],
        b=[_block_key(t, d) for t, d in new_slots],
        autojunk=False,
    )
    reuse: dict[int, ContentBlock] = {}       # new_slots index -> existing block row to keep as-is
    for tag, a0, a1, b0, b1 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(a1 - a0):
                reuse[b0 + offset] = olds[a0 + offset]
        elif tag == "replace" and (a1 - a0) == (b1 - b0):
            for offset in range(a1 - a0):
                old, (block_type, data) = olds[a0 + offset], new_slots[b0 + offset]
                if old.block_type == block_type:
                    new_slots[b0 + offset] = (block_type, _carry_hidden_attributes(block_type, old.data, data))

    surviving = {b.id for b in reuse.values()} | set(kept_ids)
    ContentBlock.objects.filter(page=page).exclude(id__in=surviving).delete()
    # (page, order) is unique: park survivors out of the way before renumbering.
    for block in ContentBlock.objects.filter(page=page):
        block.order += 1_000_000
        block.save(update_fields=["order"])

    order = 1
    for kind, ref in slot_layout:
        if kind == "keep":
            block = by_id[ref]
            block.order = order
            block.save(update_fields=["order"])
        elif ref in reuse:
            block = reuse[ref]
            block.order = order
            block.save(update_fields=["order"])
        else:
            block_type, data = new_slots[ref]
            block = ContentBlock(page=page, order=order, block_type=block_type, data=data)
            block.full_clean()
            block.save()
        order += 1
