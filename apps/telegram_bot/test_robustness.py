"""Try to break the staff Telegram bot and its Mini App: malformed Telegram updates, hostile text, bad pictures and
files, double taps and races, forged or stale credentials, wrong JSON shapes. The rule for everything here: no 500, no
crash, no half-made post, no stored data that can hurt the site."""
import io
import itertools
import json
import threading
import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from PIL import Image
from rest_framework.test import APIClient

from apps.news.models import NewsCategory, NewsPost
from apps.telegram_bot import services
from apps.telegram_bot import telegram_api as tg
from apps.telegram_bot.models import BotConfig, BotSubmission, BotUser

from .test_webapp import APP, TOKEN, active_user, api, init_data, upload
from .tests import SECRET, WEBHOOK, Fake, callback, jpeg_bytes, message, say

_NAMES = ("send_message", "edit_message_text", "answer_callback", "download_file")
_REAL = {name: getattr(tg, name) for name in _NAMES}
_ids = itertools.count(50_000)


@pytest.fixture
def world(settings, tmp_path, db):
    settings.TELEGRAM_BOT_TOKEN = TOKEN
    settings.TELEGRAM_WEBHOOK_SECRET = SECRET
    settings.MEDIA_ROOT = tmp_path
    settings.TELEGRAM_SITE_URL = "https://fermi.uz"
    cache.clear()
    NewsCategory.objects.get_or_create(slug="tadbirlar", defaults={"name_uz": "Tadbirlar", "name_ru": "Т", "name_en": "E"})
    fake = Fake()
    for name in _NAMES:
        setattr(tg, name, getattr(fake, name))
    yield fake
    for name, function in _REAL.items():
        setattr(tg, name, function)


