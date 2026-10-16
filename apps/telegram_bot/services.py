"""The conversation of the staff news bot.

A person opens the bot through the invite link (t.me/<bot>?start=<code>), tells their name and department, and from
then on sends pictures and text. Those pile up in one open "submission"; «Yuborish» turns it into a DRAFT news post in
the admin panel (never a published one) and tells the approvers. A person without the invite code is registered too,
but waits for an approver's «Ruxsat berish». Strangers outside private chats and blocked people are ignored.

Everything here is plain text on purpose (no Telegram formatting), so nothing a person types can break a message."""
import io
import logging
import uuid
from datetime import timedelta
from hmac import compare_digest

from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.db import transaction
from django.utils import timezone
from django.utils.html import escape
from PIL import Image, ImageOps
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.admin_api.news_views import AdminPostSerializer
from apps.admin_api.uz_script import to_latin
from apps.news.models import NewsCategory

from . import telegram_api as tg
from .models import BotConfig, BotSubmission, BotUser

logger = logging.getLogger(__name__)

MAX_PHOTOS = 10
MAX_PER_DAY = 10
MAX_TEXT = 6000
MAX_NAME = 80
STALE_AFTER = timedelta(hours=12)
MESSAGES_PER_MINUTE = 30
NEW_STRANGERS_PER_HOUR = 20  # people without the invite code who may start registering, all together
MAX_PIXELS = 50_000_000
MAX_SIDE = 2560
ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

HELP = (
    "Bu bot FJSTI saytiga yangilik yuborish uchun.\n\n"
    "1) Rasm(lar) va matn yuboring. Matnning birinchi qatori — sarlavha, qolgani — yangilik matni.\n"
    "2) Hammasi tayyor bo'lgach «Yuborish» tugmasini bosing.\n"
    "3) Yangilikni admin ko'rib chiqadi va tasdiqlasa, saytda chiqadi.\n\n"
    f"Bitta yangilikka ko'pi bilan {MAX_PHOTOS} ta rasm. Rasmni «fayl» sifatida yuborsangiz sifati buzilmaydi.\n"
    "/bekor — yozilgan narsani bekor qilish\n/id — Telegram raqamingiz"
)


# ---------------------------------------------------------------------------------------------------------------
# entry point
# ---------------------------------------------------------------------------------------------------------------
def app_buttons() -> list[list[tuple[str, str]]]:
    """The «Ilovani ochish» button that opens the Mini App (apps/telegram_bot/webapp.py + frontend/src/tg)."""
    return [[("📱 Ilovani ochish", f"webapp:{settings.TELEGRAM_SITE_URL}/tg")]]


def handle_update(update: dict) -> None:
    if isinstance(update.get("message"), dict):
        handle_message(update["message"])
    elif isinstance(update.get("callback_query"), dict):
        handle_callback(update["callback_query"])


def _counter_ok(key: str, window: int, limit: int) -> bool:
    """A fixed-window counter in the cache. If the cache itself is down the bot keeps working, unlimited."""
    try:
        cache.add(key, 0, window)
        return cache.incr(key) <= limit
    except Exception:
        return True


def _rate_ok(telegram_id: int) -> bool:
    return _counter_ok(f"tg-rate:{telegram_id}", 60, MESSAGES_PER_MINUTE)


def handle_message(message: dict) -> None:
    chat = message.get("chat") or {}
    sender = message.get("from") or {}
    if chat.get("type") != "private" or sender.get("is_bot") or not isinstance(sender.get("id"), int):
        return
    telegram_id = sender["id"]
    if not _rate_ok(telegram_id):
        return
    text = (message.get("text") or "").strip()

    if text == "/id":
        tg.send_message(chat["id"], f"Sizning Telegram raqamingiz: {telegram_id}")
        return

    user = BotUser.objects.filter(telegram_id=telegram_id).first()
    if text.startswith("/start"):
        return _start(chat["id"], sender, user, text)
    if user is None:
        tg.send_message(chat["id"], "Boshlash uchun maxsus havola orqali kiring yoki /start bosing.")
        return

    user.last_seen_at = timezone.now()
    fields = ["last_seen_at"]
    username = (sender.get("username") or "")[:64]
    if username != user.username:
        user.username = username
        fields.append("username")
    user.save(update_fields=fields)

    if user.status == BotUser.BLOCKED:
        return  # silently: a blocked person gets no conversation to push on
    if user.state == BotUser.ASK_NAME:
        return _got_name(chat["id"], user, text)
    if user.state == BotUser.ASK_DEPARTMENT:
        return _got_department(chat["id"], user, text)
    if user.status == BotUser.PENDING:
        tg.send_message(chat["id"], "Ruxsat so'rovingiz adminda ko'rib chiqilmoqda. Ruxsat berilgach sizga xabar beramiz.")
        return
    if text in ("/yordam", "/help"):
        tg.send_message(chat["id"], HELP)
        return
    if text == "/bekor":
        return _cancel_open(chat["id"], user)
    _collect(chat["id"], user, message, text)


