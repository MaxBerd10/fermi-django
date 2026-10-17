"""The Telegram Mini App's API (the page itself is frontend/src/tg, opened at /tg inside Telegram).

Who is calling is proven by Telegram, not by a password: the app sends the `initData` string Telegram hands to it in
the header `Authorization: tma <initData>`, and every request checks its HMAC signature (made with the bot token),
that it is fresh, and then maps the Telegram id to a registered person. Registration, the daily limits, the approver
notifications and the DRAFT-only rule are exactly those of the chat bot (services.py)."""
import hashlib
import hmac
import json
import re
import time
from hmac import compare_digest
from urllib.parse import parse_qsl

from django.conf import settings
from django.core.files.storage import default_storage
from django.db import transaction
from django.http import Http404
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.parsers import JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.news.models import NewsCategory

from . import telegram_api as tg
from .models import BotConfig, BotSubmission, BotUser
from .services import (
    DOCUMENT_EXTENSIONS,
    DOCUMENT_PATH_RE,
    MAX_FILES,
    MAX_NAME,
    MAX_PER_DAY,
    MAX_PHOTOS,
    MAX_TEXT,
    NEW_STRANGERS_PER_HOUR,
    _counter_ok,
    _today_start,
    finalize_submission,
    finish_registration,
    clean_title,
    notify_new_draft,
    store_document,
    store_image,
)

INIT_DATA_MAX_AGE = 12 * 3600  # a Mini App session older than this must be reopened
MAX_UPLOAD_BYTES = 15 * 1024 * 1024
UPLOADS_PER_DAY = 60
REQUESTS_PER_MINUTE = 120
MAX_TITLE = 250


class Unauthorized(APIException):
    status_code = 401
    default_detail = "Ilovani Telegram ichidan qayta oching."
    default_code = "unauthorized"


def verify_init_data(init_data: str, bot_token: str, max_age: int = INIT_DATA_MAX_AGE) -> dict | None:
    """The Telegram user (and start_param) inside a genuine, fresh `initData`, or None. The signature is
    HMAC_SHA256(key = HMAC_SHA256("WebAppData", bot_token), data = the other fields sorted as "key=value" lines)."""
    try:
        data = dict(parse_qsl(init_data, keep_blank_values=True))
        received = data.pop("hash", "")
        if not received:
            return None
        check = "\n".join(f"{key}={value}" for key, value in sorted(data.items()))
        secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
        expected = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
        if not compare_digest(expected, received):
            return None
        age = time.time() - int(data.get("auth_date", "0"))
        if age > max_age or age < -300:
            return None
        user = json.loads(data["user"])
        if not isinstance(user.get("id"), int):
            return None
        return {"user": user, "start_param": data.get("start_param", "")}
    except (ValueError, KeyError, TypeError):
        return None


