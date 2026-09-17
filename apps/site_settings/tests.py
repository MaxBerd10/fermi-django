"""Coverage for the public GET /api/v1/settings aggregate -- the single
endpoint every page's header/footer depends on (phone/address/logo/social
links/useful sites/counters). See SiteSettingsView's own docstring: this
replaced a frontend stub (EMPTY_SETTINGS) that always returned blanks
because no Django model backed any of it before.
"""
from django.core.files.uploadedfile import SimpleUploadedFile

import pytest
from rest_framework.test import APIClient

from apps.media_lib.models import Image
from apps.site_settings.models import SiteCounter, SiteLogo, SiteSetting, SocialNetwork, UsefulSite


@pytest.fixture
def client():
    return APIClient()


def test_settings_endpoint_works_on_a_fresh_database(client, db):
    # None of the three singleton rows exist yet -- get_solo() must
    # auto-create them rather than 404/500 on the very first request.
    res = client.get("/api/v1/settings")
    assert res.status_code == 200
    assert res.data["setting"]["address"] == {"uz": "", "ru": "", "en": ""}
    assert res.data["logo"]["img"] is None
    assert res.data["networks"] == []
    assert res.data["usefulSites"] == []
    assert res.data["counter"]["students"] == 0


def test_settings_endpoint_reshapes_address_into_a_per_language_object(client, db):
    SiteSetting.objects.create(
        phone="+998732430000", email="info@fjsti.uz", faks="",
        address_uz="Farg'ona sh., Yangi Turon 1", address_ru="г. Фергана", address_en="Fergana city",
    )
    res = client.get("/api/v1/settings")
    assert res.data["setting"]["address"] == {
        "uz": "Farg'ona sh., Yangi Turon 1", "ru": "г. Фергана", "en": "Fergana city",
    }


_PNG_1PX = (
    b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00"
    b"\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc\xfa\xcf\xc0\x00\x00\x03\x01\x01\x00\xd8\xdd\x8f"
    b"\xf5\x00\x00\x00\x00IEND\xaeB`\x82"
)


def test_settings_endpoint_returns_absolute_logo_url(client, db):
    upload = SimpleUploadedFile("logo.png", _PNG_1PX, content_type="image/png")
    image = Image.objects.create(file=upload)
    SiteLogo.objects.create(image=image, title_uz="FJSTI", title_ru="ФМИОЗ", title_en="FMIPH")
    res = client.get("/api/v1/settings")
    assert res.data["logo"]["img"].startswith("http")
    assert res.data["logo"]["img"].endswith(image.file.name)
    assert res.data["logo"]["title"] == {"uz": "FJSTI", "ru": "ФМИОЗ", "en": "FMIPH"}


def test_settings_endpoint_lists_networks_and_useful_sites_in_order(client, db):
    SocialNetwork.objects.create(title="Telegram", icon="ri-telegram-line", url="https://t.me/fjsti", order=2)
    SocialNetwork.objects.create(title="Instagram", icon="ri-instagram-line", url="https://instagram.com/fjsti", order=1)
    UsefulSite.objects.create(title_uz="Vazirlik", url="https://gov.uz", order=1)

    res = client.get("/api/v1/settings")
    assert [n["title"] for n in res.data["networks"]] == ["Instagram", "Telegram"]
    assert res.data["usefulSites"][0]["title"] == {"uz": "Vazirlik", "ru": "", "en": ""}
    assert res.data["usefulSites"][0]["url"] == "https://gov.uz"


def test_settings_endpoint_returns_counter_numbers(client, db):
    SiteCounter.objects.create(professor_teachers=120, students=3500, graduaters=900, book_fund=45000)
    res = client.get("/api/v1/settings")
    assert res.data["counter"] == {
        "professor_teachers": 120, "students": 3500, "graduaters": 900, "book_fund": 45000,
    }


def test_settings_endpoint_is_public(client, db):
    # No Authorization header at all -- SiteSettingsView sets no
    # permission_classes of its own, so it falls back to the project
    # default IsAuthenticatedOrReadOnly, which allows GET for anyone.
    res = client.get("/api/v1/settings")
    assert res.status_code == 200
