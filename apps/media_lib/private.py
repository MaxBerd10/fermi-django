"""Private storage for what visitors send in (passport scans, CVs, ...).

Site documents are public on purpose: they live under /media/ and anyone with the link may open them. A visitor's
attachment must not: it is stored under PRIVATE_PREFIX, the public /media/ route refuses that prefix (see
config/urls.py), and the only way to open such a file is a short-lived signed link that the staff-only admin API
hands out. A link that leaks (browser history, a forwarded message, a log) stops working after
LINK_LIFETIME_SECONDS, and it never worked for anyone who did not get it from a signed-in staff member.
"""
import mimetypes
import os
import posixpath

from django.core import signing
from django.core.files.storage import default_storage
from django.http import FileResponse, Http404, HttpResponse
from django.urls import reverse
from django.views import View

PRIVATE_PREFIX = "uploads/private/"
LINK_SALT = "fermi.private-media"
LINK_LIFETIME_SECONDS = 15 * 60

# What a browser may show in the tab; anything else (Word, Excel) is offered as a download.
_INLINE_TYPES = {"application/pdf", "image/jpeg", "image/png"}


def is_private_path(path: str) -> bool:
    """True for a storage path inside the private area, however it is spelled (`..`, `//`, upper case)."""
    normalized = posixpath.normpath(str(path).replace("\\", "/")).lstrip("/").lower()
    return normalized == PRIVATE_PREFIX.rstrip("/") or normalized.startswith(PRIVATE_PREFIX)


def signed_private_url(storage_name: str, request=None) -> str:
    token = signing.dumps(storage_name, salt=LINK_SALT, compress=True)
    url = reverse("private-media", args=[token])
    return request.build_absolute_uri(url) if request else url


class PrivateFileView(View):
    """GET /api/v1/private-media/<token>/ -- serves the file the token was signed for, while it is still valid."""

    def get(self, request, token):
        try:
            name = signing.loads(token, salt=LINK_SALT, max_age=LINK_LIFETIME_SECONDS)
        except signing.SignatureExpired:
            return HttpResponse(
                "Havola muddati tugagan. Admin paneldagi sahifani yangilab, faylni qayta oching.",
                status=410,
                content_type="text/plain; charset=utf-8",
            )
        except signing.BadSignature:
            raise Http404
        if not isinstance(name, str) or not is_private_path(name) or not default_storage.exists(name):
            raise Http404
        content_type = mimetypes.guess_type(name)[0] or "application/octet-stream"
        response = FileResponse(
            default_storage.open(name, "rb"),
            content_type=content_type,
            as_attachment=content_type not in _INLINE_TYPES,
            filename=os.path.basename(name),
        )
        response["Cache-Control"] = "private, no-store"
        response["X-Content-Type-Options"] = "nosniff"
        response["Referrer-Policy"] = "no-referrer"
        return response