class TgAppView(APIView):
    """Base of every Mini App endpoint: verifies initData before the handler runs."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []
    parser_classes = [JSONParser, MultiPartParser]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        if not tg.enabled():
            raise Http404
        header = request.headers.get("Authorization", "")
        info = verify_init_data(header[4:], settings.TELEGRAM_BOT_TOKEN) if header.startswith("tma ") else None
        if info is None or info["user"].get("is_bot"):
            raise Unauthorized()
        self.tg_user = info["user"]
        self.start_param = info["start_param"]
        if not _counter_ok(f"tg-app-rate:{self.tg_user['id']}", 60, REQUESTS_PER_MINUTE):
            raise APIException("Juda ko'p so'rov. Biroz kuting.")
        self.bot_user = BotUser.objects.filter(telegram_id=self.tg_user["id"]).first()

    def active_user(self) -> BotUser:
        user = self.bot_user
        if user is None or user.status != BotUser.ACTIVE or user.state != BotUser.IDLE:
            raise ValidationError({"detail": "Sizga hali ruxsat berilmagan."})
        return user

    def invited(self) -> bool:
        code = BotConfig.get().invite_code
        return bool(self.start_param) and compare_digest(self.start_param.encode(), code.encode())

    def me_payload(self) -> dict:
        user = self.bot_user
        sent_today = (
            BotSubmission.objects.filter(user=user, status=BotSubmission.SENT, created_at__gte=_today_start()).count() if user else 0
        )
        return {
            "registered": bool(user and user.state == BotUser.IDLE),
            "status": user.status if user else None,
            "full_name": user.full_name if user else "",
            "department": user.department if user else "",
            "is_approver": bool(user and user.is_approver),
            "telegram_name": self.tg_user.get("first_name", ""),
            "invited": self.invited() or bool(user and user.invited),
            "categories": [{"id": c.pk, "title": c.name_uz} for c in NewsCategory.objects.order_by("id")],
            "limits": {"photos": MAX_PHOTOS, "files": MAX_FILES, "per_day": MAX_PER_DAY, "sent_today": sent_today, "title": MAX_TITLE, "text": MAX_TEXT},
        }


class MeView(TgAppView):
    def get(self, request):
        return Response(self.me_payload())


class RegisterView(TgAppView):
    def post(self, request):
        name = " ".join(str(request.data.get("full_name") or "").split())
        department = " ".join(str(request.data.get("department") or "").split())
        if not 3 <= len(name) <= MAX_NAME:
            raise ValidationError({"full_name": ["Ism va familiyani to'liq yozing."]})
        if not 2 <= len(department) <= MAX_NAME:
            raise ValidationError({"department": ["Bo'lim yoki kafedra nomini yozing."]})
        user = self.bot_user
        if user is not None and user.state == BotUser.IDLE:
            return Response(self.me_payload())  # already registered
        invited = self.invited()
        if user is None:
            if not invited and not _counter_ok("tg-strangers", 3600, NEW_STRANGERS_PER_HOUR):
                raise ValidationError({"detail": "Hozir ro'yxatdan o'tish vaqtincha yopiq. Institut bergan havola orqali kiring."})
            user = BotUser.objects.create(telegram_id=self.tg_user["id"], username=(self.tg_user.get("username") or "")[:64], invited=invited)
        elif invited:
            user.invited = True
        user.full_name, user.department = name, department
        finish_registration(user)
        self.bot_user = user
        return Response(self.me_payload())


class SubmissionsView(TgAppView):
    def get(self, request):
        user = self.active_user()
        items = []
        for sub in BotSubmission.objects.filter(user=user, status=BotSubmission.SENT).select_related("post").order_by("-created_at")[:30]:
            if sub.post is None:
                state, url = "removed", None  # an administrator deleted it
            elif sub.post.is_published:
                state, url = "published", f"/detail/{sub.post.slug}"
            else:
                state, url = "pending", None
            items.append(
                {
                    "id": sub.pk,
                    "title": sub.title,
                    "state": state,
                    "url": url,
                    "photos": len(sub.photo_paths),
                    "files": len(sub.file_items),
                    "thumb": f"/media/{sub.photo_paths[0]}" if sub.photo_paths else None,
                    "created_at": sub.created_at,
                }
            )
        return Response(items)


class UploadView(TgAppView):
    """One picture (re-encoded) or one document (PDF/Word/Excel/PowerPoint, checked by content) per request."""

    def post(self, request):
        user = self.active_user()
        upload = request.FILES.get("file")
        if upload is None:
            raise ValidationError({"detail": "Fayl yuborilmadi."})
        if upload.size > MAX_UPLOAD_BYTES:
            raise ValidationError({"detail": "Fayl juda katta (15 MB gacha)."})
        if not _counter_ok(f"tg-uploads:{user.telegram_id}", 86400, UPLOADS_PER_DAY):
            raise ValidationError({"detail": "Bugungi yuklash chegarasiga yetdingiz."})
        name = upload.name or ""
        if name.lower().endswith(DOCUMENT_EXTENSIONS):
            try:
                path, title = store_document(upload.read(), user.telegram_id, name)
            except ValueError:
                raise ValidationError({"detail": "Fayl qabul qilinmadi. PDF, Word yoki Excel fayl tanlang."}) from None
            return Response({"path": path, "url": f"/media/{path}", "kind": "file", "title": title}, status=201)
        try:
            path = store_image(upload.read(), user.telegram_id)
        except ValueError:
            raise ValidationError({"detail": "Rasm qabul qilinmadi. JPG, PNG yoki WEBP rasm tanlang."}) from None
        return Response({"path": path, "url": f"/media/{path}", "kind": "image"}, status=201)


class SubmitView(TgAppView):
    def post(self, request):
        user = self.active_user()
        title = " ".join(str(request.data.get("title") or "").split())
        body = str(request.data.get("body") or "").replace("\r\n", "\n").strip()
        photos = request.data.get("photos") or []
        files = request.data.get("files") or []
        category_id = request.data.get("category_id")
        if not title:
            raise ValidationError({"title": ["Sarlavha yozing."]})
        if len(title) > MAX_TITLE:
            raise ValidationError({"title": [f"Sarlavha {MAX_TITLE} belgidan oshmasligi kerak."]})
        if len(body) > MAX_TEXT:
            raise ValidationError({"body": [f"Matn {MAX_TEXT} belgidan oshmasligi kerak."]})
        if not isinstance(photos, list) or len(photos) > MAX_PHOTOS:
            raise ValidationError({"photos": [f"Ko'pi bilan {MAX_PHOTOS} ta rasm."]})
        own = re.compile(rf"^uploads/telegram/\d{{4}}/\d{{2}}/{user.telegram_id}-[0-9a-f]{{32}}\.jpg$")
        clean: list[str] = []
        for path in photos:
            # only pictures this very person uploaded through the app: no other file of the media folder can be named
            if not isinstance(path, str) or not own.match(path) or not default_storage.exists(path):
                raise ValidationError({"photos": ["Rasm topilmadi. Qayta yuklang."]})
            if path not in clean:
                clean.append(path)
        if not isinstance(files, list) or len(files) > MAX_FILES:
            raise ValidationError({"files": [f"Ko'pi bilan {MAX_FILES} ta fayl."]})
        items: list[dict] = []
        for item in files:
            path = item.get("path") if isinstance(item, dict) else None
            found = DOCUMENT_PATH_RE.match(path) if isinstance(path, str) else None
            if not found or found.group(1) != str(user.telegram_id) or not default_storage.exists(path):
                raise ValidationError({"files": ["Fayl topilmadi. Qayta yuklang."]})
            if all(path != existing["path"] for existing in items):
                items.append({"path": path, "title": clean_title(str(item.get("title") or "") + ".x")})
        if BotSubmission.objects.filter(user=user, status=BotSubmission.SENT, created_at__gte=_today_start()).count() >= MAX_PER_DAY:
            raise ValidationError({"detail": f"Bugun {MAX_PER_DAY} ta yangilik yubordingiz — bu kunlik chegara."})
        category = int(category_id) if str(category_id or "").isdigit() else None
        with transaction.atomic():
            sub = BotSubmission.objects.create(user=user, title=title, body=body, photo_paths=clean, file_items=items)
            try:
                finalize_submission(sub, user, category)
            except Exception:
                import logging

                logging.getLogger(__name__).exception("mini app draft failed")
                raise ValidationError({"detail": "Yangilikni saqlab bo'lmadi. Birozdan keyin qayta urining."}) from None
        notify_new_draft(sub, user)
        return Response({"ok": True}, status=201)
