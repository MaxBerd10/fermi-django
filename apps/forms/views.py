import logging
import uuid

from django.db import transaction
from rest_framework import status
from rest_framework.exceptions import APIException
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.media_lib.models import Document

from .serializers import (
    AcceptanceSubmissionSerializer,
    ContactSubmissionSerializer,
    ContestSubmissionSerializer,
    VirtualSubmissionSerializer,
)


# Visitor attachments are stored under the same public /media/ origin as site
# documents.  Do not accept browser-executable formats (HTML/SVG/JS) there,
# even if a client lies about its MIME type.  This is intentionally limited to
# the formats a visitor realistically attaches to a reception request.
MAX_VISITOR_UPLOAD_BYTES = 10 * 1024 * 1024
VISITOR_UPLOAD_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".doc", ".docx", ".xls", ".xlsx"}


def validate_visitor_upload(upload):
    name = str(getattr(upload, "name", ""))
    suffix = name.rsplit(".", 1)[-1].lower() if "." in name else ""
    if f".{suffix}" not in VISITOR_UPLOAD_EXTENSIONS:
        raise ValidationError({"file": "Faqat PDF, JPG, PNG, DOC/DOCX yoki XLS/XLSX fayl yuklash mumkin."})
    if upload.size > MAX_VISITOR_UPLOAD_BYTES:
        raise ValidationError({"file": "Fayl hajmi 10 MB dan oshmasligi kerak."})


logger = logging.getLogger(__name__)


class AttachmentStorageError(APIException):
    status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    default_detail = "Faylni saqlab bo'lmadi. Iltimos, birozdan so'ng arizani qayta yuboring."
    default_code = "attachment_storage_failed"


def _save_with_attachment(serializer, upload):
    """Saves the submission and its attachment as ONE unit. The row used to be saved first and the file after,
    so when the disk refused the file (a new month's upload folder owned by the wrong user, a full disk) the
    visitor got a bare 500 while their name/phone stayed behind with no document -- and their retry made a
    duplicate. Now the whole thing rolls back and the visitor gets a clear, retryable message."""
    try:
        with transaction.atomic():
            instance = serializer.save()
            if upload:
                # Whatever the visitor attaches (a scanned document, a photo of a passport page, ...) is
                # restricted by validate_visitor_upload rather than through Document's pdf/xlsx-only
                # validator, which is scoped to files the SITE itself publishes.
                document = Document(title=upload.name)
                document.file.save(_private_upload_name(upload.name), upload, save=False)
                document.save()
                instance.file = document
                instance.save(update_fields=["file"])
    except OSError:
        logger.exception("Could not store a visitor attachment")
        raise AttachmentStorageError()
    return instance


def _private_upload_name(filename: str) -> str:
    """A visitor's attachment (CV, passport scan, ...) is served from the same
    public /media/ origin as site documents, so its URL is its only protection.
    A random directory makes that URL unguessable -- without it the path was just
    uploads/documents/<year>/<month>/<original filename>, trivially enumerable."""
    return f"{uuid.uuid4().hex}/{filename}"


class ContactFormView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_form"

    def post(self, request):
        serializer = ContactSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


class QabulFormView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_form"

    def post(self, request):
        serializer = AcceptanceSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()
        return Response({"submitted": True, "id": instance.id})


class ContestFormView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_form"
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = ContestSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Validate the attachment BEFORE anything is saved -- a rejected file
        # used to leave the submission row behind (minus its file) while the
        # visitor saw an error, so their retry then created a duplicate.
        upload = request.FILES.get("file")
        if upload:
            validate_visitor_upload(upload)
        instance = _save_with_attachment(serializer, upload)

        return Response({"submitted": True, "id": instance.id})


class VirtualReceptionFormView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_form"
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = VirtualSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        # Validated before saving -- see ContestFormView.
        upload = request.FILES.get("file")
        if upload:
            validate_visitor_upload(upload)
        instance = _save_with_attachment(serializer, upload)

        return Response({"submitted": True, "id": instance.id})
