"""A page says how it is laid out: `Page.layout` (plain pages are "default"). The frontend used to decide it
from the page's slug; the choice is data now, set in the admin and served by the public API."""
import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.content.models import Page

ADMIN = "/api/v1/admin"


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_user(username="layout-admin", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def test_a_new_page_is_laid_out_the_plain_way(db):
    assert Page.objects.create(slug="oddiy").layout == "default"


def test_the_public_api_serves_the_layout(db):
    Page.objects.create(slug="qaror", layout="regulatory")

    body = APIClient().get("/api/v1/pages/qaror/").json()

    assert body["layout"] == "regulatory"


def test_an_unknown_layout_is_refused(db):
    page = Page(slug="x", layout="no-such-layout")

    with pytest.raises(ValidationError):
        page.full_clean()


def test_every_layout_the_frontend_knows_is_allowed(db):
    names = {value for value, _ in Page.Layout.choices}

    assert names == {
        "default", "regulatory", "regulatory_index", "council", "council_decisions",
        "abstracts", "editorial", "archive", "faq",
    }


def test_the_admin_lists_and_changes_the_layout(admin_client):
    page = Page.objects.create(slug="arxiv-2024", title_uz="Arxiv")

    listed = admin_client.get(f"{ADMIN}/pages/{page.pk}").json()
    assert listed["layout"] == "default"

    saved = admin_client.put(
        f"{ADMIN}/pages/{page.pk}",
        {"title_uz": "Arxiv", "slug": "arxiv-2024", "layout": "archive", "content_uz": "", "content_ru": "", "content_en": ""},
        format="json",
    )

    assert saved.status_code == 200
    assert saved.json()["layout"] == "archive"
    page.refresh_from_db()
    assert page.layout == "archive"


def test_the_admin_cannot_save_an_unknown_layout(admin_client):
    page = Page.objects.create(slug="x2", title_uz="X")

    saved = admin_client.put(
        f"{ADMIN}/pages/{page.pk}",
        {"title_uz": "X", "slug": "x2", "layout": "nonsense", "content_uz": "", "content_ru": "", "content_en": ""},
        format="json",
    )

    assert saved.status_code == 400
    page.refresh_from_db()
    assert page.layout == "default"
