"""admin/site-texts -- edit any interface text (button, heading, footer line, home-page paragraph) in all three
languages. The wording built into the frontend stays the default; a row here overrides it per language, and removing
the row (or blanking all three languages) restores the defaults. See apps.site_settings.models.SiteText."""
import re

from rest_framework import serializers
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.site_settings.models import SiteText

from .common import IsAdminStaff

KEY_RE = re.compile(r"^[A-Za-z0-9_.\-]{1,120}$")
MAX_TEXT_LENGTH = 3000


class SiteTextSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteText
        fields = ["key", "text_uz", "text_ru", "text_en", "updated_at"]


class AdminSiteTextsView(APIView):
    permission_classes = [IsAuthenticated, IsAdminStaff]

    def get(self, request):
        return Response(SiteTextSerializer(SiteText.objects.all(), many=True).data)

    def put(self, request):
        key = str(request.data.get("key") or "").strip()
        if not KEY_RE.match(key):
            return Response({"key": ["Kalit noto'g'ri."]}, status=400)
        texts = {}
        for lang in ("uz", "ru", "en"):
            value = str(request.data.get(f"text_{lang}") or "").replace("\r\n", "\n").strip()
            if len(value) > MAX_TEXT_LENGTH:
                return Response({f"text_{lang}": [f"Matn {MAX_TEXT_LENGTH} belgidan oshmasligi kerak."]}, status=400)
            texts[f"text_{lang}"] = value
        if not any(texts.values()):
            SiteText.objects.filter(key=key).delete()  # nothing left to override: back to the built-in wording
            return Response({"key": key, "deleted": True})
        row, _ = SiteText.objects.update_or_create(key=key, defaults=texts)
        return Response(SiteTextSerializer(row).data)
