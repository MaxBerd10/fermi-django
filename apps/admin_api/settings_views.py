"""admin/setting, admin/logo, admin/counter (singletons -- see
SingletonAdminViewSet) + admin/networks, admin/useful-sites (plain lists).
See entityConfigs.ts's settingConfig/logoConfig/counterConfig/
networkConfig/usefulSitesConfig."""
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.site_settings.models import SiteCounter, SiteLogo, SiteSetting, SocialNetwork, UsefulSite

from .common import AdminPagination, IsAdminStaff, SingletonAdminViewSet, resolve_or_create_image


class AdminSettingSerializer(serializers.ModelSerializer):
    address_uz = serializers.CharField(required=False, allow_blank=True)
    address_ru = serializers.CharField(required=False, allow_blank=True)
    address_en = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = SiteSetting
        fields = ["id", "phone", "faks", "email", "address_uz", "address_ru", "address_en"]


class AdminSettingViewSet(SingletonAdminViewSet, viewsets.ModelViewSet):
    model = SiteSetting
    serializer_class = AdminSettingSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminLogoSerializer(serializers.ModelSerializer):
    img = serializers.SerializerMethodField()

    class Meta:
        model = SiteLogo
        fields = ["id", "img", "title_uz", "title_ru", "title_en", "subtitle_uz", "subtitle_ru", "subtitle_en"]

    def get_img(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.file.url) if request else obj.image.file.url

    def update(self, instance, validated_data):
        data = self.context["request"].data
        for field in ("title_uz", "title_ru", "title_en", "subtitle_uz", "subtitle_ru", "subtitle_en"):
            setattr(instance, field, data.get(field, getattr(instance, field) or ""))
        image = resolve_or_create_image(data.get("img"))
        if image is not None:
            instance.image = image
        instance.save()
        return instance


class AdminLogoViewSet(SingletonAdminViewSet, viewsets.ModelViewSet):
    model = SiteLogo
    serializer_class = AdminLogoSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminCounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteCounter
        fields = ["id", "professor_teachers", "students", "graduaters", "book_fund"]


class AdminCounterViewSet(SingletonAdminViewSet, viewsets.ModelViewSet):
    model = SiteCounter
    serializer_class = AdminCounterSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminNetworkSerializer(serializers.ModelSerializer):
    titlte = serializers.CharField(source="title")  # matches entityConfigs.ts's own typo, see networkConfig
    status = serializers.SerializerMethodField()

    class Meta:
        model = SocialNetwork
        fields = ["id", "titlte", "icon", "url", "status"]

    def get_status(self, obj):
        return 1


class AdminNetworkViewSet(viewsets.ModelViewSet):
    queryset = SocialNetwork.objects.order_by("order", "id")
    serializer_class = AdminNetworkSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminUsefulSiteSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()

    class Meta:
        model = UsefulSite
        fields = ["id", "title_uz", "title_ru", "title_en", "img", "url", "status"]

    def get_status(self, obj):
        return 1

    def get_img(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.file.url) if request else obj.image.file.url

    def create(self, validated_data):
        return self._save(UsefulSite(), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru") or instance.title_uz
        instance.title_en = data.get("title_en") or instance.title_uz
        instance.url = data.get("url", instance.url or "")
        image = resolve_or_create_image(data.get("img"))
        if image is not None:
            instance.image = image
        instance.save()
        return instance


class AdminUsefulSiteViewSet(viewsets.ModelViewSet):
    queryset = UsefulSite.objects.select_related("image").order_by("order", "id")
    serializer_class = AdminUsefulSiteSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