def hook(update):
    return APIClient().post(WEBHOOK, update, format="json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=SECRET)


def registered(uid, approver=False):
    return BotUser.objects.create(
        telegram_id=uid, full_name="Karimov Anvar", department="Ilmiy bo'lim", status="active", state="idle", invited=True, is_approver=approver
    )


# --------------------------------------------------------------------------------------------------------------
# the webhook: whatever arrives, answer 200 and break nothing
# --------------------------------------------------------------------------------------------------------------
WEIRD_UPDATES = [
    {},
    {"update_id": 1},
    {"update_id": "x", "message": "not a dict"},
    {"update_id": 2, "message": {}},
    {"update_id": 3, "message": {"chat": {"type": "private", "id": 5}}},  # no sender
    {"update_id": 4, "message": {"from": {"id": "five"}, "chat": {"type": "private", "id": 5}, "text": "/start"}},
    {"update_id": 5, "message": {"from": {"id": 5, "is_bot": False}, "chat": {"type": "private"}, "text": "/start"}},  # no chat id
    {"update_id": 6, "message": {"from": {"id": 5}, "chat": {"type": "private", "id": 5}, "text": None}},
    {"update_id": 7, "message": {"from": {"id": 5}, "chat": {"type": "private", "id": 5}, "text": 12345}},
    {"update_id": 8, "message": {"from": {"id": 5}, "chat": {"type": "private", "id": 5}, "photo": "nope"}},
    {"update_id": 9, "message": {"from": {"id": 5}, "chat": {"type": "private", "id": 5}, "photo": [{}]}},
    {"update_id": 10, "message": {"from": {"id": 5}, "chat": {"type": "private", "id": 5}, "document": "x"}},
    {"update_id": 11, "message": {"from": {"id": 2**70}, "chat": {"type": "private", "id": 5}, "text": "/start"}},
    {"update_id": 12, "callback_query": {}},
    {"update_id": 13, "callback_query": {"id": "c", "from": {"id": 5}, "data": "send:abc"}},
    {"update_id": 14, "callback_query": {"id": "c", "from": {"id": 5}, "data": "send:99999999999999999999999", "message": {"message_id": 1, "chat": {"id": 5}}}},
    {"update_id": 15, "callback_query": {"id": "c", "from": {"id": 5}, "data": None, "message": {"chat": {"id": 5}}}},
    {"update_id": 16, "callback_query": {"id": "c", "from": {"id": 5}, "data": "ok:1:2:3", "message": {"message_id": 1, "chat": {"id": 5}}}},
    {"update_id": 17, "edited_message": {"text": "edited"}},
    {"update_id": 18, "channel_post": {"text": "post"}},
    {"update_id": 19, "my_chat_member": {"chat": {"id": 1}}},
    {"update_id": 20, "inline_query": {"query": "x"}},
    {"update_id": 21, "message": {"from": {"id": 5}, "chat": {"type": "private", "id": 5}, "text": "/start " + "A" * 5000}},
    {"update_id": 22, "message": {"from": {"id": 5}, "chat": {"type": "private", "id": 5}, "text": "\x00\x00/start"}},
    {"update_id": 23, "message": {"from": {"id": 5, "username": "u" * 500}, "chat": {"type": "private", "id": 5}, "text": "/start"}},
]


@pytest.mark.parametrize("update", WEIRD_UPDATES, ids=[str(u.get("update_id")) for u in WEIRD_UPDATES])
def test_the_webhook_survives_any_update_shape(world, update):
    assert hook(update).status_code == 200


@pytest.mark.parametrize("body", [[], "text", 5, None])
def test_the_webhook_survives_a_non_object_body(world, body):
    res = APIClient().post(WEBHOOK, json.dumps(body), content_type="application/json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=SECRET)
    assert res.status_code in (200, 400)


def test_the_webhook_survives_invalid_json_and_a_huge_body(world):
    client = APIClient()
    bad = client.post(WEBHOOK, "{not json", content_type="application/json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=SECRET)
    assert bad.status_code in (200, 400)
    big = {"update_id": 99, "message": {"from": {"id": 5}, "chat": {"type": "private", "id": 5}, "text": "x" * 2_000_000}}
    assert hook(big).status_code == 200


def test_get_and_other_methods_on_the_webhook_are_refused(world):
    client = APIClient()
    for method in (client.get, client.put, client.delete, client.patch):
        assert method(WEBHOOK, HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=SECRET).status_code == 405


# --------------------------------------------------------------------------------------------------------------
# hostile and odd text, in the chat and in the app
# --------------------------------------------------------------------------------------------------------------
NASTY_TEXT = [
    "Oddiy sarlavha",
    "x",
    "😀🎉 Yangilik 🚀",
    "العربية نص يمين إلى يسار",
    "A​B‌C‍ zero width ﻿ bom",
    "Tab\tand\nnewlines\r\nmixed\r",
    "NUL \x00 byte inside",
    "<script>alert(1)</script>",
    "<img src=x onerror=alert(1)>",
    "'; DROP TABLE news_newspost; --",
    '" OR 1=1 --',
    "{{7*7}} ${7*7} {% load x %}",
    "%s %d {0} {name} %(x)s",
    "&amp; &lt;b&gt; &#x27; & ampersand",
    "ǅ ǆ ß İ ı ﬁ ligatures",
    "Ҳамма қатнашди ва ғолиб бўлди",
    "Студенты победили на конференции и получили награды",
    "a" * 5000,
    "слово " * 900,
    "[TAHRIRLANMAYDI] [[x]] data-preserved-block data-new-document=\"uploads/x.pdf\"",
    "https://example.com/very/long/link?x=" + "1" * 500,
    "‮ right-to-left override ‬",
    "🇺🇿" * 200,
    "퟿ private use \U0010ffff",
]


@pytest.mark.parametrize("text", NASTY_TEXT, ids=[str(i) for i in range(len(NASTY_TEXT))])
def test_any_text_goes_through_the_chat_flow_without_breaking(world, text, monkeypatch):
    # a translator that answers, so Russian text does not depend on the network
    monkeypatch.setattr(services, "translate_texts", lambda texts, source, target, timeout=20: [f"[{target}] {t}" for t in texts])
    user = registered(100)
    say(message(100, text))
    sub = BotSubmission.objects.filter(user=user).first()
    # either nothing usable was typed (an empty/blank title), or a submission is waiting for «Yuborish»
    if sub is not None and sub.title:
        data = world.sent[-1][2][0][0][1]
        say(callback(100, data))
        post = NewsPost.objects.filter(telegram_submissions__user=user).first()
        if post is None:
            # a title that is only markup (<img ...>): refused with an explanation, never half-made
            assert "kod emas" in world.answers[-1][0] and not services.strip_markup(sub.title).strip()
        else:
            assert post.is_published is False
            assert "\x00" not in post.title_uz and "<" not in post.title_uz and len(post.title_uz) <= 255
    assert NewsPost.objects.filter(is_published=True).count() == 0


@pytest.mark.parametrize("text", NASTY_TEXT, ids=[str(i) for i in range(len(NASTY_TEXT))])
def test_any_text_goes_through_the_app_without_a_500(world, text, monkeypatch):
    monkeypatch.setattr(services, "translate_texts", lambda texts, source, target, timeout=20: [f"[{target}] {t}" for t in texts])
    active_user(101)
    res = api(101).post(f"{APP}/submit", {"title": text, "body": text}, format="json")
    assert res.status_code in (201, 400), res.content
    if res.status_code == 201:
        assert NewsPost.objects.get().is_published is False


def test_hostile_names_and_departments_at_registration(world):
    for index, name in enumerate(["<b>x</b> Ali", "A" * 500, "\x00\x00\x00", "Ali\nVali", "😀😀😀", "/start", "   ", "Ó'ro"]):
        client = api(200 + index)
        res = client.post(f"{APP}/register", {"full_name": name, "department": name}, format="json")
        assert res.status_code in (200, 400), (name, res.content)
    for user in BotUser.objects.all():
        assert "\x00" not in user.full_name and len(user.full_name) <= 120


# --------------------------------------------------------------------------------------------------------------
# pictures and documents
# --------------------------------------------------------------------------------------------------------------
def _png_bytes(size=(8, 8), mode="RGBA"):
    buffer = io.BytesIO()
    Image.new(mode, size, (255, 0, 0, 128) if mode == "RGBA" else 0).save(buffer, "PNG")
    return buffer.getvalue()


def _fmt(image, fmt, **kwargs):
    buffer = io.BytesIO()
    image.save(buffer, fmt, **kwargs)
    return buffer.getvalue()


GOOD_IMAGES = {
    "jpeg": jpeg_bytes(),
    "png-alpha": _png_bytes(),
    "png-palette": _fmt(Image.new("P", (10, 10)), "PNG"),
    "webp": _fmt(Image.new("RGB", (40, 30), "blue"), "WEBP"),
    "cmyk-jpeg": _fmt(Image.new("CMYK", (20, 20)), "JPEG"),
    "gray": _fmt(Image.new("L", (20, 20), 100), "JPEG"),
    "tiny-1x1": _fmt(Image.new("RGB", (1, 1)), "PNG"),
    "wide": _fmt(Image.new("RGB", (4000, 10)), "JPEG"),
    "bigger-than-limit-side": _fmt(Image.new("RGB", (3500, 2500), "green"), "JPEG"),
}


@pytest.mark.parametrize("kind", list(GOOD_IMAGES))
def test_legitimate_pictures_of_many_kinds_are_accepted_and_normalised(world, kind):
    path = services.store_image(GOOD_IMAGES[kind], 1)
    with Image.open(services.default_storage.path(path)) as stored:
        assert stored.format == "JPEG" and max(stored.size) <= services.MAX_SIDE and stored.mode == "RGB"
        assert not stored.getexif()  # no metadata survives


def test_exif_rotation_is_applied_and_gps_is_dropped(world):
    image = Image.new("RGB", (60, 20), "red")
    exif = Image.Exif()
    exif[0x0112] = 6  # rotate 90
    exif[0x8825] = {1: "N", 2: (41.0, 18.0, 0.0)}
    data = _fmt(image, "JPEG", exif=exif)
    path = services.store_image(data, 2)
    with Image.open(services.default_storage.path(path)) as stored:
        assert stored.size == (20, 60) and not stored.getexif()


BAD_IMAGES = {
    "empty": b"",
    "text": b"hello world",
    "html": b"<html><script>alert(1)</script></html>",
    "svg": b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
    "truncated-jpeg": jpeg_bytes()[:40],
    "gif": _fmt(Image.new("P", (5, 5)), "GIF"),
    "bmp": _fmt(Image.new("RGB", (5, 5)), "BMP"),
    "pdf": b"%PDF-1.4 not an image",
    "zip": b"PK\x03\x04" + b"0" * 50,
    "exe": b"MZ\x90\x00" + b"\x00" * 100,
    "random": bytes(range(256)) * 4,
    "garbage-after-header": b"\xff\xd8\xff\xe0" + b"junk" * 50,
}


@pytest.mark.parametrize("kind", list(BAD_IMAGES))
def test_things_that_are_not_pictures_are_refused_cleanly(world, kind):
    with pytest.raises(ValueError):
        services.store_image(BAD_IMAGES[kind], 3)
    active_user(300)
    res = api(300).post(f"{APP}/upload", {"file": SimpleUploadedFile("a.jpg", BAD_IMAGES[kind], content_type="image/jpeg")}, format="multipart")
    assert res.status_code == 400


def test_a_decompression_bomb_is_refused_without_eating_memory(world):
    # 40000 x 40000 one-bit PNG: tiny file, 1.6 billion pixels once decoded
    buffer = io.BytesIO()
    Image.new("1", (40000, 40000)).save(buffer, "PNG", optimize=True)
    started = time.time()
    with pytest.raises(ValueError):
        services.store_image(buffer.getvalue(), 4)
    assert time.time() - started < 5


def test_a_huge_but_allowed_picture_is_shrunk(world):
    path = services.store_image(_fmt(Image.new("RGB", (6000, 4000), "white"), "JPEG"), 5)
    with Image.open(services.default_storage.path(path)) as stored:
        assert max(stored.size) == services.MAX_SIDE


DOCS = {
    "pdf": ("report.pdf", b"%PDF-1.7\nx", True),
    "docx": ("a.docx", b"PK\x03\x04rest", True),
    "xlsx": ("a.xlsx", b"PK\x03\x04rest", True),
    "doc": ("old.doc", b"\xd0\xcf\x11\xe0rest", True),
    "upper": ("BIG.PDF", b"%PDF-1.7\nx", True),
    "unicode": ("Ҳисобот ўқув йили.pdf", b"%PDF-1.7\nx", True),
    "pdf-as-docx": ("x.docx", b"%PDF-1.7\nx", False),
    "zip-as-pdf": ("x.pdf", b"PK\x03\x04", False),
    "exe": ("x.exe", b"MZ", False),
    "double": ("x.pdf.exe", b"%PDF-1", False),
    "html": ("x.html", b"<html>", False),
    "svg": ("x.svg", b"<svg>", False),
    "js-as-pdf": ("x.pdf", b"alert(1);", False),
    "no-ext": ("report", b"%PDF-1", False),
    "empty": ("e.pdf", b"", False),
    "docm": ("macro.docm", b"PK\x03\x04", False),
}


@pytest.mark.parametrize("kind", list(DOCS))
def test_documents_are_accepted_only_when_name_and_content_agree(world, kind):
    name, data, ok = DOCS[kind]
    if ok:
        path, title = services.store_document(data, 1, name)
        assert path.startswith("uploads/telegram/") and "<" not in title and '"' not in title
    else:
        with pytest.raises(ValueError):
            services.store_document(data, 1, name)


def test_path_tricks_in_file_names_never_reach_the_disk_path(world):
    for name in ["../../../etc/passwd.pdf", "..\\..\\x.pdf", "a/b/c.pdf", "x.pdf\x00.exe", "‮gpj.pdf"]:
        try:
            path, _title = services.store_document(b"%PDF-1.4", 6, name)
        except ValueError:
            continue
        assert ".." not in path and path.startswith("uploads/telegram/") and path.endswith(".pdf")


# --------------------------------------------------------------------------------------------------------------
# callbacks and states
# --------------------------------------------------------------------------------------------------------------
def test_callbacks_cannot_touch_somebody_elses_submission_or_a_finished_one(world):
    registered(400)
    registered(401)
    say(message(400, "Mening yangiligim\nMatn"))
    data = world.sent[-1][2][0][0][1]
    say(callback(401, data))  # another person presses my button
    assert NewsPost.objects.count() == 0
    say(callback(400, data))
    say(callback(400, data))  # tapped twice
    assert NewsPost.objects.count() == 1
    say(callback(400, data.replace("send", "cancel")))
    assert BotSubmission.objects.get(user__telegram_id=400).status == "sent"


def test_approver_buttons_on_missing_or_changed_people(world):
    boss = registered(1, approver=True)
    say(callback(1, "ok:987654"))
    say(callback(1, "block:0"))
    stranger = BotUser.objects.create(telegram_id=2, status="pending", state="idle", full_name="Ali", department="X")
    stranger.delete()
    say(callback(1, f"no:{stranger.pk}"))
    assert BotUser.objects.filter(pk=boss.pk).exists()


def test_a_blocked_or_deleted_person_cannot_continue_midway(world):
    user = registered(410)
    say(message(410, "Yarim yangilik\nMatn"))
    data = world.sent[-1][2][0][0][1]
    user.status = "blocked"
    user.save()
    say(callback(410, data))
    assert NewsPost.objects.count() == 0
    user.status = "active"
    user.save()
    user.delete()
    say(callback(410, data))
    say(message(410, "yana"))
    assert NewsPost.objects.count() == 0


def test_registration_state_machine_cannot_be_confused(world):
    say(message(420, "salom"))  # never started
    assert not BotUser.objects.filter(telegram_id=420).exists()
    say(message(420, f"/start {BotConfig.get().invite_code}"))
    say(message(420, "/start"))  # restarts in the middle
    say(message(420, "/yordam"))
    say(message(420, "/bekor"))
    say(message(420, "Ali Valiyev"))
    say(message(420, "/id"))
    say(message(420, "Laboratoriya"))
    user = BotUser.objects.get(telegram_id=420)
    assert user.status == "active" and user.state == "idle" and user.department == "Laboratoriya"
    say(message(420, f"/start {BotConfig.get().invite_code}"))  # start again after registering: no reset
    assert BotUser.objects.get(telegram_id=420).state == "idle"


# --------------------------------------------------------------------------------------------------------------
# the Mini App API: wrong shapes, forged and stale credentials
# --------------------------------------------------------------------------------------------------------------
def test_wrong_json_shapes_give_400_never_500(world):
    active_user(500)
    client = api(500)
    bodies = [
        None, [], "x", 5, {},
        {"title": None}, {"title": 5}, {"title": ["a"]}, {"title": {"a": 1}}, {"title": True},
        {"title": "t", "body": 5}, {"title": "t", "body": ["x"]}, {"title": "t", "body": None},
        {"title": "t", "photos": "x"}, {"title": "t", "photos": {"a": 1}}, {"title": "t", "photos": [None]}, {"title": "t", "photos": [1, 2]},
        {"title": "t", "photos": [["x"]]}, {"title": "t", "files": "x"}, {"title": "t", "files": [1]}, {"title": "t", "files": [None]},
        {"title": "t", "files": [{"path": 5}]}, {"title": "t", "files": [{"title": "x"}]}, {"title": "t", "files": [[]]},
        {"title": "t", "category_id": "abc"}, {"title": "t", "category_id": -1}, {"title": "t", "category_id": 10**30},
        {"title": "t", "category_id": [1]}, {"title": "t", "category_id": True}, {"title": "t", "category_id": 1.5},
    ]
    for body in bodies:
        res = client.post(f"{APP}/submit", json.dumps(body), content_type="application/json")
        assert res.status_code in (201, 400), (body, res.status_code, res.content[:200])
    # whatever got through is a draft with a real category or none
    for post in NewsPost.objects.all():
        assert post.is_published is False
    bad = client.post(f"{APP}/submit", "{broken", content_type="application/json")
    assert bad.status_code == 400
    for path in ("register",):
        for body in (None, [], "x", {"full_name": None}, {"full_name": ["a"], "department": {"b": 1}}):
            assert client.post(f"{APP}/{path}", json.dumps(body), content_type="application/json").status_code in (200, 400)


def test_upload_endpoint_shapes(world):
    active_user(500)
    client = api(500)
    assert client.post(f"{APP}/upload", {}, format="multipart").status_code == 400
    assert client.post(f"{APP}/upload", {"file": "not a file"}, format="multipart").status_code == 400
    assert client.post(f"{APP}/upload", {"other": SimpleUploadedFile("a.jpg", jpeg_bytes())}, format="multipart").status_code == 400
    assert client.post(f"{APP}/upload", json.dumps({"file": "x"}), content_type="application/json").status_code == 400
    assert client.get(f"{APP}/upload").status_code == 405
    big = SimpleUploadedFile("big.jpg", b"0" * (16 * 1024 * 1024), content_type="image/jpeg")
    assert client.post(f"{APP}/upload", {"file": big}, format="multipart").status_code == 400
    odd = SimpleUploadedFile("na\x00me‮.jpg", jpeg_bytes(), content_type="image/jpeg")
    assert client.post(f"{APP}/upload", {"file": odd}, format="multipart").status_code in (201, 400)


def test_forged_stale_and_replayed_credentials(world):
    active_user(500)
    client = APIClient()
    cases = {
        "empty": "tma ",
        "no scheme": init_data(500),
        "bearer": "Bearer " + init_data(500),
        "tma lowercase+junk": "tma " + "a" * 5000,
        "other token": "tma " + init_data(500, token="1:OTHER"),
        "tampered": "tma " + init_data(500, tamper=True),
        "expired": "tma " + init_data(500, age=13 * 3600),
        "bot account": "tma " + init_data(500, is_bot=True),
        "future": "tma " + init_data(500, age=-3600),
        "hash only": "tma hash=" + "0" * 64,
        "no user": "tma auth_date=1&hash=x",
    }
    for label, header in cases.items():
        client.credentials(HTTP_AUTHORIZATION=header)
        assert client.get(f"{APP}/me").status_code == 401, label
    client.credentials(HTTP_AUTHORIZATION="tma " + init_data(500))
    assert client.get(f"{APP}/me").status_code == 200
    # the same valid initData may be used again within its lifetime (a Mini App session does), but never for someone else
    assert client.get(f"{APP}/me").json()["full_name"] == "Karimov Anvar"
    other = APIClient()
    other.credentials(HTTP_AUTHORIZATION="tma " + init_data(501))
    assert other.get(f"{APP}/me").json()["registered"] is False  # another id sees nothing of the first person


def test_an_extra_unknown_field_in_init_data_still_verifies_but_is_not_trusted(world):
    import hashlib
    import hmac
    from urllib.parse import urlencode

    active_user(500)
    fields = {"auth_date": str(int(time.time())), "user": json.dumps({"id": 500}), "chat_instance": "123", "signature": "abc", "start_param": "x"}
    check = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))
    secret = hmac.new(b"WebAppData", TOKEN.encode(), hashlib.sha256).digest()
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION="tma " + urlencode(fields))
    assert client.get(f"{APP}/me").status_code == 200


