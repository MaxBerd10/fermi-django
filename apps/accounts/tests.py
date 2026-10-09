"""
End-to-end coverage of the register -> verify -> login contract — the exact
same rule closed on the old Yii2 site today: no tokens until the email link
is clicked, and an unverified account cannot log in at all.
"""

import re

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from rest_framework.test import APIClient

User = get_user_model()

VERIFY_LINK_RE = re.compile(r"/(?:email-tasdiqlash|parolni-tiklash)/([^/]+)/([^\s/]+)")


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def registered_user(client, db):
    client.post(
        "/api/v1/auth/register",
        {"username": "alice", "email": "alice@example.com", "password": "StrongPass123!"},
        format="json",
    )
    return User.objects.get(username="alice")


def extract_verify_link():
    body = mail.outbox[-1].body
    match = VERIFY_LINK_RE.search(body)
    assert match, f"no verification link found in email body: {body!r}"
    return match.group(1), match.group(2)


def test_register_does_not_return_tokens(client, db):
    res = client.post(
        "/api/v1/auth/register",
        {"username": "bob", "email": "bob@example.com", "password": "StrongPass123!"},
        format="json",
    )
    assert res.status_code == 201
    assert "accessToken" not in res.data
    assert res.data == {"verificationRequired": True}


def test_register_creates_an_inactive_account(registered_user):
    assert registered_user.is_active is False


def test_unverified_account_cannot_log_in(client, registered_user):
    res = client.post(
        "/api/v1/auth/login", {"username": "alice", "password": "StrongPass123!"}, format="json"
    )
    assert res.status_code == 401


def test_verify_email_activates_account_and_issues_tokens(client, registered_user):
    uid, token = extract_verify_link()
    res = client.post("/api/v1/auth/verify-email", {"uid": uid, "token": token}, format="json")
    assert res.status_code == 200
    assert "accessToken" in res.data and "refreshToken" in res.data

    registered_user.refresh_from_db()
    assert registered_user.is_active is True


def test_verified_account_can_then_log_in(client, registered_user):
    uid, token = extract_verify_link()
    client.post("/api/v1/auth/verify-email", {"uid": uid, "token": token}, format="json")

    res = client.post(
        "/api/v1/auth/login", {"username": "alice", "password": "StrongPass123!"}, format="json"
    )
    assert res.status_code == 200
    assert "accessToken" in res.data


def test_me_requires_a_valid_token(client, registered_user):
    assert client.get("/api/v1/auth/me").status_code == 401

    uid, token = extract_verify_link()
    tokens = client.post("/api/v1/auth/verify-email", {"uid": uid, "token": token}, format="json").data
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['accessToken']}")
    res = client.get("/api/v1/auth/me")
    assert res.status_code == 200
    assert res.data["username"] == "alice"


def test_logout_blacklists_the_refresh_token(client, registered_user):
    uid, token = extract_verify_link()
    tokens = client.post("/api/v1/auth/verify-email", {"uid": uid, "token": token}, format="json").data

    client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['accessToken']}")
    logout_res = client.post("/api/v1/auth/logout", {"refreshToken": tokens["refreshToken"]}, format="json")
    assert logout_res.status_code == 204

    client.credentials()
    refresh_res = client.post("/api/v1/auth/refresh", {"refreshToken": tokens["refreshToken"]}, format="json")
    assert refresh_res.status_code == 401


def test_a_stale_or_forged_verification_token_is_rejected(client, registered_user):
    res = client.post(
        "/api/v1/auth/verify-email", {"uid": "Mg", "token": "not-a-real-token"}, format="json"
    )
    assert res.status_code == 400
    registered_user.refresh_from_db()
    assert registered_user.is_active is False


def _verify(client, registered_user):
    uid, token = extract_verify_link()
    client.post("/api/v1/auth/verify-email", {"uid": uid, "token": token}, format="json")
    registered_user.refresh_from_db()


