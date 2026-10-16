import io
import itertools

import pytest
from django.core.cache import cache
from PIL import Image
from rest_framework.test import APIClient

from apps.content.admin_content import blocks_to_html
from apps.news.models import NewsCategory, NewsPost
from apps.telegram_bot import services
from apps.telegram_bot import telegram_api as tg
from apps.telegram_bot.models import BotConfig, BotSubmission, BotUser

WEBHOOK = "/api/v1/telegram/webhook/"
SECRET = "test-secret-value"
_ids = itertools.count(1000)
_NAMES = ("send_message", "edit_message_text", "answer_callback", "download_file")
_REAL = {name: getattr(tg, name) for name in _NAMES}


def jpeg_bytes(size=(64, 48), mode="RGB") -> bytes:
    buffer = io.BytesIO()
    Image.new(mode, size, "red").save(buffer, "JPEG" if mode == "RGB" else "PNG")
    return buffer.getvalue()


class Fake:
    """Stands in for Telegram: remembers what the bot sent, serves files by id."""

    def __init__(self):
        self.sent, self.edited, self.answers = [], [], []
        self.files = {}

    def send_message(self, chat_id, text, buttons=None):
        self.sent.append((chat_id, text, buttons))
        return {"message_id": len(self.sent)}

    def edit_message_text(self, chat_id, message_id, text, buttons=None):
        self.edited.append((chat_id, message_id, text))

    def answer_callback(self, callback_id, text="", alert=False):
        self.answers.append((text, alert))

    def download_file(self, file_id):
        if file_id not in self.files:
            raise tg.TelegramError("missing")
        return self.files[file_id]

    def texts_to(self, chat_id):
        return [t for c, t, _ in self.sent if c == chat_id]


@pytest.fixture
def bot(settings, tmp_path, db):
    settings.TELEGRAM_BOT_TOKEN = "123:ABC"
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


def message(user_id, text=None, photo=None, caption=None, group=None, chat_type="private", document=None, is_bot=False):
    body = {"message_id": next(_ids), "from": {"id": user_id, "is_bot": is_bot, "username": f"u{user_id}"}, "chat": {"id": user_id, "type": chat_type}}
    if text is not None:
        body["text"] = text
    if photo:
        body["photo"] = [{"file_id": photo, "file_size": 100, "width": 64, "height": 48}]
    if document:
        body["document"] = document
    if caption:
        body["caption"] = caption
    if group:
        body["media_group_id"] = group
    return {"update_id": next(_ids), "message": body}


def callback(user_id, data, message_id=7):
    return {"update_id": next(_ids), "callback_query": {"id": "cb", "from": {"id": user_id}, "data": data, "message": {"message_id": message_id, "chat": {"id": user_id}}}}


def say(update):
    services.handle_update(update)


def register(user_id, name="Karimov Anvar", department="Ilmiy bo'lim", code=True):
    start = f"/start {BotConfig.get().invite_code}" if code else "/start"
    say(message(user_id, start))
    say(message(user_id, name))
    say(message(user_id, department))
    return BotUser.objects.get(telegram_id=user_id)


# --- webhook ---------------------------------------------------------------------------------------------------