# ---------------------------------------------------------------------------------------------------------------
# registration
# ---------------------------------------------------------------------------------------------------------------
def _start(chat_id: int, sender: dict, user: BotUser | None, text: str) -> None:
    code = text.partition(" ")[2].strip()
    valid_code = bool(code) and compare_digest(code.encode(), BotConfig.get().invite_code.encode())
    if user is not None and user.status == BotUser.BLOCKED:
        return
    if user is not None and user.state == BotUser.IDLE:
        if user.status == BotUser.ACTIVE:
            tg.send_message(chat_id, f"Salom, {user.full_name}! Yangilik uchun rasm va matn yuboring yoki ilovani oching.\n\n{HELP}", app_buttons())
        else:
            tg.send_message(chat_id, "Ruxsat so'rovingiz adminda ko'rib chiqilmoqda.")
        return
    if user is None:
        if not valid_code and not _counter_ok("tg-strangers", 3600, NEW_STRANGERS_PER_HOUR):
            # someone flooding the bot with registrations: nothing is stored, no approver is bothered
            tg.send_message(chat_id, "Hozir ro'yxatdan o'tish vaqtincha yopiq. Iltimos, institut bergan havola orqali kiring yoki keyinroq urining.")
            return
        user = BotUser.objects.create(
            telegram_id=sender["id"], username=(sender.get("username") or "")[:64], state=BotUser.ASK_NAME, invited=valid_code
        )
    else:  # started again in the middle of registering
        user.state = BotUser.ASK_NAME
        user.invited = user.invited or valid_code
        user.save(update_fields=["state", "invited"])
    tg.send_message(
        chat_id,
        "Assalomu alaykum! Bu FJSTI saytiga yangilik yuborish uchun bot.\n\nAvval tanishib olamiz. Ism va familiyangizni yozing:",
    )


def _got_name(chat_id: int, user: BotUser, text: str) -> None:
    name = " ".join(text.split())
    if len(name) < 3 or len(name) > MAX_NAME or name.startswith("/"):
        tg.send_message(chat_id, "Iltimos, ism va familiyangizni to'liq yozing (matn ko'rinishida).")
        return
    user.full_name, user.state = name, BotUser.ASK_DEPARTMENT
    user.save(update_fields=["full_name", "state"])
    tg.send_message(chat_id, f"Rahmat, {name}. Qaysi bo'lim, kafedra yoki laboratoriyada ishlaysiz?")


def _got_department(chat_id: int, user: BotUser, text: str) -> None:
    department = " ".join(text.split())
    if len(department) < 2 or len(department) > MAX_NAME or department.startswith("/"):
        tg.send_message(chat_id, "Iltimos, bo'lim yoki kafedra nomini yozing (masalan: Ilmiy bo'lim).")
        return
    user.department = department
    finish_registration(user)


def finish_registration(user: BotUser) -> None:
    """The name and department are known: a person who came with the invite code is active at once, anyone else waits
    for an approver. Used by the chat and by the Mini App alike."""
    user.state = BotUser.IDLE
    if user.invited:
        user.status = BotUser.ACTIVE
        user.save(update_fields=["full_name", "department", "state", "status"])
        tg.send_message(user.telegram_id, "✅ Tayyor! Endi yangilik uchun rasm va matn yuboring yoki ilovani oching.\n\n" + HELP, app_buttons())
        notify_approvers(f"👤 Yangi xodim ro'yxatdan o'tdi: {user.label}", [[("🚫 Bloklash", f"block:{user.pk}")]])
    else:
        user.status = BotUser.PENDING
        user.save(update_fields=["full_name", "department", "state", "status"])
        tg.send_message(user.telegram_id, "So'rovingiz adminga yuborildi. Ruxsat berilgach sizga xabar beramiz.")
        handle = f" @{user.username}" if user.username else ""
        notify_approvers(
            f"👤 Ruxsat so'rayapti (havolasiz kirgan): {user.label}{handle}",
            [[("✅ Ruxsat berish", f"ok:{user.pk}"), ("❌ Rad etish", f"no:{user.pk}")]],
        )


