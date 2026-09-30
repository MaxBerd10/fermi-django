"""POST admin/translate -- machine-translates the admin forms' Uzbek text
(plain titles and RichTextEditor HTML alike) into ru/en so an editor only
has to write the uz version; see translateTexts() in frontend/src/api/admin.ts.

Uses Google Translate's keyless web endpoint with format=html, which keeps
the markup (<p>, <strong>, <img>, ...) intact and only translates the text
between tags. The result is a draft the editor can still correct before
saving -- the form fills the ru/en fields, it doesn't save them itself.
"""
import html
import json
import re
import ssl
import urllib.error
import urllib.parse
import urllib.request

import certifi
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .common import IsAdminStaff

_ENDPOINT = "https://translate.googleapis.com/translate_a/t"
_LANGS = {"uz", "ru", "en"}
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
# The endpoint re-inserts a space after an inline tag it moved a word out
# of ("<strong>area</strong> ." / "</p><p> Next") -- undo just that.
_SPACE_BEFORE_PUNCT_RE = re.compile(r"(</[a-z0-9]+>)\s+([.,!?;:])")
_SPACE_AFTER_OPEN_RE = re.compile(r"(<(?:p|li|h[1-6]|blockquote)>)\s+")
_TAG_RE = re.compile(r"<[a-zA-Z/][^>]*>")


class TranslationError(Exception):
    pass


def translate_texts(texts: list[str], source: str, target: str) -> list[str]:
    if not any(text.strip() for text in texts):
        return list(texts)
    query = urllib.parse.urlencode({"client": "gtx", "sl": source, "tl": target, "format": "html"})
    body = urllib.parse.urlencode([("q", text) for text in texts]).encode()
    request = urllib.request.Request(
        f"{_ENDPOINT}?{query}",
        data=body,
        headers={
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "User-Agent": "Mozilla/5.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20, context=_SSL_CONTEXT) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        raise TranslationError(str(exc)) from exc

    # One q comes back as a bare string list entry either way, but guard
    # against the [translated, detected_lang] pair shape it sometimes uses.
    translated = [item[0] if isinstance(item, list) else item for item in result]
    if len(translated) != len(texts):
        raise TranslationError("unexpected response shape")
    return [_clean(text, original) for text, original in zip(translated, texts)]


def _clean(text: str, original: str) -> str:
    if not original.strip():
        return original
    if not _TAG_RE.search(original):
        # format=html escapes apostrophes etc. ("Let&#39;s") -- a plain-text
        # field like a title would show those literally.
        return html.unescape(text)
    return _SPACE_AFTER_OPEN_RE.sub(r"\1", _SPACE_BEFORE_PUNCT_RE.sub(r"\1\2", text))


class TranslateView(APIView):
    """Body: {"source": "uz", "targets": ["ru", "en"], "texts": {"title": "...", "content": "<p>...</p>"}}
    Response: {"translations": [{"lang": "ru", "texts": {"title": "...", "content": "..."}}, ...]}

    A list rather than a {"ru": ..., "en": ...} map on purpose: the frontend's
    apiClient collapses any object whose keys are all locale codes down to
    the active language (resolveLocale in frontend/src/api/client.ts)."""

    permission_classes = [IsAuthenticated, IsAdminStaff]

    def post(self, request):
        source = request.data.get("source", "uz")
        targets = request.data.get("targets") or ["ru", "en"]
        texts = request.data.get("texts")
        if source not in _LANGS or not isinstance(targets, list) or not set(targets) <= _LANGS:
            return Response({"detail": "Noto'g'ri til."}, status=400)
        if not isinstance(texts, dict) or not all(isinstance(v, str) for v in texts.values()):
            return Response({"detail": "texts obyekt bo'lishi kerak."}, status=400)

        keys = list(texts.keys())
        values = [texts[key] for key in keys]
        output = []
        try:
            for target in targets:
                if target == source:
                    continue
                output.append({"lang": target, "texts": dict(zip(keys, translate_texts(values, source, target)))})
        except TranslationError:
            return Response({"detail": "Tarjima xizmati javob bermadi. Keyinroq urinib ko'ring."}, status=502)
        return Response({"translations": output})
