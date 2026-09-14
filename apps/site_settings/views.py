from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SiteCounter, SiteLogo, SiteSetting, SocialNetwork, UsefulSite
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