def test_pending_blocked_and_unregistered_people_cannot_send_anything(world):
    BotUser.objects.create(telegram_id=600, status="pending", state="idle", full_name="Ali", department="X")
    BotUser.objects.create(telegram_id=601, status="blocked", state="idle", full_name="Vali", department="X")
    BotUser.objects.create(telegram_id=602, status="active", state="ask_name")
    for uid in (600, 601, 602, 603):
        client = api(uid)
        assert client.post(f"{APP}/submit", {"title": "x"}, format="json").status_code == 400
        assert upload(client).status_code == 400
        assert client.get(f"{APP}/submissions").status_code == 400
    assert NewsPost.objects.count() == 0


def test_a_double_tap_on_send_makes_one_draft_not_two(world):
    active_user(500)
    client = api(500)
    first = client.post(f"{APP}/submit", {"title": "Bitta yangilik", "body": "Matn"}, format="json")
    second = client.post(f"{APP}/submit", {"title": "Bitta yangilik", "body": "Matn"}, format="json")
    assert first.status_code == 201 and second.status_code == 201
    assert NewsPost.objects.count() == 1 and BotSubmission.objects.filter(status="sent").count() == 1
    other = client.post(f"{APP}/submit", {"title": "Boshqa yangilik", "body": "Matn"}, format="json")
    assert other.status_code == 201 and NewsPost.objects.count() == 2


