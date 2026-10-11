"""Django's stock admin is closed (404) unless DJANGO_ADMIN_ENABLED is on; the site's own admin API is unaffected."""
import pytest


@pytest.mark.parametrize("path", ["/django-admin", "/django-admin/", "/django-admin/login/", "/django-admin/auth/user/"])
def test_the_stock_admin_is_a_404_when_closed(client, db, settings, path):
    settings.DJANGO_ADMIN_ENABLED = False

    assert client.get(path).status_code == 404
    assert client.post(path, {"username": "x", "password": "y"}).status_code == 404


def test_the_stock_admin_opens_when_switched_on(client, db, settings):
    settings.DJANGO_ADMIN_ENABLED = True

    assert client.get("/django-admin/login/").status_code == 200


def test_the_production_default_is_closed():
    import os

    from config import settings as config_settings

    saved = os.environ.pop("DJANGO_ADMIN_ENABLED", None)
    try:
        assert config_settings.env_bool("DJANGO_ADMIN_ENABLED", False) is False
    finally:
        if saved is not None:
            os.environ["DJANGO_ADMIN_ENABLED"] = saved


def test_the_sites_own_admin_api_is_not_affected_by_the_gate(client, db, settings):
    settings.DJANGO_ADMIN_ENABLED = False

    assert client.get("/api/v1/admin/users").status_code == 401  # still its own login wall, not a 404
    assert client.get("/api/v1/settings").status_code == 200
