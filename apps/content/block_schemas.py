"""
Contract for what each ContentBlock.data shape must look like, per block_type.

Every block's data is {"uz": <per-language payload>, "ru": <...>, "en": <...>} —
all three languages required, so a translator can never accidentally ship a page
that's half-translated and silently falls back to raw HTML soup (the old site's
actual failure mode). Validation runs in ContentBlock.clean(), so a malformed
block cannot be saved through the admin or the API — this is what "the mold
doesn't break when content changes" means concretely: enforced at the model
layer, not hoped for from a rich-text editor.

Every text field here is *plain text by design* — blocks never need raw HTML,
unlike the old site's CMS. That's what makes the HTML_TAG_RE check below able to
reject ANY tag outright: it's not guessing which tags are "safe", it's enforcing
that this content never needed tags in the first place. That one rule is what
closes off, in one stroke, both real-world failure modes found on the old site
today — pasting straight from ChatGPT's web UI (its own `<div class="...">`
wrapper markup riding along) and pasting from a PDF viewer's text-selection
layer (`<div style="position:absolute...">` per character) — neither can
possibly pass a "no tags at all" check.
"""

import re

from django.core.exceptions import ValidationError

SUPPORTED_LANGUAGES = ("uz", "ru", "en")

HTML_TAG_RE = re.compile(r"<[a-zA-Z!/]")


def _require_plain_text(payload, field: str, lang: str):
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"[{lang}] '{field}' must be a non-empty string")
    if HTML_TAG_RE.search(value):
        raise ValidationError(
            f"[{lang}] '{field}' looks like it contains HTML/markup — this field is "
            "plain text only. If this was pasted from a website or PDF viewer, paste "
            "as plain text instead (many editors support Cmd/Ctrl+Shift+V)."
        )


def _validate_heading(payload: dict, lang: str) -> None:
    _require_plain_text(payload, "text", lang)


def _validate_paragraph(payload: dict, lang: str) -> None:
    _require_plain_text(payload, "text", lang)


def _validate_list(payload: dict, lang: str) -> None:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValidationError(f"[{lang}] 'items' must be a non-empty list")
    for item in items:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"[{lang}] every list item must be a non-empty string")
        if HTML_TAG_RE.search(item):
            raise ValidationError(f"[{lang}] list items are plain text only — remove any markup")


def _validate_staff_card(payload: dict, lang: str) -> None:
    _require_plain_text(payload, "full_name", lang)
    if "title" in payload:
        if not isinstance(payload["title"], str):
            raise ValidationError(f"[{lang}] 'title' must be a string")
        if HTML_TAG_RE.search(payload["title"]):
            raise ValidationError(f"[{lang}] 'title' is plain text only — remove any markup")


def _validate_image(payload: dict, lang: str) -> None:
    # image_id is language-independent in practice, but every language's payload
    # still carries it so the block shape stays uniform — alt text is what varies.
    if not isinstance(payload.get("image_id"), int):
        raise ValidationError(f"[{lang}] 'image_id' must reference an uploaded Image")
    if "alt" in payload:
        if not isinstance(payload["alt"], str):
            raise ValidationError(f"[{lang}] 'alt' must be a string")
        if HTML_TAG_RE.search(payload["alt"]):
            raise ValidationError(f"[{lang}] 'alt' is plain text only — remove any markup")


def _validate_video(payload: dict, lang: str) -> None:
    # video_id is language-independent in practice, but every language's payload
    # still carries it so the block shape stays uniform — caption is what varies.
    if not isinstance(payload.get("video_id"), int):
        raise ValidationError(f"[{lang}] 'video_id' must reference an uploaded Video")
    if "caption" in payload:
        if not isinstance(payload["caption"], str):
            raise ValidationError(f"[{lang}] 'caption' must be a string")
        if HTML_TAG_RE.search(payload["caption"]):
            raise ValidationError(f"[{lang}] 'caption' is plain text only — remove any markup")