def test_rate_limits_hold_without_breaking_the_api(world):
    active_user(500)
    client = api(500)
    codes = [client.get(f"{APP}/me").status_code for _ in range(130)]
    assert codes[0] == 200 and 429 in codes and 500 not in codes


# --------------------------------------------------------------------------------------------------------------
# admin side
# --------------------------------------------------------------------------------------------------------------
def test_admin_telegram_endpoints_with_odd_input(world):
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import RefreshToken

    staff = get_user_model().objects.create_user(username="tgstaff2", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(staff).access_token}")
    person = BotUser.objects.create(telegram_id=9, status="pending", state="idle", full_name="Ali", department="X")
    url = f"/api/v1/admin/telegram-users/{person.pk}"
    for body in ({"status": "hacked"}, {"status": 5}, {"status": None}, {"is_approver": "maybe"}, {"full_name": "x" * 500}, {"department": "y" * 500}, {"full_name": ""}):
        assert client.put(url, body, format="json").status_code in (200, 400), body
    person.refresh_from_db()
    assert person.status in ("pending", "active", "blocked") and len(person.full_name) <= 120
    assert client.put(url, {"telegram_id": 12345}, format="json").status_code in (200, 400)
    person.refresh_from_db()
    assert person.telegram_id == 9  # read-only
    assert client.get("/api/v1/admin/telegram-users/99999").status_code == 404
    assert client.get("/api/v1/admin/telegram-users", {"search": "'; DROP TABLE x;--", "page": "abc", "pageSize": "-5"}).status_code in (200, 400, 404)
    assert client.post("/api/v1/admin/telegram-bot", {"action": "delete_everything"}, format="json").status_code == 400
    assert client.post("/api/v1/admin/telegram-bot", "junk", content_type="application/json").status_code in (400, 415)
    assert client.delete(url).status_code == 204
    assert client.get("/api/v1/admin/news", {"source": "telegram", "status": "x", "category": "y"}).status_code == 200


