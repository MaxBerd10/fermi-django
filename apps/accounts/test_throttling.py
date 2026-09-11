import pytest
from rest_framework.test import APIClient


@pytest.fixture
def client():
    return APIClient()


def test_register_is_rate_limited(client, db):
    for i in range(5):
        res = client.post(
            "/api/v1/auth/register",
            {"username": f"flood{i}", "email": f"flood{i}@example.com", "password": "StrongPass123!"},
            format="json",
        )
        assert res.status_code == 201

    res = client.post(
        "/api/v1/auth/register",
        {"username": "flood_over", "email": "flood_over@example.com", "password": "StrongPass123!"},
        format="json",
    )
    assert res.status_code == 429


def test_login_is_rate_limited(client, db):
    for _ in range(10):
        res = client.post(
            "/api/v1/auth/login", {"username": "nobody", "password": "wrong"}, format="json"
        )
        assert res.status_code == 401

    res = client.post("/api/v1/auth/login", {"username": "nobody", "password": "wrong"}, format="json")
    assert res.status_code == 429
