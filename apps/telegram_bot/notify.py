"""Telling a post's author, in Telegram, that an administrator published it -- with the link people keep asking for.
Kept free of imports from admin_api so that the news editor can call it without a circular import."""
from django.conf import settings
from django.utils import timezone

from . import telegram_api as tg


def public_url(post) -> str:
    return f"{settings.TELEGRAM_SITE_URL}/detail/{post.slug}"


def notify_published(post) -> None:
    """Call right after a post became published. Sends once per submission (a post unpublished and published again
    does not message the author twice)."""
    if not tg.enabled():
        return
    from .models import BotSubmission

    for submission in BotSubmission.objects.filter(post=post, published_notified=False).select_related("user"):
        if post.published_at and post.published_at > timezone.now():
            when = timezone.localtime(post.published_at).strftime("%d.%m.%Y %H:%M")
            text = f"✅ Yangiligingiz tasdiqlandi: «{post.title_uz}»\n{when} da saytda chiqadi.\n\nHavola: {public_url(post)}"
        else:
            text = f"✅ Yangiligingiz saytda chiqdi: «{post.title_uz}»\n\nHavola: {public_url(post)}"
        tg.send_message(submission.user.telegram_id, text)
        submission.published_notified = True
        submission.save(update_fields=["published_notified"])
