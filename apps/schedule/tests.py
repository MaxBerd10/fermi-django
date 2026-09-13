from django.core.files.uploadedfile import SimpleUploadedFile

import pytest
from rest_framework.test import APIClient

from apps.media_lib.models import Document
from apps.schedule.models import Course, ScheduleFile


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def course(db):
    upload = SimpleUploadedFile("jadval.pdf", b"%PDF-1.4 fake pdf bytes", content_type="application/pdf")
    document = Document.objects.create(file=upload, title="1-guruh jadvali")
    c = Course.objects.create(title_uz="Davolash ishi", title_ru="Лечебное дело", title_en="General Medicine", order=1)
    ScheduleFile.objects.create(
        course=c, document=document,
        title_uz="1-guruh", title_ru="1-я группа", title_en="Group 1", order=1,
    )
    return c


def test_schedule_list_returns_courses_with_nested_files(client, course):
    res = client.get("/api/v1/schedule/")
    assert res.status_code == 200
    assert res.data[0]["title"] == {"uz": "Davolash ishi", "ru": "Лечебное дело", "en": "General Medicine"}
    files = res.data[0]["schedules"]
    assert len(files) == 1
    assert files[0]["title"] == {"uz": "1-guruh", "ru": "1-я группа", "en": "Group 1"}
    assert files[0]["file"].endswith(".pdf")


def test_schedule_list_is_not_paginated(client, course):
    res = client.get("/api/v1/schedule/")
    assert isinstance(res.data, list)
