"""The admin start page numbers: unread messages per inbox and the latest news."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.forms.models import ContactSubmission

URL = "/api/v1/admin/dashboard"


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_user(username="dashboardeditor", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def test_dashboard_counts_only_unread_messages(admin_client):
    for read in (False, False, True):
        ContactSubmission.objects.create(name="A", subject="s", phone="1", email="a@b.c", message="m", is_read=read)
    data = admin_client.get(URL).json()
    assert data["unread"]["contacts"] == 2
    assert data["unread"]["acceptances"] == 0
    assert isinstance(data["news"], list)


def test_dashboard_is_staff_only(db, client):
    assert client.get(URL).status_code in (401, 403)


LOCATE = "/api/v1/admin/locate"


def test_locate_points_to_the_right_editor(admin_client):
    from apps.content.models import Page
    from apps.faculties.models import Faculty
    from apps.news.models import NewsCategory, NewsPost
    from django.utils import timezone

    plain = Page.objects.create(slug="oddiy-sahifa", title_uz="Oddiy")
    data = admin_client.get(LOCATE, {"slug": "oddiy-sahifa"}).json()
    assert data == {"found": True, "kind": "page", "title": "Oddiy", "edit": f"/admin/pages/{plain.pk}"}

    faculty_page = Page.objects.create(slug="davolash-fakulteti")
    faculty = Faculty.objects.create(slug="davolash-fakulteti-f", name_uz="Davolash", name_ru="D", name_en="D", page=faculty_page)
    data = admin_client.get(LOCATE, {"slug": "davolash-fakulteti"}).json()  # by the page's own slug
    assert data["kind"] == "faculty" and data["edit"] == f"/admin/faculty/{faculty.pk}"

    post_page = Page.objects.create(slug="yangilik-sahifasi")
    category = NewsCategory.objects.create(slug="tadbirlar", name_uz="T", name_ru="T", name_en="T")
    post = NewsPost.objects.create(
        slug="yangilik-1", title_uz="Y", title_ru="Y", title_en="Y", category=category, page=post_page, published_at=timezone.now()
    )
    data = admin_client.get(LOCATE, {"slug": "yangilik-sahifasi"}).json()
    assert data["kind"] == "news" and data["edit"] == f"/admin/news/{post.pk}"


def test_locate_unknown_slug_and_staff_only(admin_client, client):
    assert admin_client.get(LOCATE, {"slug": "yoq-sahifa"}).json() == {"found": False}
    assert admin_client.get(LOCATE).json() == {"found": False}
    assert client.get(LOCATE, {"slug": "x"}).status_code in (401, 403)
