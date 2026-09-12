import pytest
from rest_framework.test import APIClient

from apps.content.models import Page
from apps.departments.models import Department
from apps.faculties.models import Faculty


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def faculty(db):
    page = Page.objects.create(slug="davolash-ishi-fakulteti")
    return Faculty.objects.create(
        slug="davolash-ishi-fakulteti",
        name_uz="Davolash ishi fakulteti",
        name_ru="Факультет лечебного дела",
        name_en="Faculty of General Medicine",
        page=page,
    )


def test_faculty_list_returns_localized_name(client, faculty):
    # Faculties are an unpaginated list (see FacultyViewSet.pagination_class)
    # — there are only ever a handful, and the frontend renders them as one
    # grid, not a feed a visitor pages through.
    res = client.get("/api/v1/faculties/")
    assert res.data[0]["name"]["en"] == "Faculty of General Medicine"


def test_faculty_detail_lists_its_departments(client, faculty):
    dept_page = Page.objects.create(slug="test-dept")
    Department.objects.create(
        slug="test-dept", name_uz="Test kafedra", name_ru="Тест", name_en="Test",
        page=dept_page, faculty=faculty,
    )

    res = client.get(f"/api/v1/faculties/{faculty.slug}/")
    assert res.status_code == 200
    assert len(res.data["departments"]) == 1
    assert res.data["departments"][0]["slug"] == "test-dept"
    assert res.data["departments"][0]["name"]["en"] == "Test"