def notify_approvers(text: str, buttons: list[list[tuple[str, str]]] | None = None) -> None:
    for approver in BotUser.objects.filter(is_approver=True, status=BotUser.ACTIVE):
        tg.send_message(approver.telegram_id, text, buttons)


def user_changed_status(user: BotUser) -> None:
    """Called when an administrator changes a person's status in the admin panel: tell the person."""
    if user.status == BotUser.ACTIVE and user.state == BotUser.IDLE:
        tg.send_message(user.telegram_id, "✅ Sizga ruxsat berildi. Endi yangilik uchun rasm va matn yuborishingiz mumkin.\n\n" + HELP, app_buttons())


# ---------------------------------------------------------------------------------------------------------------
# collecting a news item
# ---------------------------------------------------------------------------------------------------------------
def _today_start():
    return timezone.localtime().replace(hour=0, minute=0, second=0, microsecond=0)


def _split_title(text: str) -> tuple[str, str]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "", ""
    first = lines[0]
    if len(first) > 250:  # a title that long is really the first paragraph
        return first[:247].rstrip() + "…", "\n".join(lines)
    return first, "\n".join(lines[1:])


def store_image(data: bytes, owner: int) -> str:
    """Checks that `data` really is a picture (JPEG/PNG/WEBP of sane size), re-encodes it as JPEG (which also drops
    every metadata field, GPS included) and saves it under uploads/telegram/<owner>-<random>.jpg (the owner's Telegram id
    in the name is how a later "submit" proves the picture is the sender's own). Returns the MEDIA_ROOT-relative path."""
    try:
        image = Image.open(io.BytesIO(data))
        if image.format not in ALLOWED_FORMATS or image.width * image.height > MAX_PIXELS:
            raise ValueError("format or size")
        image = ImageOps.exif_transpose(image)
        image.load()
    except Exception:
        raise ValueError("not a usable picture") from None
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGBA")
        flat = Image.new("RGB", image.size, "white")
        flat.paste(image, mask=image.split()[-1])
        image = flat
    else:
        image = image.convert("RGB")
    image.thumbnail((MAX_SIDE, MAX_SIDE))
    buffer = io.BytesIO()
    image.save(buffer, "JPEG", quality=88, optimize=True)
    stamp = timezone.localdate()
    return default_storage.save(f"uploads/telegram/{stamp:%Y/%m}/{owner}-{uuid.uuid4().hex}.jpg", ContentFile(buffer.getvalue()))


def _photo_file_id(message: dict) -> str | None:
    photos = message.get("photo")
    if isinstance(photos, list) and photos:
        return max(photos, key=lambda p: p.get("file_size") or p.get("width", 0) * p.get("height", 0)).get("file_id")
    document = message.get("document")
    if isinstance(document, dict) and str(document.get("mime_type", "")).startswith("image/"):
        return document.get("file_id")
    return None


def _open_submission(user: BotUser) -> BotSubmission:
    """The person's open submission (locked); one older than STALE_AFTER is dropped and a fresh one started."""
    sub = BotSubmission.objects.select_for_update().filter(user=user, status=BotSubmission.COLLECTING).first()
    if sub is not None and timezone.now() - sub.updated_at > STALE_AFTER:
        sub.status = BotSubmission.CANCELLED
        sub.save(update_fields=["status"])
        sub = None
    return sub or BotSubmission.objects.create(user=user)


def _summary(sub: BotSubmission) -> str:
    title = sub.title or "— (hali yo'q: matn yozing, birinchi qator sarlavha bo'ladi)"
    return (
        f"📝 Sarlavha: {title}\n🖼 Rasmlar: {len(sub.photo_paths)}\n\n"
        "Yana rasm yoki matn qo'shishingiz mumkin. Tayyor bo'lsa «Yuborish» ni bosing."
    )


