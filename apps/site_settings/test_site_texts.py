"""Admin-edited interface texts: a public JSON the frontend lays over its built-in wording, and a staff-only editor."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.site_settings.models import SiteText

ADMIN = "/api/v1/admin/site-texts"


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_user(username="texteditor", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def test_the_public_json_has_only_the_non_blank_texts_per_language(db, client):
    SiteText.objects.create(key="home.heroTitle", text_uz="Yangi sarlavha", text_ru="", text_en="  ")
    SiteText.objects.create(key="footer.rights", text_uz="", text_ru="Все права", text_en="All rights")

    data = client.get("/api/v1/site-texts").json()

    assert data == {
        "uz": {"home.heroTitle": "Yangi sarlavha"},
        "ru": {"footer.rights": "Все права"},
        "en": {"footer.rights": "All rights"},
    }


def test_no_overrides_means_three_empty_languages(db, client):
    assert client.get("/api/v1/site-texts").json() == {"uz": {}, "ru": {}, "en": {}}


def test_staff_can_save_and_the_site_shows_it(admin_client, client):
    res = admin_client.put(ADMIN, {"key": "home.heroTitle", "text_uz": " Salom ", "text_ru": "Привет", "text_en": ""}, format="json")

    assert res.status_code == 200 and res.json()["text_uz"] == "Salom"
    assert client.get("/api/v1/site-texts").json()["uz"] == {"home.heroTitle": "Salom"}
    assert [r["key"] for r in admin_client.get(ADMIN).json()] == ["home.heroTitle"]


def test_saving_the_same_key_again_updates_it(admin_client):
    admin_client.put(ADMIN, {"key": "a.b", "text_uz": "bir"}, format="json")
    admin_client.put(ADMIN, {"key": "a.b", "text_uz": "ikki"}, format="json")

    assert list(SiteText.objects.values_list("text_uz", flat=True)) == ["ikki"]


def test_blanking_every_language_restores_the_default(admin_client):
    admin_client.put(ADMIN, {"key": "a.b", "text_uz": "bir", "text_ru": "один"}, format="json")

    res = admin_client.put(ADMIN, {"key": "a.b", "text_uz": "", "text_ru": " ", "text_en": ""}, format="json")

    assert res.json() == {"key": "a.b", "deleted": True} and not SiteText.objects.exists()


@pytest.mark.parametrize("key", ["", "has space", "a/b", "x" * 121, "<script>"])
def test_a_bad_key_is_a_400(admin_client, key):
    assert admin_client.put(ADMIN, {"key": key, "text_uz": "x"}, format="json").status_code == 400


def test_an_overlong_text_is_a_400(admin_client):
    res = admin_client.put(ADMIN, {"key": "a.b", "text_uz": "x" * 3001}, format="json")

    assert res.status_code == 400 and not SiteText.objects.exists()


def test_the_editor_is_closed_to_visitors_and_non_staff(db):
    assert APIClient().get(ADMIN).status_code == 401
    assert APIClient().put(ADMIN, {"key": "a.b", "text_uz": "x"}, format="json").status_code == 401
    user = get_user_model().objects.create_user(username="plain", password="x", is_staff=False)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    assert client.put(ADMIN, {"key": "a.b", "text_uz": "x"}, format="json").status_code == 403
    assert not SiteText.objects.exists()
