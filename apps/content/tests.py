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
