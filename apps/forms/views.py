from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.media_lib.models import Document

from .serializers import AcceptanceSubmissionSerializer, ContactSubmissionSerializer, VirtualSubmissionSerializer


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
            # Whatever the visitor attaches (a scanned document, a photo of
            # a passport page, ...) -- not run through Document's own
            # pdf/xlsx-only validator (see media_lib/models.py), which is
            # scoped to the documents the SITE publishes, not arbitrary
            # visitor uploads.
            document = Document(title=upload.name)
            document.file.save(upload.name, upload, save=False)
            document.save()
            instance.file = document
            instance.save(update_fields=["file"])

        return Response({"submitted": True, "id": instance.id})
