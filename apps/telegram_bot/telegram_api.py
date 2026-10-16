"""A minimal Telegram Bot API client on the standard library (no extra dependency). The token is never logged or put
in an exception message: a failure says only which method failed."""
import json
import logging
import urllib.error
import urllib.request

from django.conf import settings

logger = logging.getLogger(__name__)

API = "https://api.telegram.org"
TIMEOUT = 8
MAX_DOWNLOAD_BYTES = 20 * 1024 * 1024  # Telegram itself serves at most 20 MB through getFile


class TelegramError(Exception):
    pass


def enabled() -> bool:
    return bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_WEBHOOK_SECRET)


def call(method: str, params: dict | None = None) -> dict:
    url = f"{API}/bot{settings.TELEGRAM_BOT_TOKEN}/{method}"
    request = urllib.request.Request(
        url, data=json.dumps(params or {}).encode(), headers={"Content-Type": "application/json"}, method="POST"
    )
    try:
        with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
            payload = json.loads(response.read())
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise TelegramError(f"{method}: {type(exc).__name__}") from None
    if not payload.get("ok"):
        raise TelegramError(f"{method}: {payload.get('description', 'not ok')}")
    return payload.get("result")


def _button(label: str, data: str) -> dict:
    """(label, "webapp:<url>") opens that address as a Telegram Mini App; anything else is callback data."""
    if data.startswith("webapp:"):
        return {"text": label, "web_app": {"url": data[len("webapp:"):]}}
    return {"text": label, "callback_data": data}


def send_message(chat_id: int, text: str, buttons: list[list[tuple[str, str]]] | None = None) -> dict | None:
    """Plain text (no parse mode, so nothing a person typed can break the message). `buttons` = rows of
    (label, callback_data | "webapp:<url>")."""
    params: dict = {"chat_id": chat_id, "text": text[:4000], "disable_web_page_preview": True}
    if buttons:
        params["reply_markup"] = {"inline_keyboard": [[_button(t, d) for t, d in row] for row in buttons]}
    try:
        return call("sendMessage", params)
    except TelegramError as exc:  # a person who blocked the bot must not break the rest of the update
        logger.warning("telegram sendMessage failed: %s", exc)
        return None


def edit_message_text(chat_id: int, message_id: int, text: str, buttons: list[list[tuple[str, str]]] | None = None) -> None:
    params: dict = {"chat_id": chat_id, "message_id": message_id, "text": text[:4000], "disable_web_page_preview": True}
    params["reply_markup"] = {"inline_keyboard": [[{"text": t, "callback_data": d} for t, d in row] for row in (buttons or [])]}
    try:
        call("editMessageText", params)
    except TelegramError as exc:
        logger.warning("telegram editMessageText failed: %s", exc)


def answer_callback(callback_id: str, text: str = "", alert: bool = False) -> None:
    try:
        call("answerCallbackQuery", {"callback_query_id": callback_id, "text": text[:190], "show_alert": alert})
    except TelegramError as exc:
        logger.warning("telegram answerCallbackQuery failed: %s", exc)


def download_file(file_id: str) -> bytes:
    """The bytes of a file a person sent. Refuses anything Telegram reports as bigger than the cap."""
    info = call("getFile", {"file_id": file_id})
    if int(info.get("file_size") or 0) > MAX_DOWNLOAD_BYTES or not info.get("file_path"):
        raise TelegramError("getFile: too big or missing")
    url = f"{API}/file/bot{settings.TELEGRAM_BOT_TOKEN}/{info['file_path']}"
    try:
        with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
            data = response.read(MAX_DOWNLOAD_BYTES + 1)
    except (urllib.error.URLError, TimeoutError):
        raise TelegramError("download: failed") from None
    if len(data) > MAX_DOWNLOAD_BYTES:
        raise TelegramError("download: too big")
    return data