def test_deleting_a_post_or_a_person_leaves_the_rest_intact(world):
    user = registered(700)
    client = api(700)
    client.post(f"{APP}/submit", {"title": "O'chiriladigan yangilik"}, format="json")
    post = NewsPost.objects.get()
    post.delete()
    assert client.get(f"{APP}/submissions").json()[0]["state"] == "removed"
    client.post(f"{APP}/submit", {"title": "Ikkinchi yangilik"}, format="json")
    user.delete()
    assert NewsPost.objects.count() == 1  # the post stays, only the person's record is gone


def test_a_deleted_category_falls_back_to_a_real_one(world):
    other = NewsCategory.objects.create(slug="vaqtincha", name_uz="V", name_ru="V", name_en="V")
    active_user(500)
    other.delete()
    res = api(500).post(f"{APP}/submit", {"title": "Kategoriyasiz", "category_id": other.pk or 999}, format="json")
    assert res.status_code == 201 and NewsPost.objects.get().category is not None


def test_no_categories_at_all_still_makes_a_draft(world):
    NewsCategory.objects.all().delete()
    active_user(500)
    res = api(500).post(f"{APP}/submit", {"title": "Kategoriyasiz yangilik"}, format="json")
    assert res.status_code in (201, 400)


def test_telegram_being_down_never_breaks_the_site_side(world, monkeypatch):
    registered(1, approver=True)
    registered(800)

    def down(*args, **kwargs):
        raise tg.TelegramError("down")

    # the real send_message swallows Telegram errors; simulate it failing at the HTTP layer
    for name in ("send_message", "edit_message_text", "answer_callback"):
        setattr(tg, name, _REAL[name])
    monkeypatch.setattr(tg, "call", down)
    say(message(800, "Telegram ishlamayapti\nMatn"))  # the reply cannot be sent: nothing crashes
    sub = BotSubmission.objects.get(user__telegram_id=800)
    assert sub.title == "Telegram ishlamayapti"
    res = api(800).post(f"{APP}/submit", {"title": "Ilova orqali", "body": "x"}, format="json")
    assert res.status_code == 201 and NewsPost.objects.count() == 1


