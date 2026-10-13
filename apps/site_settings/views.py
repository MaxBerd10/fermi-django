from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SiteCounter, SiteLogo, SiteSetting, SiteText, SocialNetwork, UsefulSite
from .serializers import (
    CounterSerializer,
    LogoSerializer,
    NetworkSerializer,
    SettingSerializer,
    UsefulSiteSerializer,
)


class SiteSettingsView(APIView):
    """GET /api/v1/settings -- matches frontend/src/types/content.ts's
    SiteSettings exactly, replacing the EMPTY_SETTINGS stub api/settings.ts
    used to always return (there was no Django model for any of this at
    all before -- see that file's own former comment)."""

    def get(self, request):
        setting = SiteSetting.get_solo()
        logo = SiteLogo.get_solo()
        counter = SiteCounter.get_solo()
        networks = SocialNetwork.objects.all()
        useful_sites = UsefulSite.objects.select_related("image").all()

        ctx = {"request": request}
        return Response({
            "setting": SettingSerializer(setting, context=ctx).data,
            "logo": LogoSerializer(logo, context=ctx).data,
            "networks": NetworkSerializer(networks, many=True, context=ctx).data,
            "usefulSites": UsefulSiteSerializer(useful_sites, many=True, context=ctx).data,
            "counter": CounterSerializer(counter, context=ctx).data,
        })


class SiteTextsView(APIView):
    """GET /api/v1/site-texts -- the admin-edited interface texts, {"uz": {key: text}, "ru": {...}, "en": {...}}, only
    the non-blank ones. The frontend lays them over its built-in wording (see src/i18n/index.ts); the Node server also
    puts this very JSON into index.html so a page opens with the edited texts and no extra request."""

    def get(self, request):
        texts: dict[str, dict[str, str]] = {"uz": {}, "ru": {}, "en": {}}
        for key, uz, ru, en in SiteText.objects.values_list("key", "text_uz", "text_ru", "text_en"):
            for lang, value in (("uz", uz), ("ru", ru), ("en", en)):
                if value.strip():
                    texts[lang][key] = value
        return Response(texts)
