"""Connects the bot to the site: tells Telegram to deliver every message to https://<site>/api/v1/telegram/webhook/
(with the secret from the environment), and sets the bot's command menu. Run once after the token is in the
environment file, and again if the site address changes.

    .venv/bin/python manage.py telegram_set_webhook            # connect
    .venv/bin/python manage.py telegram_set_webhook --status   # what Telegram currently has
    .venv/bin/python manage.py telegram_set_webhook --delete   # disconnect"""
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from apps.telegram_bot import telegram_api as tg


class Command(BaseCommand):
    help = "Register (or remove) the Telegram webhook of the staff news bot."

    def add_arguments(self, parser):
        parser.add_argument("--delete", action="store_true")
        parser.add_argument("--status", action="store_true")

    def handle(self, *args, **options):
        if not tg.enabled():
            raise CommandError("TELEGRAM_BOT_TOKEN and TELEGRAM_WEBHOOK_SECRET must both be set in the environment.")
        try:
            me = tg.call("getMe")
            self.stdout.write(f"Bot: @{me.get('username')} ({me.get('first_name')})")
            if options["delete"]:
                tg.call("deleteWebhook", {"drop_pending_updates": True})
                self.stdout.write(self.style.SUCCESS("Webhook removed."))
                return
            if options["status"]:
                info = tg.call("getWebhookInfo")
                self.stdout.write(f"url: {info.get('url') or '-'} | pending: {info.get('pending_update_count')} | last error: {info.get('last_error_message') or '-'}")
                return
            url = f"{settings.TELEGRAM_SITE_URL}/api/v1/telegram/webhook/"
            tg.call(
                "setWebhook",
                {
                    "url": url,
                    "secret_token": settings.TELEGRAM_WEBHOOK_SECRET,
                    "allowed_updates": ["message", "callback_query"],
                    "drop_pending_updates": True,
                    "max_connections": 10,
                },
            )
            tg.call(
                "setMyCommands",
                {
                    "commands": [
                        {"command": "start", "description": "Boshlash"},
                        {"command": "yordam", "description": "Qanday yuboriladi"},
                        {"command": "bekor", "description": "Yozilganini bekor qilish"},
                    ]
                },
            )
        except tg.TelegramError as exc:
            raise CommandError(f"Telegram refused: {exc}") from None
        self.stdout.write(self.style.SUCCESS(f"Webhook set: {url}"))
