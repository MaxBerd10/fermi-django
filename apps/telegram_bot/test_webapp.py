import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework.test import APIClient

from apps.news.models import NewsCategory, NewsPost
from apps.telegram_bot import telegram_api as tg
from apps.telegram_bot.models import BotConfig, BotSubmission, BotUser
from apps.telegram_bot.webapp import verify_init_data

from .tests import Fake, jpeg_bytes  # the fake Telegram of the chat tests

TOKEN = "123:ABCDEF"
APP = "/api/v1/telegram/app"
_NAMES = ("send_message", "edit_message_text", "answer_callback", "download_file")
_REAL = {name: getattr(tg, name) for name in _NAMES}


def init_data(user_id=500, token=TOKEN, age=0, start_param=None, tamper=False, is_bot=False):
    fields = {"auth_date": str(int(time.time()) - age), "query_id": "AAA", "user": json.dumps({"id": user_id, "first_name": "Anvar", "username": f"u{user_id}", "is_bot": is_bot})}
    if start_param:
        fields["start_param"] = start_param
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", token.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    if tamper:
        fields["user"] = fields["user"].replace(str(user_id), str(user_id + 1))
    return urlencode(fields)


def api(user_id=500, **kwargs):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="tma " + init_data(user_id, **kwargs))
    return client


@pytest.fixture
def app(settings, tmp_path, db):
    settings.TELEGRAM_BOT_TOKEN = TOKEN
    settings.TELEGRAM_WEBHOOK_SECRET = "s"
    settings.MEDIA_ROOT = tmp_path
    cache.clear()
    NewsCategory.objects.get_or_create(slug="tadbirlar", defaults={"name_uz": "Tadbirlar", "name_ru": "Т", "name_en": "E"})
    fake = Fake()
    for name in _NAMES:
        setattr(tg, name, getattr(fake, name))
    yield fake
    for name, function in _REAL.items():
        setattr(tg, name, function)


def active_user(user_id=500, approver=False):
    return BotUser.objects.create(telegram_id=user_id, full_name="Karimov Anvar", department="Ilmiy bo'lim", status="active", state="idle", invited=True, is_approver=approver)


def upload(client, data=None):
    return client.post(f"{APP}/upload", {"file": SimpleUploadedFile("a.jpg", data or jpeg_bytes(), content_type="image/jpeg")}, format="multipart")


# --- who is calling ------------------------------------------------------------------------------------------

def test_init_data_is_checked_for_signature_age_and_shape():
    assert verify_init_data(init_data(), TOKEN)["user"]["id"] == 500
    assert verify_init_data(init_data(), "999:OTHER") is None  # signed with another bot's token
    assert verify_init_data(init_data(tamper=True), TOKEN) is None  # the user id was changed after signing
    assert verify_init_data(init_data(age=13 * 3600), TOKEN) is None  # too old
    assert verify_init_data("", TOKEN) is None and verify_init_data("hash=abc", TOKEN) is None
    assert verify_init_data(init_data(start_param="CODE"), TOKEN)["start_param"] == "CODE"


def test_every_endpoint_refuses_a_request_without_valid_init_data(app):
    anonymous = APIClient()
    for path in ("me", "submissions"):
        assert anonymous.get(f"{APP}/{path}").status_code == 401
    assert anonymous.post(f"{APP}/submit", {}, format="json").status_code == 401
    forged = APIClient()
    forged.credentials(HTTP_AUTHORIZATION="tma " + init_data(tamper=True))
    assert forged.get(f"{APP}/me").status_code == 401
    assert api(is_bot=True).get(f"{APP}/me").status_code == 401


def test_the_app_api_is_off_while_the_bot_is_not_configured(app, settings):
    settings.TELEGRAM_BOT_TOKEN = ""
    assert api().get(f"{APP}/me").status_code == 404


# --- registration --------------------------------------------------------------------------------------------

def test_a_stranger_can_register_in_the_app_with_the_invite_code(app):
    approver = active_user(1, approver=True)
    code = BotConfig.get().invite_code
    client = api(600, start_param=code)
    me = client.get(f"{APP}/me").json()
    assert me["registered"] is False and me["invited"] is True and me["categories"][0]["title"] == "Tadbirlar"
    res = client.post(f"{APP}/register", {"full_name": "Aliyeva Dilnoza", "department": "Laboratoriya"}, format="json")
    assert res.status_code == 200 and res.json()["status"] == "active" and res.json()["registered"] is True
    assert any("ro'yxatdan o'tdi" in t for t in app.texts_to(approver.telegram_id))


def test_without_the_code_registration_waits_for_an_approver(app):
    approver = active_user(1, approver=True)
    res = api(601).post(f"{APP}/register", {"full_name": "Valiyev Sardor", "department": "Kafedra"}, format="json")
    assert res.json()["status"] == "pending"
    assert any("Ruxsat so'rayapti" in t for t in app.texts_to(approver.telegram_id))
    assert api(601).post(f"{APP}/upload", {}, format="multipart").status_code == 400  # a pending person cannot send anything
    bad = api(602).post(f"{APP}/register", {"full_name": "A", "department": ""}, format="json")
    assert bad.status_code == 400


# --- sending -------------------------------------------------------------------------------------------------