def test_password_reset_request_never_reveals_whether_the_email_exists(client, db):
    known = client.post(
        "/api/v1/auth/password-reset-request", {"email": "nobody-here@example.com"}, format="json"
    )
    User.objects.create_user(username="dave", email="dave@example.com", password="StrongPass123!", is_active=True)
    unknown = client.post(
        "/api/v1/auth/password-reset-request", {"email": "dave@example.com"}, format="json"
    )
    assert known.status_code == unknown.status_code == 200
    assert known.data == unknown.data == {"sent": True}


def test_password_reset_confirm_changes_the_password_and_logs_in(client, registered_user):
    _verify(client, registered_user)
    mail.outbox.clear()

    client.post("/api/v1/auth/password-reset-request", {"email": "alice@example.com"}, format="json")
    uid, token = extract_verify_link()

    res = client.post(
        "/api/v1/auth/password-reset",
        {"uid": uid, "token": token, "password": "BrandNewPass456!"},
        format="json",
    )
    assert res.status_code == 200
    assert "accessToken" in res.data

    old_login = client.post(
        "/api/v1/auth/login", {"username": "alice", "password": "StrongPass123!"}, format="json"
    )
    assert old_login.status_code == 401

    new_login = client.post(
        "/api/v1/auth/login", {"username": "alice", "password": "BrandNewPass456!"}, format="json"
    )
    assert new_login.status_code == 200


def test_password_reset_confirm_rejects_a_reused_token(client, registered_user):
    _verify(client, registered_user)
    mail.outbox.clear()

    client.post("/api/v1/auth/password-reset-request", {"email": "alice@example.com"}, format="json")
    uid, token = extract_verify_link()

    first = client.post(
        "/api/v1/auth/password-reset",
        {"uid": uid, "token": token, "password": "BrandNewPass456!"},
        format="json",
    )
    assert first.status_code == 200

    second = client.post(
        "/api/v1/auth/password-reset",
        {"uid": uid, "token": token, "password": "AnotherPass789!"},
        format="json",
    )
    assert second.status_code == 400


def test_password_reset_confirm_enforces_password_validation(client, registered_user):
    _verify(client, registered_user)
    mail.outbox.clear()

    client.post("/api/v1/auth/password-reset-request", {"email": "alice@example.com"}, format="json")
    uid, token = extract_verify_link()

    res = client.post(
        "/api/v1/auth/password-reset", {"uid": uid, "token": token, "password": "1234"}, format="json"
    )
    assert res.status_code == 400


def test_password_must_be_at_least_twelve_characters(client, db):
    short = client.post(
        "/api/v1/auth/register",
        {"username": "carol", "email": "carol@example.com", "password": "Xk9!mQ2#vLp"},  # 11 characters
        format="json",
    )
    assert short.status_code == 400
    assert not User.objects.filter(username="carol").exists()

    long_enough = client.post(
        "/api/v1/auth/register",
        {"username": "carol", "email": "carol@example.com", "password": "Xk9!mQ2#vLpz"},  # 12 characters
        format="json",
    )
    assert long_enough.status_code == 201


def test_failed_sign_in_is_logged_without_the_username(client, db, caplog):
    with caplog.at_level("INFO", logger="fermi.security"):
        res = client.post(
            "/api/v1/auth/login",
            {"username": "mallory-secret-name", "password": "wrong"},
            format="json",
            HTTP_X_FORWARDED_FOR="203.0.113.7\r\nFAKE LOG LINE",
        )
    assert res.status_code == 401
    lines = [r.getMessage() for r in caplog.records if r.name == "fermi.security"]
    assert any(line.startswith("failed sign-in") and "203.0.113.7" in line for line in lines)
    assert not any("mallory-secret-name" in line for line in lines)
    assert not any("\n" in line or "\r" in line for line in lines)


def test_staff_sign_in_is_logged(client, db, caplog):
    User.objects.create_user(username="staffer", email="s@example.com", password="StrongPass123!", is_staff=True)
    with caplog.at_level("INFO", logger="fermi.security"):
        res = client.post("/api/v1/auth/login", {"username": "staffer", "password": "StrongPass123!"}, format="json")
    assert res.status_code == 200
    assert any(r.getMessage().startswith("staff sign-in") for r in caplog.records if r.name == "fermi.security")
