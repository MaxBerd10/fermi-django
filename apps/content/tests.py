"""
Tests for the block-validation contract — the core promise of the new content
model is that a malformed or partially-translated block can never be saved.
These tests exist to prove that promise, not just describe it in a comment.
"""

import pytest
from django.core.exceptions import ValidationError

from apps.content.models import ContentBlock, Page


@pytest.fixture
def page(db):
    return Page.objects.create(slug="test-page")


def valid_heading_data():
    return {
        "uz": {"text": "Sarlavha"},
        "ru": {"text": "Заголовок"},
        "en": {"text": "Heading"},
    }


def test_valid_heading_block_passes_validation(page):
    block = ContentBlock(page=page, order=1, block_type="heading", data=valid_heading_data())
    block.full_clean()  # must not raise


def test_block_missing_a_language_is_rejected(page):
    data = valid_heading_data()
    del data["en"]
    block = ContentBlock(page=page, order=1, block_type="heading", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_block_with_unsupported_language_is_rejected(page):
    data = valid_heading_data()
    data["fr"] = {"text": "Titre"}
    block = ContentBlock(page=page, order=1, block_type="heading", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_block_with_empty_text_is_rejected(page):
    data = valid_heading_data()
    data["ru"]["text"] = ""
    block = ContentBlock(page=page, order=1, block_type="heading", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_unknown_block_type_is_rejected(page):
    block = ContentBlock(page=page, order=1, block_type="carousel", data=valid_heading_data())
    with pytest.raises(ValidationError):
        block.full_clean()


def test_list_block_requires_non_empty_items(page):
    data = {
        "uz": {"items": ["Birinchi", "Ikkinchi"]},
        "ru": {"items": ["Первый", "Второй"]},
        "en": {"items": []},
    }
    block = ContentBlock(page=page, order=1, block_type="list", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_two_blocks_on_the_same_page_cannot_share_an_order(page):
    ContentBlock.objects.create(page=page, order=1, block_type="heading", data=valid_heading_data())
    with pytest.raises(Exception):
        ContentBlock.objects.create(page=page, order=1, block_type="heading", data=valid_heading_data())


def valid_video_data(video_id=1):
    return {
        "uz": {"video_id": video_id},
        "ru": {"video_id": video_id},
        "en": {"video_id": video_id},
    }


def test_valid_video_block_passes_validation(page):
    block = ContentBlock(page=page, order=1, block_type="video", data=valid_video_data())
    block.full_clean()  # must not raise


def test_video_block_missing_video_id_is_rejected(page):
    data = valid_video_data()
    del data["en"]["video_id"]
    block = ContentBlock(page=page, order=1, block_type="video", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_video_block_rejects_html_in_caption(page):
    data = valid_video_data()
    data["uz"]["caption"] = '<div style="position: absolute; color: transparent;">S</div>'
    block = ContentBlock(page=page, order=1, block_type="video", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def valid_document_data(document_id=1):
    return {
        "uz": {"document_id": document_id},
        "ru": {"document_id": document_id},
        "en": {"document_id": document_id},
    }


def test_valid_document_block_passes_validation(page):
    block = ContentBlock(page=page, order=1, block_type="document", data=valid_document_data())
    block.full_clean()  # must not raise


def test_document_block_missing_document_id_is_rejected(page):
    data = valid_document_data()
    del data["en"]["document_id"]
    block = ContentBlock(page=page, order=1, block_type="document", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_document_block_rejects_html_in_caption(page):
    data = valid_document_data()
    data["uz"]["caption"] = '<div style="position: absolute; color: transparent;">S</div>'
    block = ContentBlock(page=page, order=1, block_type="document", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def valid_gallery_data(image_ids=(1, 2)):
    items = [{"image_id": i} for i in image_ids]
    return {"uz": {"items": items}, "ru": {"items": items}, "en": {"items": items}}


def test_valid_gallery_block_passes_validation(page):
    block = ContentBlock(page=page, order=1, block_type="gallery", data=valid_gallery_data())
    block.full_clean()  # must not raise


def test_gallery_block_requires_non_empty_items(page):
    data = valid_gallery_data()
    data["en"]["items"] = []
    block = ContentBlock(page=page, order=1, block_type="gallery", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_gallery_item_missing_image_id_is_rejected(page):
    data = valid_gallery_data()
    del data["uz"]["items"][0]["image_id"]
    block = ContentBlock(page=page, order=1, block_type="gallery", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_gallery_item_rejects_html_in_alt(page):
    data = valid_gallery_data()
    data["uz"]["items"][0]["alt"] = '<div style="position: absolute; color: transparent;">S</div>'
    block = ContentBlock(page=page, order=1, block_type="gallery", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def valid_table_data():
    payload = {"headers": ["Fan", "Soat"], "rows": [["Anatomiya", "36"], ["Fiziologiya", "24"]]}
    return {"uz": payload, "ru": payload, "en": payload}


def test_valid_table_block_passes_validation(page):
    block = ContentBlock(page=page, order=1, block_type="table", data=valid_table_data())
    block.full_clean()  # must not raise


def test_table_block_requires_non_empty_headers(page):
    data = valid_table_data()
    data["en"]["headers"] = []
    block = ContentBlock(page=page, order=1, block_type="table", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_table_row_must_match_header_count(page):
    data = valid_table_data()
    data["uz"]["rows"][0] = ["Anatomiya", "36", "Prof. X"]  # 3 cells, 2 headers
    block = ContentBlock(page=page, order=1, block_type="table", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_table_rejects_html_in_a_cell(page):
    data = valid_table_data()
    data["uz"]["rows"][0][0] = '<div style="position: absolute; color: transparent;">S</div>'
    block = ContentBlock(page=page, order=1, block_type="table", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


# Regression tests: the exact two content-pollution patterns found on the old
# Yii2 site today (ChatGPT web-UI markup, a PDF viewer's per-character text
# layer) must never be savable here — see block_schemas.py's module docstring.


def test_rejects_text_pasted_straight_from_chatgpts_web_ui(page):
    data = valid_heading_data()
    data["uz"]["text"] = (
        '<div class="flex flex-col text-sm pb-25"><div class="z-0 flex '
        'min-h-[46px] justify-start">Kafedraning o\'quv-uslubiy faoliyati</div></div>'
    )
    block = ContentBlock(page=page, order=1, block_type="heading", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_rejects_text_pasted_from_a_pdf_viewers_text_layer(page):
    data = valid_heading_data()
    data["uz"]["text"] = (
        '<div style="padding: 0px; margin: 0px; color: transparent; '
        'position: absolute; white-space: pre;">S</div>'
    )
    block = ContentBlock(page=page, order=1, block_type="heading", data=data)
    with pytest.raises(ValidationError):
        block.full_clean()


def test_plain_text_containing_a_bare_less_than_sign_is_still_accepted(page):
    # The HTML check looks for <letter/!  specifically, so ordinary text using
    # "<" (e.g. a comparison) isn't caught in the crossfire.
    data = valid_heading_data()
    data["uz"]["text"] = "Talabalar soni 100 dan kam"
    block = ContentBlock(page=page, order=1, block_type="heading", data=data)
    block.full_clean()  # must not raise