def _collect(chat_id: int, user: BotUser, message: dict, text: str) -> None:
    file_id = _photo_file_id(message)
    caption = (message.get("caption") or "").strip()
    body_text = text or caption
    if not file_id and not text:
        tg.send_message(chat_id, "Faqat rasm va matn qabul qilinadi.")
        return
    if len(body_text) > MAX_TEXT:
        tg.send_message(chat_id, f"Matn juda uzun (eng ko'pi {MAX_TEXT} belgi). Qisqartirib qayta yuboring.")
        return
    sent_today = BotSubmission.objects.filter(user=user, status=BotSubmission.SENT, created_at__gte=_today_start()).count()
    if sent_today >= MAX_PER_DAY:
        tg.send_message(chat_id, f"Bugun {MAX_PER_DAY} ta yangilik yubordingiz — bu kunlik chegara. Ertaga davom eting.")
        return

    stored = None
    if file_id:
        try:
            stored = store_image(tg.download_file(file_id), user.telegram_id)
        except (tg.TelegramError, ValueError):
            tg.send_message(chat_id, "Rasmni qabul qilib bo'lmadi. JPG, PNG yoki WEBP rasm yuboring (20 MB gacha).")
            return

    reply = True
    with transaction.atomic():
        sub = _open_submission(user)
        if stored:
            if len(sub.photo_paths) >= MAX_PHOTOS:
                default_storage.delete(stored)
                tg.send_message(chat_id, f"Bitta yangilikka ko'pi bilan {MAX_PHOTOS} ta rasm. «Yuborish» ni bosing.")
                return
            sub.photo_paths = [*sub.photo_paths, stored]
        if body_text:
            if not sub.title:
                sub.title, rest = _split_title(body_text)
                sub.body = "\n".join(filter(None, [sub.body, rest]))
            else:
                sub.body = "\n".join(filter(None, [sub.body, body_text]))
        group = message.get("media_group_id")
        if group:  # an album arrives as several messages: answer once
            if group in sub.media_group_ids:
                reply = False
            else:
                sub.media_group_ids = [*sub.media_group_ids, group]
        sub.save()
    if reply:
        tg.send_message(chat_id, _summary(sub), [[("📤 Yuborish", f"send:{sub.pk}"), ("🗑 Bekor qilish", f"cancel:{sub.pk}")]])


def _cancel_open(chat_id: int, user: BotUser) -> None:
    cancelled = BotSubmission.objects.filter(user=user, status=BotSubmission.COLLECTING).update(status=BotSubmission.CANCELLED)
    tg.send_message(chat_id, "Bekor qilindi." if cancelled else "Bekor qiladigan narsa yo'q.")


# ---------------------------------------------------------------------------------------------------------------
# the draft
# ---------------------------------------------------------------------------------------------------------------
def create_draft(sub: BotSubmission, category_id: int | None = None):
    """A DRAFT news post (status 0: hidden from the public site) made through the same serializer the admin panel's
    news form uses, so it is exactly what the panel would save."""
    category = (
        (category_id and NewsCategory.objects.filter(pk=category_id).first())
        or NewsCategory.objects.filter(slug="tadbirlar").first()
        or NewsCategory.objects.order_by("id").first()
    )
    # The page model refuses plain text that looks like markup, so angle brackets are simply dropped from what a person typed
    clean = lambda text: text.replace("<", "").replace(">", "")  # noqa: E731
    paragraphs = "".join(f"<p>{escape(clean(line))}</p>" for line in sub.body.splitlines() if clean(line).strip())
    paths = list(sub.photo_paths)
    payload = {
        "title_uz": to_latin(clean(sub.title)),
        "content_uz": to_latin(paragraphs),
        "category_id": category.pk if category else None,
        "status": 0,
        "date": timezone.now().isoformat(),
        "img": paths[0] if paths else "",
        "gallery": paths[1:],
    }
    request = Request(APIRequestFactory().post("/api/v1/admin/news", payload, format="json"), parsers=[JSONParser()])
    serializer = AdminPostSerializer(data=payload, context={"request": request})
    serializer.is_valid(raise_exception=True)
    return serializer.save()


