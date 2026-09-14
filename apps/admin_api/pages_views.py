"""admin/pages -- see entityConfigs.ts is wrong here, Pages actually uses
its own bespoke PagesFormPage.tsx (types.ts::AdminPage), not a generic
EntityConfig. Manages apps.content.models.Page directly -- the same model
backing every legacy-imported static page, department, faculty, and news
post, but here as its own standalone CRUD resource (an admin-created page
has no MenuItem of its own, hence Page.title_* -- see that field's own
comment in models.py)."""
from django.utils.text import slugify
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.content.admin_content import blocks_to_html, write_blocks_from_html
from apps.content.models import Page

from .common import AdminPagination, IsAdminStaff


class AdminPageSerializer(serializers.ModelSerializer):
    content_uz = serializers.SerializerMethodField()
    content_ru = serializers.SerializerMethodField()
    content_en = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    korish = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    file_en = serializers.SerializerMethodField()
    file_ru = serializers.SerializerMethodField()
    meta_key = serializers.SerializerMethodField()
    slug = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Page
        fields = [
            "id", "title_uz", "title_ru", "title_en",
            "content_uz", "content_ru", "content_en",
            "slug", "file", "file_en", "file_ru", "date", "status", "korish", "meta_key",
        ]

    def _content(self, obj, lang):
        return blocks_to_html(obj, lang, request=self.context.get("request"))

    def get_content_uz(self, obj):
        return self._content(obj, "uz")

    def get_content_ru(self, obj):
        return self._content(obj, "ru")

    def get_content_en(self, obj):
        return self._content(obj, "en")

    def get_date(self, obj):
        return obj.updated_at.isoformat() if obj.updated_at else None

    def get_status(self, obj):
        return 1

    def get_korish(self, obj):
        return 0

    def get_file(self, obj):
        return None

    def get_file_en(self, obj):
        return None

    def get_file_ru(self, obj):
        return None

    def get_meta_key(self, obj):
        return None

    def create(self, validated_data):
        return self._save(Page(), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru", instance.title_ru or "")
        instance.title_en = data.get("title_en", instance.title_en or "")
        if not instance.slug:
            slug = (data.get("slug") or "").strip() or slugify(instance.title_uz or f"sahifa-{Page.objects.count() + 1}", allow_unicode=False)
            instance.slug = slug
        instance.save()
        write_blocks_from_html(instance, {
            "uz": data.get("content_uz") or "",
            "ru": data.get("content_ru") or "",
            "en": data.get("content_en") or "",
        })
        return instance


class AdminPageViewSet(viewsets.ModelViewSet):
    # Page is shared infrastructure (a department's body, a faculty's,
    # a news post's, ... all point one at a page instead of storing raw
    # HTML themselves -- see Page's own docstring) -- "Sahifalar" in the
    # admin panel means the standalone static pages specifically (the
    # ~235 imported ones, or a fresh admin-authored one), not every page
    # underneath every other resource, so those are excluded here.
    queryset = Page.objects.filter(
        department__isnull=True, faculty__isnull=True, news_post__isnull=True,
    ).order_by("-updated_at")
    serializer_class = AdminPageSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