# --------------------------------------------------------------------------------------------------------------
# races
# --------------------------------------------------------------------------------------------------------------
@pytest.mark.django_db(transaction=True)
def test_an_album_arriving_at_once_is_collected_completely(settings, tmp_path):
    settings.TELEGRAM_BOT_TOKEN = TOKEN
    settings.TELEGRAM_WEBHOOK_SECRET = SECRET
    settings.MEDIA_ROOT = tmp_path
    cache.clear()
    NewsCategory.objects.get_or_create(slug="tadbirlar", defaults={"name_uz": "Tadbirlar", "name_ru": "Т", "name_en": "E"})
    fake = Fake()
    for name in _NAMES:
        setattr(tg, name, getattr(fake, name))
    try:
        user = registered(900)
        for n in range(6):
            fake.files[f"p{n}"] = jpeg_bytes((30 + n, 30))

        def send(n):
            try:
                say(message(900, photo=f"p{n}", group="race-album", caption="Sarlavha" if n == 0 else None))
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(send, range(6)))
        assert BotSubmission.objects.filter(user=user, status="collecting").count() == 1
        sub = BotSubmission.objects.get(user=user)
        assert len(sub.photo_paths) == 6 and len(set(sub.photo_paths)) == 6
        assert len(sub.media_group_ids) == 1
        album_replies = [t for c, t, _ in fake.sent if c == 900]
        assert len(album_replies) == 1  # one answer for the whole album
    finally:
        for name, function in _REAL.items():
            setattr(tg, name, function)


