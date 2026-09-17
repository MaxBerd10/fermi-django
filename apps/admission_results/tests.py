"""Coverage for the public /qabul-natijalari endpoints -- mirrors
apps/schedule/tests.py's style, since ResultCategory/ResultFile
deliberately mirror Course/ScheduleFile (a document library grouped by
category, not a structured dataset -- see each model's own docstring).
"""
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models.deletion import ProtectedError

import pytest
from rest_framework.test import APIClient

from apps.media_lib.models import Document
from apps.admission_results.models import ResultCategory, ResultFile, ResultsPage


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def category(db):
    upload = SimpleUploadedFile("natija.pdf", b"%PDF-1.4 fake pdf bytes", content_type="application/pdf")
    document = Document.objects.create(file=upload, title="Natija")
    c = ResultCategory.objects.create(title_uz="Davolash ishi", title_ru="Лечебное дело", title_en="General Medicine", order=1)
    ResultFile.objects.create(
        category=c, document=document,
        title_uz="1-guruh", title_ru="1-я группа", title_en="Group 1", order=1,
    )
    return c


def test_admission_results_list_returns_categories_with_nested_files(client, category):
    res = client.get("/api/v1/admission-results/")
    assert res.status_code == 200
    assert res.data[0]["title"] == {"uz": "Davolash ishi", "ru": "Лечебное дело", "en": "General Medicine"}
    files = res.data[0]["files"]
    assert len(files) == 1
    assert files[0]["title"] == {"uz": "1-guruh", "ru": "1-я группа", "en": "Group 1"}
    assert files[0]["file"].endswith(".pdf")


def test_admission_results_list_is_not_paginated(client, category):
    res = client.get("/api/v1/admission-results/")
    assert isinstance(res.data, list)


def test_admission_results_is_read_only(client, category, django_user_model):
    # The view sets no permission_classes of its own, so it falls back to the
    # project default IsAuthenticatedOrReadOnly -- an anonymous POST is
    # rejected at the permission check (401) before routing ever reaches the
    # "no such handler" 405 this test means to prove, so authenticate first.
    user = django_user_model.objects.create_user(username="reader", password="x")
    client.force_authenticate(user=user)
    res = client.post("/api/v1/admission-results/", {"title_uz": "X", "title_ru": "X", "title_en": "X"}, format="json")
    assert res.status_code == 405


def test_admission_results_page_auto_creates_singleton_row(client, db):
    assert not ResultsPage.objects.exists()
    res = client.get("/api/v1/admission-results-page")
    assert res.status_code == 200
    assert res.data["heading"] == {"uz": "", "ru": "", "en": ""}


def test_admission_results_page_reshapes_fields_into_per_language_objects(client, db):
    ResultsPage.objects.create(
        heading_uz="Natijalar", heading_ru="Результаты", heading_en="Results",
        intro_uz="Kirish", intro_ru="Введение", intro_en="Intro",
        announcement_uz="E'lon", announcement_ru="Объявление", announcement_en="Announcement",
    )
    res = client.get("/api/v1/admission-results-page")
    assert res.data["heading"] == {"uz": "Natijalar", "ru": "Результаты", "en": "Results"}
    assert res.data["announcement"] == {"uz": "E'lon", "ru": "Объявление", "en": "Announcement"}


def test_deleting_a_category_cascades_to_its_files(db, category):
    file_id = category.files.get().id
    category.delete()
    assert not ResultFile.objects.filter(id=file_id).exists()


def test_deleting_a_referenced_document_is_protected(db, category):
    # ResultFile.document is on_delete=PROTECT -- a document still backing a
    # published result file must not be silently deletable.
    document = category.files.get().document
    with pytest.raises(ProtectedError):
        document.delete()
