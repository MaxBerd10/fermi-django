"""Removes what the Telegram bot left behind and nothing uses: pictures and documents that were uploaded (Mini App) or
downloaded (chat) but never became part of a sent news item, and old unfinished or cancelled drafts.

    .venv/bin/python manage.py telegram_cleanup              # report only
    .venv/bin/python manage.py telegram_cleanup --apply      # delete
    .venv/bin/python manage.py telegram_cleanup --apply --days 7

A file is kept if any sent submission, any picture row or any document row refers to it. Run as the web user (www-data) so
nothing root-owned ends up in the media folder."""
import os
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.media_lib.models import Document, Image
from apps.telegram_bot.models import BotSubmission

FOLDER = os.path.join("uploads", "telegram")


class Command(BaseCommand):
    help = "Delete unused files and stale drafts of the Telegram bot."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--days", type=int, default=3, help="only files older than this many days (default 3)")

    def handle(self, *args, **options):
        cutoff = time.time() - options["days"] * 86400
        used: set[str] = set()
        for sub in BotSubmission.objects.filter(status=BotSubmission.SENT):
            used.update(sub.photo_paths)
            used.update(item["path"] for item in sub.file_items if isinstance(item, dict) and "path" in item)
        used.update(name for name in Image.objects.filter(file__startswith=FOLDER).values_list("file", flat=True))
        used.update(name for name in Document.objects.filter(file__startswith=FOLDER).values_list("file", flat=True))

        root = os.path.join(settings.MEDIA_ROOT, FOLDER)
        stale, kept, freed = [], 0, 0
        for folder, _dirs, files in os.walk(root):
            for name in files:
                path = os.path.join(folder, name)
                relative = os.path.relpath(path, settings.MEDIA_ROOT).replace(os.sep, "/")
                if relative in used or os.path.getmtime(path) > cutoff:
                    kept += 1
                    continue
                stale.append(path)
                freed += os.path.getsize(path)

        old_drafts = BotSubmission.objects.exclude(status=BotSubmission.SENT).filter(
            updated_at__lt=timezone.now() - timezone.timedelta(days=options["days"])
        )
        self.stdout.write(f"{len(stale)} unused file(s), {freed / 1024 / 1024:.1f} MB; {kept} kept; {old_drafts.count()} old draft(s)")
        if not options["apply"]:
            self.stdout.write("Report only. Add --apply to delete.")
            return
        for path in stale:
            os.remove(path)
        old_drafts.delete()
        self.stdout.write(self.style.SUCCESS("Deleted."))
