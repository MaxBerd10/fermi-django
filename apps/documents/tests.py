import pytest
from rest_framework.test import APIClient

from apps.documents.models import Document, DocumentItem


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def document(db):
    doc = Document.objects.create(slug="ustav", title_uz="Ustav", title_ru="Устав", title_en="Charter")
    DocumentItem.objects.create(
        document=doc,
        slug="1-bob",
        title_uz="1-bob", title_ru="Глава 1", title_en="Chapter 1",
        content_uz="<p>Matn</p>", content_ru="<p>Текст</p>", content_en="<p>Text</p>",
        order=1,
    )
    DocumentItem.objects.create(
        document=doc,
        slug="2-bob",
        title_uz="2-bob", title_ru="Глава 2", title_en="Chapter 2",
        content_uz="<p>Ikkinchi</p>", content_ru="<p>Второй</p>", content_en="<p>Second</p>",
        order=2,
    )
    return doc


def test_document_detail_returns_localized_title_and_items_in_order(client, document):
    res = client.get("/api/v1/documents/ustav/")
    assert res.status_code == 200
    assert res.data["title"] == {"uz": "Ustav", "ru": "Устав", "en": "Charter"}
    assert [item["slug"] for item in res.data["items"]] == ["1-bob", "2-bob"]
    assert res.data["items"][0]["content"] == {
        "uz": "<p>Matn</p>", "ru": "<p>Текст</p>", "en": "<p>Text</p>",
    }


def test_document_detail_404_for_unknown_slug(client, db):
    res = client.get("/api/v1/documents/does-not-exist/")
    assert res.status_code == 404
