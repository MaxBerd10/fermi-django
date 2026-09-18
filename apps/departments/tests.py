import pytest
from rest_framework.test import APIClient

from apps.content.models import Page
from apps.departments.models import Department, StaffMember


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def department(db):
    page = Page.objects.create(slug="test-department-page")
    return Department.objects.create(slug="test-department", name_uz="X", name_ru="X", name_en="X", page=page)


def test_staff_needs_translation_when_bio_is_identical_across_languages(department):
    staff = StaffMember.objects.create(
        department=department,
        full_name_uz="Ism Familiya",
        full_name_ru="Ism Familiya",  # fallback copy, not a real transliteration
        full_name_en="Ism Familiya",
        title_uz="Dotsent",
        title_ru="Доцент",
        title_en="Associate Professor",
        bio_uz="Bio matni",
        bio_ru="Bio matni",  # fallback copy, not a real translation
        bio_en="Bio matni",
    )
    assert staff.needs_translation is True


def test_staff_does_not_need_translation_when_every_language_differs(department):
    staff = StaffMember.objects.create(
        department=department,
        full_name_uz="Ism Familiya",
        full_name_ru="Имя Фамилия",
        full_name_en="Name Surname",
        title_uz="Dotsent",
        title_ru="Доцент",
        title_en="Associate Professor",
        bio_uz="uz matn",
        bio_ru="ru текст",
        bio_en="en text",
    )
    assert staff.needs_translation is False


def test_kafedra_mudirlari_endpoint_returns_every_department_head(client, department):
    StaffMember.objects.create(
        department=department, full_name_uz="Head Person", title_uz="Kafedra mudiri", is_head=True,
    )
    StaffMember.objects.create(
        department=department, full_name_uz="Regular Staff", title_uz="Assistent", is_head=False,
    )

    res = client.get("/api/v1/leaders/kafedra-mudirlari/")
    assert res.status_code == 200
    names = [leader["full_name"]["uz"] for leader in res.data["leaders"]]
    assert names == ["Head Person"]


def test_leaders_endpoint_404s_for_unknown_category(client, db):
    res = client.get("/api/v1/leaders/not-a-real-category/")
    assert res.status_code == 404
