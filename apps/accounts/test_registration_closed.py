"""Visitor sign-up is closed unless PUBLIC_REGISTRATION_ENABLED is switched on."""
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient

User = get_user_model()
PAYLOAD = {"username": "newperson", "email": "n@example.uz", "password": "A-long-enough-pass-123"}


def test_registration_answers_403_and_creates_no_account_when_closed(db, settings):
    settings.PUBLIC_REGISTRATION_ENABLED = False

    res = APIClient().post("/api/v1/auth/register", PAYLOAD, format="json")

    assert res.status_code == 403 and "yopiq" in res.json()["detail"]
    assert not User.objects.filter(username="newperson").exists()


def test_the_production_default_is_closed():
    import os

    from config import settings as config_settings

    saved = os.environ.pop("PUBLIC_REGISTRATION_ENABLED", None)
    try:
        assert config_settings.env_bool("PUBLIC_REGISTRATION_ENABLED", False) is False
    finally:
        if saved is not None:
            os.environ["PUBLIC_REGISTRATION_ENABLED"] = saved