def test_photos_and_text_become_a_draft(app):
    approver = active_user(1, approver=True)
    user = active_user(500)
    client = api(500)
    first = upload(client).json()
    second = upload(client, jpeg_bytes((90, 60))).json()
    assert first["path"].startswith("uploads/telegram/") and f"/500-" in first["path"]
    res = client.post(f"{APP}/submit", {"title": "Тадбир ўтказилди", "body": "Birinchi.\nIkkinchi.", "photos": [first["path"], second["path"]]}, format="json")
    assert res.status_code == 201
    post = NewsPost.objects.get()
    assert post.is_published is False and post.cover is not None
    sub = BotSubmission.objects.get(user=user)
    assert sub.status == "sent" and sub.post_id == post.pk and len(sub.photo_paths) == 2
    assert f"/admin/news/{post.pk}" in app.texts_to(approver.telegram_id)[-1]
    listed = client.get(f"{APP}/submissions").json()
    assert listed[0]["state"] == "pending" and listed[0]["photos"] == 2
    post.is_published = True
    post.save()
    assert client.get(f"{APP}/submissions").json()[0]["state"] == "published"
    post.delete()
    assert client.get(f"{APP}/submissions").json()[0]["state"] == "removed"


def test_only_ones_own_uploaded_pictures_can_be_attached(app):
    active_user(500)
    active_user(501)
    mine = upload(api(500)).json()["path"]
    theirs = upload(api(501)).json()["path"]
    client = api(500)
    for bad in (theirs, "uploads/2026/10/other.jpg", "../../etc/passwd", "uploads/telegram/2026/10/500-" + "0" * 32 + ".jpg", 5):
        res = client.post(f"{APP}/submit", {"title": "x", "photos": [bad]}, format="json")
        assert res.status_code == 400, bad
    assert NewsPost.objects.count() == 0
    assert client.post(f"{APP}/submit", {"title": "x", "photos": [mine, mine]}, format="json").status_code == 201
    assert len(BotSubmission.objects.get().photo_paths) == 1  # the same picture twice is kept once


def test_validation_and_limits(app):
    user = active_user(500)
    client = api(500)
    assert client.post(f"{APP}/submit", {"title": "  ", "body": "x"}, format="json").status_code == 400
    assert client.post(f"{APP}/submit", {"title": "t" * 300}, format="json").status_code == 400
    assert client.post(f"{APP}/submit", {"title": "t", "body": "x" * 7000}, format="json").status_code == 400
    assert client.post(f"{APP}/submit", {"title": "t", "photos": ["a"] * 11}, format="json").status_code == 400
    assert upload(client, b"<html>not a picture</html>").status_code == 400
    for _ in range(10):
        BotSubmission.objects.create(user=user, status="sent", title="x")
    over = client.post(f"{APP}/submit", {"title": "Yana"}, format="json")
    assert over.status_code == 400 and "kunlik chegara" in str(over.json())


def test_a_category_can_be_chosen(app):
    active_user(500)
    other = NewsCategory.objects.create(slug="elonlar", name_uz="E'lonlar", name_ru="О", name_en="A")
    assert api(500).post(f"{APP}/submit", {"title": "E'lon", "category_id": other.pk}, format="json").status_code == 201
    assert NewsPost.objects.get().category_id == other.pk


def test_documents_can_be_uploaded_and_attached_but_only_real_ones(app):
    from apps.content.models import ContentBlock

    active_user(500)
    active_user(501)
    client = api(500)
    pdf = SimpleUploadedFile("Yillik_hisobot.pdf", b"%PDF-1.7\nbody", content_type="application/pdf")
    res = client.post(f"{APP}/upload", {"file": pdf}, format="multipart")
    assert res.status_code == 201 and res.json()["kind"] == "file" and res.json()["title"] == "Yillik hisobot"
    path = res.json()["path"]
    fake = SimpleUploadedFile("x.pdf", b"MZ not a pdf", content_type="application/pdf")
    assert client.post(f"{APP}/upload", {"file": fake}, format="multipart").status_code == 400
    exe = SimpleUploadedFile("x.exe", b"MZ", content_type="application/octet-stream")
    assert client.post(f"{APP}/upload", {"file": exe}, format="multipart").status_code == 400
    # someone else's document, a path outside the telegram folder, too many files: refused
    theirs = api(501).post(f"{APP}/upload", {"file": SimpleUploadedFile("o.pdf", b"%PDF-1", content_type="application/pdf")}, format="multipart").json()["path"]
    for bad in ([{"path": theirs, "title": "x"}], [{"path": "uploads/2026/10/a.pdf", "title": "x"}], [{"path": path, "title": "a"}] * 2 + [{"path": "uploads/telegram/2026/10/500-" + "1" * 32 + ".pdf"}] * 2):
        res = client.post(f"{APP}/submit", {"title": "x", "files": bad}, format="json")
        assert res.status_code == 400, bad
    ok = client.post(f"{APP}/submit", {"title": "Hisobot chiqdi", "files": [{"path": path, "title": "Yillik hisobot"}]}, format="json")
    assert ok.status_code == 201
    post = NewsPost.objects.get()
    assert ContentBlock.objects.filter(page=post.page, block_type="document").count() == 1
    assert client.get(f"{APP}/submissions").json()[0]["files"] == 1
