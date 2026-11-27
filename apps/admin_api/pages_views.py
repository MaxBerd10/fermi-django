"""admin/pages -- see entityConfigs.ts is wrong here, Pages actually uses
its own bespoke PagesFormPage.tsx (types.ts::AdminPage), not a generic
EntityConfig. Manages apps.content.models.Page directly -- the same model
backing every legacy-imported static page, department, faculty, and news
post, but here as its own standalone CRUD resource (an admin-created page
has no MenuItem of its own, hence Page.title_* -- see that field's own
comment in models.py)."""
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404
from django.utils.text import slugify
from rest_framework import serializers, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.content.admin_content import EDITABLE_TYPES, blocks_to_html, write_blocks_from_html
from apps.content.models import ContentBlock, Page
from apps.content.raw_editing import is_raw_capable
from apps.media_lib.models import Document
from apps.menu.models import MenuItem

from .common import AdminSearchMixin, AdminPagination, IsAdminStaff


def menu_titles_by_slug() -> dict[str, str]:
    """slug -> the (Uzbek) label of the menu entry whose link ends in that slug; the first entry wins."""
    titles: dict[str, str] = {}
    for url, label in MenuItem.objects.exclude(url="").values_list("url", "label_uz"):
        slug = url.split("?", 1)[0].split("#", 1)[0].rstrip("/").rsplit("/", 1)[-1]
        if slug and slug not in titles:
            titles[slug] = label
    return titles


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
    menu_title = serializers.SerializerMethodField()
    raw_editing = serializers.SerializerMethodField()
    slug = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = Page
        fields = [
            "id", "title_uz", "title_ru", "title_en",
            "content_uz", "content_ru", "content_en",
            "slug", "layout", "file", "file_en", "file_ru", "date", "status", "korish", "meta_key",
            "menu_title", "raw_editing",
        ]

    def _content(self, obj, lang):
        return blocks_to_html(obj, lang, request=self.context.get("request"), open_raw=True)

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

    def get_raw_editing(self, obj):
        return is_raw_capable(obj)

    def get_menu_title(self, obj):
        # An imported page has no title of its own: it is the label of the menu entry that opens it.
        return menu_titles_by_slug().get(obj.slug)

    def create(self, validated_data):
        return self._save(Page(), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru", instance.title_ru or "")
        instance.title_en = data.get("title_en", instance.title_en or "")
        instance.layout = data.get("layout", instance.layout)
        try:
            instance.full_clean(exclude=["slug"])  # an unknown layout is a 400, not a silently wrong page
        except DjangoValidationError as error:
            raise serializers.ValidationError(error.message_dict)
        if not instance.slug:
            slug = (data.get("slug") or "").strip() or slugify(instance.title_uz or f"sahifa-{Page.objects.count() + 1}", allow_unicode=False)
            instance.slug = slug
        instance.save()
        try:
            write_blocks_from_html(instance, {
                "uz": data.get("content_uz") or "",
                "ru": data.get("content_ru") or "",
                "en": data.get("content_en") or "",
            }, open_raw=True)
        except DjangoValidationError as error:  # a refused block (a table with a short row, an unknown embed address ...) is a 400 with its reason, not a 500
            raise serializers.ValidationError({"content_uz": error.messages})
        return instance


class AdminPageViewSet(AdminSearchMixin, viewsets.ModelViewSet):
    search_fields = ('title_uz', 'title_ru', 'title_en', 'slug')
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

    def get_queryset(self):
        queryset = super().get_queryset()
        term = (self.request.query_params.get("search") or "").strip().lower()
        if term:
            # AdminSearchMixin already matched titles and slugs; an imported page is also found by its menu label.
            by_menu = [slug for slug, label in menu_titles_by_slug().items() if term in label.lower()]
            if by_menu:
                matched = Page.objects.filter(
                    department__isnull=True, faculty__isnull=True, news_post__isnull=True, slug__in=by_menu
                )
                queryset = (queryset | matched).distinct().order_by("-updated_at")
        return queryset

    @action(detail=True, methods=["get"], url_path=r"blocks/(?P<block_id>[0-9]+)")
    def block(self, request, pk=None, block_id=None):
        """The payload of one block of this page that the page editor has a form for (table, embed, document): what the form opens with."""
        page = self.get_object()
        found = ContentBlock.objects.filter(page=page, pk=block_id, block_type__in=EDITABLE_TYPES).first()
        if found is None:
            raise Http404
        body = {"id": found.pk, "block_type": found.block_type, "data": found.data}
        if found.block_type == "document":  # the form shows which file the card is for (it cannot be changed here)
            document = Document.objects.filter(pk=(found.data.get("uz") or {}).get("document_id")).first()
            body["document"] = {"title": document.title, "filename": document.file.name.rsplit("/", 1)[-1]} if document else None
        return Response(body)
