import pytest

from apps.content.models import Page
from apps.departments.models import Department, StaffMember


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
