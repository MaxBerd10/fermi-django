"""admin/telegram-users and admin/telegram-bot -- who may send news through the staff Telegram bot, and the invite
link they enter by (apps/telegram_bot). Staff only."""
from django.core.cache import cache
from django.conf import settings
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.telegram_bot import telegram_api as tg
from apps.telegram_bot.models import BotConfig, BotSubmission, BotUser, new_invite_code
from apps.telegram_bot.services import user_changed_status

from .common import AdminPagination, AdminSearchMixin, IsAdminStaff


class AdminTelegramUserSerializer(serializers.ModelSerializer):
    posts = serializers.SerializerMethodField()

    class Meta:
        model = BotUser
        fields = [
            "id", "telegram_id", "username", "full_name", "department", "status", "is_approver",
            "created_at", "last_seen_at", "posts",
        ]
        read_only_fields = ["id", "telegram_id", "username", "created_at", "last_seen_at", "posts"]

    def get_posts(self, obj):
        return obj.submissions.filter(status=BotSubmission.SENT).count()


class AdminTelegramUserViewSet(AdminSearchMixin, viewsets.ModelViewSet):
    """People are created by the bot itself, never from here: the panel only lets an administrator change their
    name / department / status (allow, block) and mark who is an approver."""

    search_fields = ("full_name", "department", "username")
    queryset = BotUser.objects.all().order_by("-created_at")
    serializer_class = AdminTelegramUserSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
    http_method_names = ["get", "put", "patch", "delete", "head", "options"]

    def perform_update(self, serializer):
        before = serializer.instance.status
        user = serializer.save()
        if before != BotUser.ACTIVE and user.status == BotUser.ACTIVE:
            user_changed_status(user)  # tell the person they may start sending


def _bot_username() -> str | None:
    if not tg.enabled():
        return None
    cached = cache.get("tg-bot-username")
    if cached:
        return cached
    try:
        username = tg.call("getMe").get("username")
    except tg.TelegramError:
        return None
    if username:
        cache.set("tg-bot-username", username, 3600)
    return username


class AdminTelegramBotView(APIView):
    permission_classes = [IsAuthenticated, IsAdminStaff]

    def _payload(self):
        config = BotConfig.get()
        username = _bot_username()
        return {
            "enabled": tg.enabled(),
            "username": username,
            "invite_code": config.invite_code,
            "invite_link": f"https://t.me/{username}?start={config.invite_code}" if username else None,
            "bot_link": f"https://t.me/{username}" if username else None,
            "webhook_url": f"{settings.TELEGRAM_SITE_URL}/api/v1/telegram/webhook/",
            "pending": BotUser.objects.filter(status=BotUser.PENDING, state=BotUser.IDLE).count(),
            "active": BotUser.objects.filter(status=BotUser.ACTIVE).count(),
            "approvers": BotUser.objects.filter(status=BotUser.ACTIVE, is_approver=True).count(),
        }

    def get(self, request):
        return Response(self._payload())

    def post(self, request):
        if request.data.get("action") != "rotate_code":
            return Response({"detail": "Noma'lum amal."}, status=400)
        config = BotConfig.get()
        config.invite_code = new_invite_code()
        config.save()
        return Response(self._payload())
