from rest_framework import serializers

from .models import SiteCounter, SiteLogo, SiteSetting, SocialNetwork, UsefulSite


class SettingSerializer(serializers.Serializer):
    phone = serializers.CharField()
    email = serializers.CharField()
    faks = serializers.CharField(allow_null=True)
    address = serializers.SerializerMethodField()

    def get_address(self, obj: SiteSetting):
        return {"uz": obj.address_uz, "ru": obj.address_ru, "en": obj.address_en}


class LogoSerializer(serializers.Serializer):
    img = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()
    subtitle = serializers.SerializerMethodField()

    def get_img(self, obj: SiteLogo):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.file.url) if request else obj.image.file.url

    def get_title(self, obj: SiteLogo):
        return {"uz": obj.title_uz, "ru": obj.title_ru, "en": obj.title_en}

    def get_subtitle(self, obj: SiteLogo):
        return {"uz": obj.subtitle_uz, "ru": obj.subtitle_ru, "en": obj.subtitle_en}


class NetworkSerializer(serializers.ModelSerializer):
    class Meta:
        model = SocialNetwork
        fields = ["title", "icon", "url"]


class UsefulSiteSerializer(serializers.Serializer):
    title = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()
    url = serializers.CharField()

    def get_title(self, obj: UsefulSite):
        return {"uz": obj.title_uz, "ru": obj.title_ru, "en": obj.title_en}

    def get_img(self, obj: UsefulSite):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.file.url) if request else obj.image.file.url


class CounterSerializer(serializers.ModelSerializer):
    class Meta:
        model = SiteCounter
        fields = ["professor_teachers", "students", "graduaters", "book_fund"]
