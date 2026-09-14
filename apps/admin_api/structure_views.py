"""admin/faculty + admin/departments -- see entityConfigs.ts's
facultyConfig/departmentsConfig. Both are simple title+image+body
resources (no per-language file, view counter, or SEO fields like News
has), so their serializers are noticeably shorter."""
from django.utils.text import slugify
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.content.models import Page
from apps.departments.models import Department
from apps.faculties.models import Faculty

from .common import (
    AdminPagination,
    IsAdminStaff,
    OwnedPageCleanupMixin,
    PageContentSerializerMixin,
    resolve_or_create_image,
)


class AdminFacultySerializer(PageContentSerializerMixin, serializers.ModelSerializer):
    title_uz = serializers.CharField(source="name_uz")
    title_ru = serializers.CharField(source="name_ru", required=False, allow_blank=True)
    title_en = serializers.CharField(source="name_en", required=False, allow_blank=True)
    content_uz = serializers.SerializerMethodField()
    content_ru = serializers.SerializerMethodField()
    content_en = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()

    class Meta:
        model = Faculty
        fields = ["id", "title_uz", "title_ru", "title_en", "content_uz", "content_ru", "content_en", "status", "img"]

    def get_status(self, obj):
        return 1

    def get_img(self, obj):
        if not obj.logo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.logo.file.url) if request else obj.logo.file.url

    def create(self, validated_data):
        return self._save(Faculty(), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.name_uz = data.get("title_uz", instance.name_uz or "")
        instance.name_ru = data.get("title_ru") or instance.name_uz
        instance.name_en = data.get("title_en") or instance.name_uz
        if not instance.slug:
            instance.slug = slugify(instance.name_uz, allow_unicode=False)
        instance.logo = resolve_or_create_image(data.get("img"))
        if not instance.page_id:
            instance.page = Page.objects.create(slug=f"faculty-admin-{instance.slug}")
        instance.save()
        self.save_page_content(instance.page)
        return instance


class AdminFacultyViewSet(OwnedPageCleanupMixin, viewsets.ModelViewSet):
    queryset = Faculty.objects.select_related("logo", "page").order_by("order", "id")
    serializer_class = AdminFacultySerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminDepartmentSerializer(PageContentSerializerMixin, serializers.ModelSerializer):
    title_uz = serializers.CharField(source="name_uz")
    title_ru = serializers.CharField(source="name_ru", required=False, allow_blank=True)
    title_en = serializers.CharField(source="name_en", required=False, allow_blank=True)
    content_uz = serializers.SerializerMethodField()
    content_ru = serializers.SerializerMethodField()
    content_en = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "title_uz", "title_ru", "title_en", "content_uz", "content_ru", "content_en", "status", "img"]

    def get_status(self, obj):
        return 1

    def get_img(self, obj):
        if not obj.logo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.logo.file.url) if request else obj.logo.file.url

    def create(self, validated_data):
        return self._save(Department(), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.name_uz = data.get("title_uz", instance.name_uz or "")
        instance.name_ru = data.get("title_ru") or instance.name_uz
        instance.name_en = data.get("title_en") or instance.name_uz
        if not instance.slug:
            instance.slug = slugify(instance.name_uz, allow_unicode=False)
        instance.logo = resolve_or_create_image(data.get("img"))
        if not instance.page_id:
            instance.page = Page.objects.create(slug=f"department-admin-{instance.slug}")
        instance.save()
        self.save_page_content(instance.page)
        return instance


class AdminDepartmentViewSet(OwnedPageCleanupMixin, viewsets.ModelViewSet):
    queryset = Department.objects.select_related("logo", "page").order_by("name_uz")
    serializer_class = AdminDepartmentSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