@pytest.mark.django_db(transaction=True)
def test_pressing_send_many_times_at_once_creates_exactly_one_post(settings, tmp_path):
    settings.TELEGRAM_BOT_TOKEN = TOKEN
    settings.TELEGRAM_WEBHOOK_SECRET = SECRET
    settings.MEDIA_ROOT = tmp_path
    cache.clear()
    NewsCategory.objects.get_or_create(slug="tadbirlar", defaults={"name_uz": "Tadbirlar", "name_ru": "Т", "name_en": "E"})
    fake = Fake()
    for name in _NAMES:
        setattr(tg, name, getattr(fake, name))
    try:
        registered(901)
        say(message(901, "Poyga yangiligi\nMatn"))
        data = fake.sent[-1][2][0][0][1]

        def press(_):
            try:
                say(callback(901, data))
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=6) as pool:
            list(pool.map(press, range(6)))
        assert NewsPost.objects.count() == 1
    finally:
        for name, function in _REAL.items():
            setattr(tg, name, function)


@pytest.mark.django_db(transaction=True)
def test_two_phones_submitting_at_once_from_the_app_do_not_collide(settings, tmp_path):
    settings.TELEGRAM_BOT_TOKEN = TOKEN
    settings.TELEGRAM_WEBHOOK_SECRET = SECRET
    settings.MEDIA_ROOT = tmp_path
    cache.clear()
    NewsCategory.objects.get_or_create(slug="tadbirlar", defaults={"name_uz": "Tadbirlar", "name_ru": "Т", "name_en": "E"})
    fake = Fake()
    for name in _NAMES:
        setattr(tg, name, getattr(fake, name))
    try:
        for uid in (910, 911, 912):
            active_user(uid)
        results = []

        def go(uid):
            try:
                results.append(api(uid).post(f"{APP}/submit", {"title": "Bir xil sarlavha", "body": "Bir xil matn"}, format="json").status_code)
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=3) as pool:
            list(pool.map(go, (910, 911, 912)))
        assert results == [201, 201, 201]
        assert NewsPost.objects.count() == 3
        assert len({post.slug for post in NewsPost.objects.all()}) == 3  # same title, distinct addresses
    finally:
        for name, function in _REAL.items():
            setattr(tg, name, function)