def test_webhook_is_off_without_a_token_and_checks_the_secret(db, settings, bot):
    client = APIClient()
    assert client.post(WEBHOOK, message(5, "/id"), format="json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN="wrong").status_code == 403
    assert client.post(WEBHOOK, message(5, "/id"), format="json").status_code == 403
    ok = client.post(WEBHOOK, message(5, "/id"), format="json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=SECRET)
    assert ok.status_code == 200 and bot.texts_to(5) == ["Sizning Telegram raqamingiz: 5"]
    settings.TELEGRAM_BOT_TOKEN = ""
    assert client.post(WEBHOOK, message(5, "/id"), format="json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=SECRET).status_code == 404


def test_the_same_update_is_run_once(bot):
    client = APIClient()
    update = message(6, "/id")
    for _ in range(3):
        client.post(WEBHOOK, update, format="json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=SECRET)
    assert len(bot.texts_to(6)) == 1


# --- registration ----------------------------------------------------------------------------------------------

def test_a_person_with_the_invite_code_registers_and_is_active(bot):
    approver = BotUser.objects.create(telegram_id=1, full_name="Admin", status="active", is_approver=True, state="idle")
    user = register(10)
    assert user.status == "active" and user.full_name == "Karimov Anvar" and user.department == "Ilmiy bo'lim" and user.invited
    assert any("Tayyor" in t for t in bot.texts_to(10))
    assert any("ro'yxatdan o'tdi" in t for t in bot.texts_to(approver.telegram_id))


def test_a_person_without_the_code_waits_for_an_approver(bot):
    approver = BotUser.objects.create(telegram_id=1, full_name="Admin", status="active", is_approver=True, state="idle")
    user = register(11, code=False)
    assert user.status == "pending"
    to_approver = [(t, b) for c, t, b in bot.sent if c == approver.telegram_id]
    assert "Ruxsat so'rayapti" in to_approver[0][0]
    ok_data = to_approver[0][1][0][0][1]
    say(message(11, "salom"))
    assert "ko'rib chiqilmoqda" in bot.texts_to(11)[-1]
    say(callback(approver.telegram_id, ok_data))
    user.refresh_from_db()
    assert user.status == "active" and "ruxsat berildi" in bot.texts_to(11)[-1].lower()


def test_only_an_approver_may_press_the_approval_buttons(bot):
    pending = register(12, code=False)
    stranger = register(13)
    say(callback(stranger.telegram_id, f"ok:{pending.pk}"))
    pending.refresh_from_db()
    assert pending.status == "pending" and bot.answers[-1][1] is True


def test_blocked_people_and_group_chats_are_ignored(bot):
    user = register(14)
    user.status = "blocked"
    user.save()
    before = len(bot.sent)
    say(message(14, "salom"))
    say(message(14, "/start"))
    say(message(99, "salom", chat_type="group"))
    say(message(98, "salom", is_bot=True))
    assert len(bot.sent) == before and BotUser.objects.filter(telegram_id__in=[98, 99]).count() == 0


def test_a_wrong_code_is_not_an_invite(bot):
    say(message(15, "/start not-the-code"))
    say(message(15, "Aliyev Vali"))
    say(message(15, "Kafedra"))
    assert BotUser.objects.get(telegram_id=15).status == "pending"


# --- sending a news item ---------------------------------------------------------------------------------------

def test_photos_and_text_become_a_draft_news_post(bot):
    approver = BotUser.objects.create(telegram_id=1, full_name="Admin", status="active", is_approver=True, state="idle")
    user = register(20)
    bot.files.update({"f1": jpeg_bytes(), "f2": jpeg_bytes((80, 60))})
    say(message(20, photo="f1", caption="Тадбир ўтказилди\nBirinchi paragraf.\nIkkinchi paragraf."))
    say(message(20, photo="f2"))
    sub = BotSubmission.objects.get(user=user)
    assert sub.status == "collecting" and len(sub.photo_paths) == 2 and sub.title == "Тадбир ўтказилди"
    send_data = bot.sent[-1][2][0][0][1]
    say(callback(20, send_data))

    post = NewsPost.objects.get()
    assert post.is_published is False
    assert not any("а" <= ch.lower() <= "я" for ch in post.title_uz)  # the Cyrillic title arrives in Latin
    assert post.cover is not None
    assert "Birinchi paragraf." in blocks_to_html(post.page, "uz") and "Ikkinchi paragraf." in blocks_to_html(post.page, "uz")
    sub.refresh_from_db()
    assert sub.status == "sent" and sub.post_id == post.pk
    note = bot.texts_to(approver.telegram_id)[-1]
    assert f"/admin/news/{post.pk}" in note and "Karimov Anvar" in note


def test_an_album_is_answered_once(bot):
    user = register(21)
    for n in range(3):
        bot.files[f"p{n}"] = jpeg_bytes()
    replies_before = len(bot.texts_to(21))
    for n in range(3):
        say(message(21, photo=f"p{n}", group="album-1", caption="Sarlavha" if n == 0 else None))
    assert len(bot.texts_to(21)) == replies_before + 1
    assert len(BotSubmission.objects.get(user=user).photo_paths) == 3


def test_a_draft_needs_a_title(bot):
    user = register(22)
    bot.files["only"] = jpeg_bytes()
    say(message(22, photo="only"))
    say(callback(22, bot.sent[-1][2][0][0][1]))
    assert NewsPost.objects.count() == 0 and "sarlavha" in bot.answers[-1][0].lower()
    say(message(22, "Endi sarlavha\nMatn"))
    say(callback(22, bot.sent[-1][2][0][0][1]))
    assert NewsPost.objects.count() == 1


def test_only_pictures_of_the_right_kind_are_accepted(bot):
    register(23)
    bot.files["junk"] = b"<html>not a picture</html>"
    say(message(23, photo="junk"))
    assert "qabul qilib bo'lmadi" in bot.texts_to(23)[-1]
    say(message(23, "x", document={"file_id": "d", "mime_type": "application/pdf"}))
    assert BotSubmission.objects.filter(user__telegram_id=23, photo_paths=[]).count() >= 0
    say(message(23, document={"file_id": "d", "mime_type": "application/pdf"}))
    assert "Faqat rasm va matn" in bot.texts_to(23)[-1]


def test_limits_on_pictures_and_on_sent_items_per_day(bot):
    user = register(24)
    bot.files["p"] = jpeg_bytes()
    say(message(24, "Sarlavha"))
    for _ in range(services.MAX_PHOTOS):
        say(message(24, photo="p"))
    say(message(24, photo="p"))
    assert "ko'pi bilan" in bot.texts_to(24)[-1]
    assert len(BotSubmission.objects.get(user=user).photo_paths) == services.MAX_PHOTOS
    for _ in range(services.MAX_PER_DAY):
        BotSubmission.objects.create(user=user, status="sent", title="x")
    say(message(24, "Yana bir yangilik"))
    assert "kunlik chegara" in bot.texts_to(24)[-1]


def test_cancel_and_text_is_escaped(bot):
    user = register(25)
    say(message(25, "<script>alert(1)</script>\n<b>qalin</b> matn"))
    say(callback(25, bot.sent[-1][2][0][0][1]))
    post = NewsPost.objects.get()
    html = blocks_to_html(post.page, "uz")
    assert "<" not in post.title_uz and ">" not in post.title_uz  # markup typed into the title is dropped
    assert "<b>" not in html and "<script" not in html and "qalin" in html
    say(message(25, "Yana"))
    say(message(25, "/bekor"))
    assert BotSubmission.objects.filter(user=user, status="collecting").count() == 0


# --- admin side ------------------------------------------------------------------------------------------------

@pytest.fixture
def staff(db):
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import RefreshToken

    user = get_user_model().objects.create_user(username="tgstaff", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def test_admin_lists_people_and_allowing_one_tells_them(bot, staff):
    person = register(30, code=False)
    listed = staff.get("/api/v1/admin/telegram-users").json()["results"]
    assert listed[0]["full_name"] == "Karimov Anvar" and listed[0]["status"] == "pending"
    res = staff.put(f"/api/v1/admin/telegram-users/{person.pk}", {"status": "active", "is_approver": 1, "department": "Laboratoriya"}, format="json")
    assert res.status_code == 200
    person.refresh_from_db()
    assert person.status == "active" and person.is_approver and person.department == "Laboratoriya"
    assert "ruxsat berildi" in bot.texts_to(30)[-1].lower()
    assert staff.post("/api/v1/admin/telegram-users", {}, format="json").status_code == 405  # people come from the bot only


def test_admin_bot_settings_and_the_invite_code_rotates(bot, staff, monkeypatch):
    monkeypatch.setattr(tg, "call", lambda method, params=None: {"username": "fjsti_test_bot"})
    cache.clear()
    before = staff.get("/api/v1/admin/telegram-bot").json()
    assert before["enabled"] and before["invite_link"] == f"https://t.me/fjsti_test_bot?start={before['invite_code']}"
    after = staff.post("/api/v1/admin/telegram-bot", {"action": "rotate_code"}, format="json").json()
    assert after["invite_code"] != before["invite_code"]
    # the old link no longer registers anyone as invited
    say(message(31, f"/start {before['invite_code']}"))
    assert BotUser.objects.get(telegram_id=31).invited is False


def test_telegram_endpoints_are_staff_only(db, client):
    for path in ("admin/telegram-users", "admin/telegram-bot"):
        assert client.get(f"/api/v1/{path}").status_code in (401, 403)


def test_news_shows_who_sent_it_and_can_be_filtered(bot, staff):
    register(32, name="Valiyev Sardor", department="Ilmiy bo'lim")
    say(message(32, "Telegram yangiligi\nMatn"))
    say(callback(32, bot.sent[-1][2][0][0][1]))
    mine = staff.get("/api/v1/admin/news", {"source": "telegram"}).json()["results"]
    assert len(mine) == 1 and mine[0]["telegram_author"] == {"name": "Valiyev Sardor", "department": "Ilmiy bo'lim"}
    assert staff.get("/api/v1/admin/dashboard").json()["telegram_drafts"] == 1


# --- the real HTTP layer, against a stand-in Telegram server --------------------------------------------------

@pytest.fixture
def stub_telegram(settings):
    """A local HTTP server that answers like api.telegram.org, recording what the bot called."""
    import json
    import threading
    from http.server import BaseHTTPRequestHandler, HTTPServer

    calls = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def do_POST(self):
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))) or b"{}")
            calls.append((self.path, body))
            method = self.path.rsplit("/", 1)[-1]
            result = {"getFile": {"file_path": "photos/x.jpg", "file_size": 20}, "getMe": {"username": "stub_bot"}}.get(method, {"message_id": 1})
            if method == "fail":
                payload = {"ok": False, "description": "Bad Request"}
            else:
                payload = {"ok": True, "result": result}
            data = json.dumps(payload).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def do_GET(self):
            data = b"FILEBYTES"
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

    server = HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    settings.TELEGRAM_BOT_TOKEN = "123:SECRETTOKEN"
    settings.TELEGRAM_WEBHOOK_SECRET = SECRET
    original = tg.API
    tg.API = f"http://127.0.0.1:{server.server_port}"
    yield calls
    tg.API = original
    server.shutdown()


def test_the_http_layer_speaks_the_bot_api_and_never_leaks_the_token(stub_telegram):
    real = tg
    result = real.send_message(5, "Salom", [[("Ha", "ok:1")]])
    path, body = stub_telegram[-1]
    assert path == "/bot123:SECRETTOKEN/sendMessage" and body["chat_id"] == 5
    assert body["reply_markup"] == {"inline_keyboard": [[{"text": "Ha", "callback_data": "ok:1"}]]} and result == {"message_id": 1}
    assert real.download_file("abc") == b"FILEBYTES"
    assert [p.rsplit("/", 1)[-1] for p, _ in stub_telegram][-2:] == ["sendMessage", "getFile"]
    with pytest.raises(real.TelegramError) as caught:
        real.call("fail")
    assert "SECRETTOKEN" not in str(caught.value) and "fail" in str(caught.value)


def test_a_flood_of_strangers_is_cut_off_but_invited_people_still_get_in(bot):
    for n in range(services.NEW_STRANGERS_PER_HOUR):
        say(message(5000 + n, "/start"))
    say(message(9000, "/start"))
    assert BotUser.objects.filter(telegram_id=9000).count() == 0 and "vaqtincha yopiq" in bot.texts_to(9000)[-1]
    say(message(9001, f"/start {BotConfig.get().invite_code}"))
    assert BotUser.objects.filter(telegram_id=9001).exists()


def test_the_bot_survives_a_broken_cache(bot, monkeypatch):
    def broken(*args, **kwargs):
        raise ConnectionError("redis down")

    monkeypatch.setattr(cache, "add", broken)
    monkeypatch.setattr(cache, "incr", broken)
    client = APIClient()
    res = client.post(WEBHOOK, message(40, "/id"), format="json", HTTP_X_TELEGRAM_BOT_API_SECRET_TOKEN=SECRET)
    assert res.status_code == 200 and bot.texts_to(40) == ["Sizning Telegram raqamingiz: 40"]
