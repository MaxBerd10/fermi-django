"""The Telegram bot through which university staff send news (photos + text) that lands in the admin panel as a
DRAFT: nothing is ever published without an administrator. See services.py for the conversation and
docs/TELEGRAM_BOT.md for how it is set up."""
import secrets

from django.db import models


def new_invite_code() -> str:
    return secrets.token_urlsafe(6)  # 8 chars of [A-Za-z0-9_-]: valid in a t.me/<bot>?start=<code> link


class BotConfig(models.Model):
    """One row: the invite code that is part of the link handed to the staff. Rotating it kills every old link."""

    invite_code = models.CharField(max_length=32, default=new_invite_code)
    updated_at = models.DateTimeField(auto_now=True)

    @classmethod
    def get(cls) -> "BotConfig":
        config, _ = cls.objects.get_or_create(pk=1)
        return config


class BotUser(models.Model):
    PENDING = "pending"
    ACTIVE = "active"
    BLOCKED = "blocked"
    STATUS_CHOICES = [(PENDING, "Ruxsat kutmoqda"), (ACTIVE, "Faol"), (BLOCKED, "Bloklangan")]

    # conversation position while the person registers
    NEW = "new"
    ASK_NAME = "ask_name"
    ASK_DEPARTMENT = "ask_department"
    IDLE = "idle"

    telegram_id = models.BigIntegerField(unique=True)
    username = models.CharField(max_length=64, blank=True)
    full_name = models.CharField(max_length=120, blank=True)  # as the person typed it, not Telegram's profile name
    department = models.CharField(max_length=120, blank=True)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=PENDING, db_index=True)
    is_approver = models.BooleanField(default=False)
    state = models.CharField(max_length=20, default=NEW)
    invited = models.BooleanField(default=False)  # arrived with a valid invite code
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name or self.telegram_id} ({self.department})"

    @property
    def label(self) -> str:
        name = self.full_name or (f"@{self.username}" if self.username else str(self.telegram_id))
        return f"{name} ({self.department})" if self.department else name


class BotSubmission(models.Model):
    COLLECTING = "collecting"
    SENT = "sent"
    CANCELLED = "cancelled"

    user = models.ForeignKey(BotUser, on_delete=models.CASCADE, related_name="submissions")
    status = models.CharField(max_length=12, default=COLLECTING, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    body = models.TextField(blank=True)
    photo_paths = models.JSONField(default=list)  # MEDIA_ROOT-relative paths of the stored pictures
    file_items = models.JSONField(default=list)  # attached documents: [{"path": ..., "title": ...}] (PDF, Word, Excel, ...)
    published_notified = models.BooleanField(default=False)  # the author was told (with the link) that the post is public
    media_group_ids = models.JSONField(default=list)  # albums already answered once
    post = models.ForeignKey("news.NewsPost", null=True, blank=True, on_delete=models.SET_NULL, related_name="telegram_submissions")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
