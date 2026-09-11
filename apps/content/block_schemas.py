"""
Contract for what each ContentBlock.data shape must look like, per block_type.

Every block's data is {"uz": <per-language payload>, "ru": <...>, "en": <...>} —
all three languages required, so a translator can never accidentally ship a page
that's half-translated and silently falls back to raw HTML soup (the old site's
actual failure mode). Validation runs in ContentBlock.clean(), so a malformed
block cannot be saved through the admin or the API — this is what "the mold
doesn't break when content changes" means concretely: enforced at the model
layer, not hoped for from a rich-text editor.
"""

from django.core.exceptions import ValidationError

SUPPORTED_LANGUAGES = ("uz", "ru", "en")


def _require_str(payload, field: str, lang: str):
    if not isinstance(payload.get(field), str) or not payload[field].strip():
        raise ValidationError(f"[{lang}] '{field}' must be a non-empty string")


def _validate_heading(payload: dict, lang: str) -> None:
    _require_str(payload, "text", lang)


def _validate_paragraph(payload: dict, lang: str) -> None:
    _require_str(payload, "text", lang)


def _validate_list(payload: dict, lang: str) -> None:
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValidationError(f"[{lang}] 'items' must be a non-empty list")
    for item in items:
        if not isinstance(item, str) or not item.strip():
            raise ValidationError(f"[{lang}] every list item must be a non-empty string")


def _validate_staff_card(payload: dict, lang: str) -> None:
    _require_str(payload, "full_name", lang)
    if "title" in payload and not isinstance(payload["title"], str):
        raise ValidationError(f"[{lang}] 'title' must be a string")


def _validate_image(payload: dict, lang: str) -> None:
    # image_id is language-independent in practice, but every language's payload
    # still carries it so the block shape stays uniform — alt text is what varies.
    if not isinstance(payload.get("image_id"), int):
        raise ValidationError(f"[{lang}] 'image_id' must reference an uploaded Image")
    if "alt" in payload and not isinstance(payload["alt"], str):
        raise ValidationError(f"[{lang}] 'alt' must be a string")


BLOCK_VALIDATORS = {
    "heading": _validate_heading,
    "paragraph": _validate_paragraph,
    "list": _validate_list,
    "staff_card": _validate_staff_card,
    "image": _validate_image,
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
