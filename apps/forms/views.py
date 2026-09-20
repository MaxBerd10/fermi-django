from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.media_lib.models import Document

from .serializers import AcceptanceSubmissionSerializer, ContactSubmissionSerializer, VirtualSubmissionSerializer


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


class VirtualReceptionFormView(APIView):
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "public_form"
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = VirtualSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        instance = serializer.save()

        upload = request.FILES.get("file")
        if upload:
            validate_visitor_upload(upload)
            # Whatever the visitor attaches (a scanned document, a photo of
            # a passport page, ...) is restricted above rather than through
            # Document's pdf/xlsx-only validator, which is scoped to files
            # the SITE itself publishes.
            document = Document(title=upload.name)
            document.file.save(upload.name, upload, save=False)
            document.save()
            instance.file = document
            instance.save(update_fields=["file"])

        return Response({"submitted": True, "id": instance.id})
