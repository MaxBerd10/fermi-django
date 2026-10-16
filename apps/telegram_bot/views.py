import logging
from hmac import compare_digest

from django.conf import settings
from django.core.cache import cache
from django.http import Http404
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from . import telegram_api as tg
from .services import handle_update

logger = logging.getLogger(__name__)


class TelegramWebhookView(APIView):
    """POST /api/v1/telegram/webhook/ -- Telegram delivers every message sent to the bot here. Only Telegram knows the
    secret it sends back in a header; everything else gets 403 (and a bot that is not set up does not exist: 404).
    It always answers 200 once the secret matched, so Telegram never retries (and re-runs) an update that failed."""

    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = []

    def post(self, request):
        if not tg.enabled():
            raise Http404
        sent = request.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
        if not compare_digest(sent.encode(), settings.TELEGRAM_WEBHOOK_SECRET.encode()):
            return Response({"detail": "forbidden"}, status=403)
        update = request.data if isinstance(request.data, dict) else {}
        update_id = update.get("update_id")
        # Telegram resends an update it did not get an answer to in time: run each one once
        try:
            if isinstance(update_id, int) and not cache.add(f"tg-update:{update_id}", 1, 3600):
                return Response({"ok": True})
        except Exception:  # cache down: handle the update anyway
            logger.warning("telegram dedupe cache unavailable")
        try:
            handle_update(update)
        except Exception:
            logger.exception("telegram update failed")
        return Response({"ok": True})
