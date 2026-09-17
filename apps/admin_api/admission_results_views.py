"""admin/result-categories, admin/result-files, admin/results-page --
mirrors admin/courses + admin/schedules exactly (see media_content_views.py's
AdminCourseViewSet/AdminScheduleFileViewSet): a document library grouped by
category, plus one singleton page heading/announcement."""
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.admission_results.models import ResultCategory, ResultFile, ResultsPage

from .common import AdminPagination, IsAdminStaff, SingletonAdminViewSet, resolve_or_create_document


class AdminResultCategorySerializer(serializers.ModelSerializer):
    title_uz = serializers.CharField()
    title_ru = serializers.CharField(required=False, allow_blank=True)
    title_en = serializers.CharField(required=False, allow_blank=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = ResultCategory
        fields = ["id", "title_uz", "title_ru", "title_en", "status"]

    def get_status(self, obj):
        return 1

    def create(self, validated_data):
        return self._save(ResultCategory())

    def update(self, instance, validated_data):
        return self._save(instance)

    def _save(self, instance):
        data = self.context["request"].data
        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru") or instance.title_uz
        instance.title_en = data.get("title_en") or instance.title_uz
        instance.save()
        return instance


class AdminResultCategoryViewSet(viewsets.ModelViewSet):
    queryset = ResultCategory.objects.order_by("order", "id")
    serializer_class = AdminResultCategorySerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminResultFileSerializer(serializers.ModelSerializer):
    title_uz = serializers.CharField()
    title_ru = serializers.CharField(required=False, allow_blank=True)
    title_en = serializers.CharField(required=False, allow_blank=True)
    category_id = serializers.IntegerField()
    status = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()

    class Meta:
        model = ResultFile
        fields = ["id", "title_uz", "title_ru", "title_en", "category_id", "status", "file"]

    def get_status(self, obj):
        return 1

    def get_file(self, obj):
        if not obj.document:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.document.file.url) if request else obj.document.file.url

    def create(self, validated_data):
        return self._save(ResultFile())

    def update(self, instance, validated_data):
        return self._save(instance)

    def _save(self, instance):
        data = self.context["request"].data
        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru") or instance.title_uz
        instance.title_en = data.get("title_en") or instance.title_uz
        instance.category_id = data.get("category_id") or instance.category_id
        document = resolve_or_create_document(data.get("file"))
        if document:
            instance.document = document
        instance.save()
        return instance


class AdminResultFileViewSet(viewsets.ModelViewSet):
    queryset = ResultFile.objects.select_related("category", "document").order_by("order", "id")
    serializer_class = AdminResultFileSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminResultsPageSerializer(serializers.ModelSerializer):
    heading_ru = serializers.CharField(required=False, allow_blank=True)
    heading_en = serializers.CharField(required=False, allow_blank=True)
    intro_ru = serializers.CharField(required=False, allow_blank=True)
    intro_en = serializers.CharField(required=False, allow_blank=True)
    announcement_ru = serializers.CharField(required=False, allow_blank=True)
    announcement_en = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = ResultsPage
        fields = [
            "id",
            "heading_uz", "heading_ru", "heading_en",
            "intro_uz", "intro_ru", "intro_en",
            "announcement_uz", "announcement_ru", "announcement_en",
        ]

    def update(self, instance, validated_data):
        # A blank ru/en falls back to the uz text rather than rendering empty
        # for RU/EN visitors -- same convention as every other admin
        # resource's _save() (see e.g. AdminBannerSerializer), which this
        # singleton serializer skipped by just being a plain ModelSerializer.
        for base in ("heading", "intro", "announcement"):
            uz_val = validated_data.get(f"{base}_uz", getattr(instance, f"{base}_uz"))
            for lang in ("ru", "en"):
                key = f"{base}_{lang}"
                if not validated_data.get(key):
                    validated_data[key] = uz_val
        return super().update(instance, validated_data)


class AdminResultsPageViewSet(SingletonAdminViewSet, viewsets.ModelViewSet):
    model = ResultsPage
    serializer_class = AdminResultsPageSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
