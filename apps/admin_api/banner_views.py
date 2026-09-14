"""admin/corusel -- entityConfigs.ts's coruselConfig ("Bosh sahifa
banneri"). No public page currently renders HomeBanner rows (see the
model's own docstring); the admin CRUD is still real and persists to a
real table, just without a consumer yet."""
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.site_settings.models import HomeBanner

from .common import AdminPagination, IsAdminStaff, resolve_or_create_image


class AdminBannerSerializer(serializers.ModelSerializer):
    img = serializers.SerializerMethodField()

    class Meta:
        model = HomeBanner
        fields = ["id", "title_uz", "title_ru", "title_en", "content_uz", "content_ru", "content_en", "status", "img"]

    def get_img(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.file.url) if request else obj.image.file.url

    def create(self, validated_data):
        return self._save(HomeBanner(order=HomeBanner.objects.count()), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru") or instance.title_uz
        instance.title_en = data.get("title_en") or instance.title_uz
        instance.content_uz = data.get("content_uz", instance.content_uz or "")
        instance.content_ru = data.get("content_ru") or instance.content_uz
        instance.content_en = data.get("content_en") or instance.content_uz
        instance.status = int(data.get("status", instance.status))
        instance.image = resolve_or_create_image(data.get("img"))
        instance.save()
        return instance


class AdminBannerViewSet(viewsets.ModelViewSet):
    queryset = HomeBanner.objects.select_related("image").order_by("order", "id")
    serializer_class = AdminBannerSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
