"""admin/news + admin/postcategories -- see frontend/src/admin/pages/news/*
and admin/types.ts::AdminPost/AdminPostcategory for the exact contract.

A few AdminPost fields have no real backing model yet and are accepted but
inert here rather than faking persistence: `status` (no draft/published
concept on NewsPost -- every post is always live), `seen` (no view
counter), `meta_key`, and the per-language `file`/`file_en`/`file_ru`
attachments. Each always reads back as its "nothing happened" value (1, 0,
None) regardless of what was last written. Real support for any of these
is a model change, not an API-layer one -- left for when it's actually
wanted rather than guessed at now.
"""
from django.utils.text import slugify
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.content.admin_content import blocks_to_html, write_blocks_from_html
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image
from apps.news.models import NewsCategory, NewsPost

from .common import AdminPagination, IsAdminStaff, OwnedPageCleanupMixin, resolve_or_create_image


class AdminPostcategorySerializer(serializers.ModelSerializer):
    title_uz = serializers.CharField(source="name_uz")
    title_ru = serializers.CharField(source="name_ru", required=False, allow_blank=True)
    title_en = serializers.CharField(source="name_en", required=False, allow_blank=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = NewsCategory
        fields = ["id", "title_uz", "title_ru", "title_en", "slug", "status"]

    def get_status(self, obj):
        return 1


class AdminPostcategoryViewSet(viewsets.ModelViewSet):
    queryset = NewsCategory.objects.all().order_by("name_uz")
    serializer_class = AdminPostcategorySerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminPostSerializer(serializers.ModelSerializer):
    title_uz = serializers.CharField()
    title_ru = serializers.CharField(required=False, allow_blank=True)
    title_en = serializers.CharField(required=False, allow_blank=True)
    slug = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    content_uz = serializers.SerializerMethodField()
    content_ru = serializers.SerializerMethodField()
    content_en = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    seen = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()
    gallery = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    file_en = serializers.SerializerMethodField()
    file_ru = serializers.SerializerMethodField()
    meta_key = serializers.SerializerMethodField()

    class Meta:
        model = NewsPost
        fields = [
            "id", "title_uz", "title_ru", "title_en",
            "content_uz", "content_ru", "content_en",
            "category_id", "date", "seen", "slug", "status",
            "img", "gallery", "file", "file_en", "file_ru", "meta_key",
        ]

    def _content(self, obj, lang):
        request = self.context.get("request")
        return blocks_to_html(obj.page, lang, request=request)

    def get_content_uz(self, obj):
        return self._content(obj, "uz")

    def get_content_ru(self, obj):
        return self._content(obj, "ru")

    def get_content_en(self, obj):
        return self._content(obj, "en")

    def get_date(self, obj):
        return obj.published_at.isoformat() if obj.published_at else None

    def get_seen(self, obj):
        return 0

    def get_status(self, obj):
        return 1

    def get_img(self, obj):
        if not obj.cover:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.cover.file.url) if request else obj.cover.file.url

    def get_gallery(self, obj):
        """The post's extra photos, as absolute URLs in display order --
        stored as one trailing `gallery` ContentBlock on its page (the
        public BlockRenderer already renders that block type), so no
        model change was needed to support more than the single cover."""
        request = self.context.get("request")
        image_ids = _gallery_image_ids(obj.page) if obj.page_id else []
        images = Image.objects.in_bulk(image_ids)
        urls = []
        for image_id in image_ids:
            image = images.get(image_id)
            if image:
                urls.append(request.build_absolute_uri(image.file.url) if request else image.file.url)
        return urls

    def get_file(self, obj):
        return None

    def get_file_en(self, obj):
        return None

    def get_file_ru(self, obj):
        return None

    def get_meta_key(self, obj):
        return None

    def create(self, validated_data):
        instance = self._save(NewsPost(), validated_data)
        return instance

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        request = self.context["request"]
        data = request.data

        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru", instance.title_ru or "") or instance.title_uz
        instance.title_en = data.get("title_en", instance.title_en or "") or instance.title_uz

        slug = (data.get("slug") or "").strip() or slugify(instance.title_uz, allow_unicode=False)
        instance.slug = slug

        excerpt_source = data.get("content_uz") or ""
        # A plain, tag-stripped preview -- same as any list/card view of a
        # NewsPost needs (see NewsPostListSerializer.excerpt), truncated the
        # same way the public API's own excerpt fields already are.
        from django.utils.html import strip_tags
        plain = strip_tags(excerpt_source).strip()
        instance.excerpt_uz = plain[:500]
        instance.excerpt_ru = strip_tags(data.get("content_ru") or "").strip()[:500] or instance.excerpt_uz
        instance.excerpt_en = strip_tags(data.get("content_en") or "").strip()[:500] or instance.excerpt_uz

        category_id = data.get("category_id")
        instance.category_id = category_id or None

        image = resolve_or_create_image(data.get("img"))
        instance.cover = image

        if not instance.published_at:
            from django.utils import timezone
            instance.published_at = timezone.now()

        if not instance.page_id:
            instance.page = Page.objects.create(slug=f"news-{slug}")
        instance.save()

        # write_blocks_from_html replaces every block on the page, gallery
        # included -- keep the existing photos when a client didn't send the
        # field at all, rather than silently dropping them.
        if "gallery" in data:
            gallery_ids = [
                image.id
                for image in (resolve_or_create_image(path) for path in (data.get("gallery") or []) if path)
                if image
            ]
        else:
            gallery_ids = _gallery_image_ids(instance.page)

        write_blocks_from_html(instance.page, {
            "uz": data.get("content_uz") or "",
            "ru": data.get("content_ru") or "",
            "en": data.get("content_en") or "",
        })
        _append_gallery_block(instance.page, gallery_ids)
        return instance


def _gallery_image_ids(page: Page) -> list[int]:
    block = page.blocks.filter(block_type=ContentBlock.BlockType.GALLERY).first()
    if not block:
        return []
    items = (block.data.get("uz") or {}).get("items", [])
    return [item["image_id"] for item in items if isinstance(item.get("image_id"), int)]


def _append_gallery_block(page: Page, image_ids: list[int]) -> None:
    if not image_ids:
        return
    last = page.blocks.order_by("-order").first()
    payload = {"items": [{"image_id": image_id, "alt": ""} for image_id in image_ids]}
    block = ContentBlock(
        page=page,
        order=(last.order + 1) if last else 1,
        block_type=ContentBlock.BlockType.GALLERY,
        data={"uz": payload, "ru": payload, "en": payload},
    )
    block.full_clean()
    block.save()


class AdminPostViewSet(OwnedPageCleanupMixin, viewsets.ModelViewSet):
    queryset = NewsPost.objects.select_related("cover", "page").order_by("-published_at")
    serializer_class = AdminPostSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