def handle_callback(callback: dict) -> None:
    sender = callback.get("from") or {}
    message = callback.get("message") or {}
    chat_id = (message.get("chat") or {}).get("id")
    message_id = message.get("message_id")
    action, _, raw = str(callback.get("data") or "").partition(":")
    if not isinstance(sender.get("id"), int) or not chat_id or not raw.isdigit():
        return
    user = BotUser.objects.filter(telegram_id=sender["id"]).first()
    if user is None or user.status == BotUser.BLOCKED:
        return
    pk = int(raw)
    if action in ("send", "cancel"):
        return _owner_action(callback, user, action, pk, chat_id, message_id)
    if action in ("ok", "no", "block"):
        return _approver_action(callback, user, action, pk, chat_id, message_id)


def _owner_action(callback: dict, user: BotUser, action: str, pk: int, chat_id: int, message_id) -> None:
    with transaction.atomic():
        sub = BotSubmission.objects.select_for_update().filter(pk=pk, user=user).first()
        if sub is None or sub.status != BotSubmission.COLLECTING:
            tg.answer_callback(callback["id"], "Bu yangilik allaqachon yuborilgan yoki bekor qilingan.", True)
            return
        if action == "cancel":
            sub.status = BotSubmission.CANCELLED
            sub.save(update_fields=["status"])
            tg.answer_callback(callback["id"], "Bekor qilindi.")
            tg.edit_message_text(chat_id, message_id, "🗑 Bekor qilindi.")
            return
        if not sub.title:
            tg.answer_callback(callback["id"], "Avval matn yozing: birinchi qator sarlavha bo'ladi.", True)
            return
        if BotSubmission.objects.filter(user=user, status=BotSubmission.SENT, created_at__gte=_today_start()).count() >= MAX_PER_DAY:
            tg.answer_callback(callback["id"], "Kunlik chegaraga yetdingiz.", True)
            return
        try:
            finalize_submission(sub, user)
        except Exception:
            logger.exception("telegram draft failed")
            tg.answer_callback(callback["id"], "Yangilikni saqlab bo'lmadi. Birozdan keyin qayta urining.", True)
            return
    tg.answer_callback(callback["id"], "Yuborildi!")
    tg.edit_message_text(chat_id, message_id, f"✅ Yuborildi: «{sub.title}». Admin ko'rib chiqadi, tasdiqlansa saytda chiqadi.")
    notify_new_draft(sub, user)


def finalize_submission(sub: BotSubmission, user: BotUser, category_id: int | None = None) -> None:
    """Turns an open submission into a DRAFT news post (call inside a transaction)."""
    post = create_draft(sub, category_id)
    sub.status, sub.post = BotSubmission.SENT, post
    sub.save(update_fields=["status", "post"])


def notify_new_draft(sub: BotSubmission, user: BotUser) -> None:
    notify_approvers(
        f"📰 Yangi yangilik (qoralama): «{sub.title}»\nMuallif: {user.label}\nRasmlar: {len(sub.photo_paths)}\n\n"
        f"Ko'rib chiqish: {settings.TELEGRAM_SITE_URL}/admin/news/{sub.post_id}"
    )


def _approver_action(callback: dict, user: BotUser, action: str, pk: int, chat_id: int, message_id) -> None:
    if not (user.is_approver and user.status == BotUser.ACTIVE):
        tg.answer_callback(callback["id"], "Bu tugma faqat adminlar uchun.", True)
        return
    target = BotUser.objects.filter(pk=pk).first()
    if target is None:
        tg.answer_callback(callback["id"], "Xodim topilmadi.", True)
        return
    if action == "ok":
        target.status = BotUser.ACTIVE
        target.save(update_fields=["status"])
        user_changed_status(target)
        result = f"✅ Ruxsat berildi: {target.label}"
    elif action == "no":
        target.status = BotUser.BLOCKED
        target.save(update_fields=["status"])
        tg.send_message(target.telegram_id, "Afsus, sizga ruxsat berilmadi.")
        result = f"❌ Rad etildi: {target.label}"
    else:
        target.status = BotUser.BLOCKED
        target.save(update_fields=["status"])
        result = f"🚫 Bloklandi: {target.label}"
    tg.answer_callback(callback["id"], "Bajarildi.")
    tg.edit_message_text(chat_id, message_id, result)
