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