def _validate_document(payload: dict, lang: str) -> None:
    # document_id is language-independent in practice, but every language's
    # payload still carries it so the block shape stays uniform — caption is
    # what varies.
    if not isinstance(payload.get("document_id"), int):
        raise ValidationError(f"[{lang}] 'document_id' must reference an uploaded Document")
    if "caption" in payload:
        if not isinstance(payload["caption"], str):
            raise ValidationError(f"[{lang}] 'caption' must be a string")
        if HTML_TAG_RE.search(payload["caption"]):
            raise ValidationError(f"[{lang}] 'caption' is plain text only — remove any markup")


def _validate_gallery(payload: dict, lang: str) -> None:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValidationError(f"[{lang}] 'items' must be a non-empty list")
    for item in items:
        if not isinstance(item, dict):
            raise ValidationError(f"[{lang}] every gallery item must be an object")
        if not isinstance(item.get("image_id"), int):
            raise ValidationError(f"[{lang}] every gallery item's 'image_id' must reference an uploaded Image")
        if "alt" in item:
            if not isinstance(item["alt"], str):
                raise ValidationError(f"[{lang}] gallery item 'alt' must be a string")
            if HTML_TAG_RE.search(item["alt"]):
                raise ValidationError(f"[{lang}] gallery item 'alt' is plain text only — remove any markup")


def _validate_table(payload: dict, lang: str) -> None:
    headers = payload.get("headers")
    if not isinstance(headers, list) or not headers:
        raise ValidationError(f"[{lang}] 'headers' must be a non-empty list")
    for header in headers:
        if not isinstance(header, str) or not header.strip():
            raise ValidationError(f"[{lang}] every header must be a non-empty string")
        if HTML_TAG_RE.search(header):
            raise ValidationError(f"[{lang}] headers are plain text only — remove any markup")

    rows = payload.get("rows")
    if not isinstance(rows, list) or not rows:
        raise ValidationError(f"[{lang}] 'rows' must be a non-empty list")
    for row in rows:
        if not isinstance(row, list) or len(row) != len(headers):
            raise ValidationError(f"[{lang}] every row must have exactly {len(headers)} cells (one per header)")
        for cell in row:
            if not isinstance(cell, str):
                raise ValidationError(f"[{lang}] every cell must be a string")
            if HTML_TAG_RE.search(cell):
                raise ValidationError(f"[{lang}] cells are plain text only — remove any markup")


def _validate_raw_html(payload: dict, lang: str) -> None:
    """Legacy HTML is only rendered through the client's sanitizer."""
    value = payload.get("html")
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"[{lang}] 'html' must be a non-empty string")


BLOCK_VALIDATORS = {
    "heading": _validate_heading,
    "paragraph": _validate_paragraph,
    "list": _validate_list,
    "staff_card": _validate_staff_card,
    "image": _validate_image,
    "video": _validate_video,
    "document": _validate_document,
    "gallery": _validate_gallery,
    "table": _validate_table,
    "raw_html": _validate_raw_html,
}


def validate_block_data(block_type: str, data) -> None:
    if block_type not in BLOCK_VALIDATORS:
        raise ValidationError(f"Unknown block_type '{block_type}'")
    if not isinstance(data, dict):
        raise ValidationError("data must be an object keyed by language")
    missing = [lang for lang in SUPPORTED_LANGUAGES if lang not in data]
    if missing:
        raise ValidationError(f"data is missing languages: {missing}")
    extra = [lang for lang in data if lang not in SUPPORTED_LANGUAGES]
    if extra:
        raise ValidationError(f"data has unsupported languages: {extra}")
    validator = BLOCK_VALIDATORS[block_type]
    for lang in SUPPORTED_LANGUAGES:
        payload = data[lang]
        if not isinstance(payload, dict):
            raise ValidationError(f"[{lang}] payload must be an object")
        validator(payload, lang)
