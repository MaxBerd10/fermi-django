"""admin/documents + admin/documents-items -- see entityConfigs.ts's
documentsConfig/documentsitemConfig. Unlike News/Pages/Faculty/
Department, DocumentItem stores its body as plain content_uz/ru/en
TextFields directly (see apps.documents.models's own docstring: "Short,
uniform fields per language... not long-form prose that would need
ContentBlock's grow-with-content layout") -- so no HTML<->blocks bridging
is needed here at all, a direct field mapping is already the right shape.
"""
from django.utils.text import slugify
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.documents.models import Document, DocumentItem

from .common import AdminPagination, IsAdminStaff


class AdminDocumentSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    slug = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Document
        fields = ["id", "title_uz", "title_ru", "title_en", "slug", "status"]

    def get_status(self, obj):
        return 1

    def create(self, validated_data):
        return self._save(Document(), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru") or instance.title_uz
        instance.title_en = data.get("title_en") or instance.title_uz
        if not instance.slug:
            instance.slug = slugify(instance.title_uz, allow_unicode=False)
        instance.save()
        return instance


class AdminDocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.order_by("title_uz")
    serializer_class = AdminDocumentSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminDocumentItemSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    slug = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = DocumentItem
        fields = [
            "id", "document_id", "title_uz", "title_ru", "title_en", "slug",
            "content_uz", "content_ru", "content_en", "status",
        ]

    def get_status(self, obj):
        return 1

    def create(self, validated_data):
        return self._save(DocumentItem(), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.document_id = data.get("document_id") or instance.document_id
        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru") or instance.title_uz
        instance.title_en = data.get("title_en") or instance.title_uz
        instance.content_uz = data.get("content_uz", instance.content_uz or "")
        instance.content_ru = data.get("content_ru", instance.content_ru or "")
        instance.content_en = data.get("content_en", instance.content_en or "")
        if not instance.slug:
            instance.slug = slugify(instance.title_uz, allow_unicode=False)
        instance.save()
        return instance


class AdminDocumentItemViewSet(viewsets.ModelViewSet):
    queryset = DocumentItem.objects.select_related("document").order_by("order", "id")
    serializer_class = AdminDocumentItemSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
