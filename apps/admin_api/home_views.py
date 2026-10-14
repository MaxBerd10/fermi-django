"""admin/home-partners, home-projects, home-voices, home-facts, home-why -- the editable lists of the home page
(see apps.site_settings.models.HomeItem and entityConfigs.ts). One serializer for all five; each resource is the same
ViewSet narrowed to one `section`, so the editor form of a section only shows the fields that section uses."""
from django.db.models import Max
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.site_settings.models import HomeItem

from .common import AdminPagination, AdminSearchMixin, IsAdminStaff, resolve_or_create_image

TEXT_FIELDS = ("title", "subtitle", "text")


class AdminHomeItemSerializer(serializers.ModelSerializer):
    img = serializers.SerializerMethodField()
    hidden = serializers.SerializerMethodField()

    class Meta:
        model = HomeItem
        fields = [
            "id", "order", "hidden", "value", "url", "icon", "img",
            "title_uz", "title_ru", "title_en",
            "subtitle_uz", "subtitle_ru", "subtitle_en",
            "text_uz", "text_ru", "text_en",
        ]

    def get_hidden(self, obj):
        return 0 if obj.is_active else 1

    def get_img(self, obj):
        if obj.image:
            request = self.context.get("request")
            return request.build_absolute_uri(obj.image.file.url) if request else obj.image.file.url
        return obj.image_path or None

    def create(self, validated_data):
        return self._save(HomeItem(section=self.context["section"]), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        for field in TEXT_FIELDS:
            for lang in ("uz", "ru", "en"):
                name = f"{field}_{lang}"
                if name in data:
                    setattr(instance, name, str(data.get(name) or "").strip())
        for name in ("value", "url", "icon"):
            if name in data:
                setattr(instance, name, str(data.get(name) or "").strip())
        if "hidden" in data:
            instance.is_active = not int(data.get("hidden") or 0)
        order = data.get("order")
        if order not in (None, ""):
            instance.order = max(0, int(order))
        elif instance.pk is None:
            last = HomeItem.objects.filter(section=instance.section).aggregate(last=Max("order"))["last"]
            instance.order = (last or 0) + 1
        if "img" in data:
            img = str(data.get("img") or "").strip()
            if img.startswith("/images/"):  # a picture shipped with the site, not an upload
                instance.image, instance.image_path = None, img
            else:
                instance.image, instance.image_path = resolve_or_create_image(img), ""
        instance.save()
        return instance


def _viewset(section: str, search_fields: tuple[str, ...]):
    class AdminHomeItemViewSet(AdminSearchMixin, viewsets.ModelViewSet):
        permission_classes = [IsAuthenticated, IsAdminStaff]
        pagination_class = AdminPagination
        serializer_class = AdminHomeItemSerializer
        queryset = HomeItem.objects.filter(section=section).select_related("image").order_by("order", "id")

        def get_serializer_context(self):
            return {**super().get_serializer_context(), "section": section}

    AdminHomeItemViewSet.search_fields = search_fields
    AdminHomeItemViewSet.__name__ = f"AdminHome{section.title()}ViewSet"
    return AdminHomeItemViewSet


AdminHomePartnerViewSet = _viewset(HomeItem.PARTNER, ("title_uz", "title_ru", "title_en", "url"))
AdminHomeProjectViewSet = _viewset(HomeItem.PROJECT, ("title_uz", "title_ru", "title_en", "url"))
AdminHomeVoiceViewSet = _viewset(HomeItem.VOICE, ("title_uz", "title_ru", "title_en", "text_uz"))
AdminHomeFactViewSet = _viewset(HomeItem.FACT, ("title_uz", "title_ru", "title_en", "value"))
AdminHomeWhyViewSet = _viewset(HomeItem.WHY, ("title_uz", "title_ru", "title_en", "text_uz"))