def test_cleanup_removes_only_unused_old_files(world, tmp_path):
    import os
    from django.core.management import call_command

    user = registered(950)
    keep, orphan, fresh = (services.store_image(jpeg_bytes(), 950) for _ in range(3))
    BotSubmission.objects.create(user=user, status="sent", title="x", photo_paths=[keep])
    BotSubmission.objects.create(user=user, status="cancelled", title="y")
    old = time.time() - 10 * 86400
    for path in (keep, orphan):
        os.utime(services.default_storage.path(path), (old, old))
    call_command("telegram_cleanup")  # report only
    assert services.default_storage.exists(orphan)
    call_command("telegram_cleanup", "--apply", "--days", "3")
    assert services.default_storage.exists(keep) and services.default_storage.exists(fresh)
    assert not services.default_storage.exists(orphan)


def test_a_failing_publish_notice_never_breaks_the_admin_save(world, monkeypatch, django_capture_on_commit_callbacks):
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import RefreshToken

    from apps.telegram_bot import notify

    staff = get_user_model().objects.create_user(username="tgstaff3", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(staff).access_token}")
    registered(951)
    say(message(951, "Chiqadigan yangilik\nMatn"))
    say(callback(951, world.sent[-1][2][0][0][1]))
    post = NewsPost.objects.get()

    def boom(*args, **kwargs):
        raise RuntimeError("telegram exploded")

    monkeypatch.setattr(notify.tg, "send_message", boom)
    with django_capture_on_commit_callbacks(execute=True):
        res = client.put(f"/api/v1/admin/news/{post.pk}", {"title_uz": post.title_uz, "status": 1, "category_id": post.category_id, "content_uz": "<p>x</p>"}, format="json")
    assert res.status_code == 200
    post.refresh_from_db()
    assert post.is_published is True
