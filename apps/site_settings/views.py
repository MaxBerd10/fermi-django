from rest_framework.response import Response
from rest_framework.views import APIView

from .models import HomeItem, SiteCounter, SiteLogo, SiteSetting, SiteText, SocialNetwork, UsefulSite
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


def _lang3(item: HomeItem, field: str) -> dict[str, str]:
    """{"uz","ru","en"} of one text field; a language the editors left blank shows the Uzbek wording."""
    uz = getattr(item, f"{field}_uz")
    return {"uz": uz, "ru": getattr(item, f"{field}_ru") or uz, "en": getattr(item, f"{field}_en") or uz}


class HomeSectionsView(APIView):
    """GET /api/v1/home-sections -- the editable lists of the home page (partners, project cards, student quotes,
    headline figures, "why us" cards), only the active ones, in the editors' order. The frontend keeps its built-in
    copy of the same content only for the case that this request fails."""

    def get(self, request):
        # ?only=tools: just the top-section buttons (the Node server puts them into index.html, see production-server.mjs)
        only_tools = request.query_params.get("only") == "tools"
        sections: dict[str, list] = (
            {"tools": []}
            if only_tools
            else {"partners": [], "projects": [], "voices": [], "facts": [], "why": [], "tools": []}
        )
        items = HomeItem.objects.filter(is_active=True).select_related("image")
        if only_tools:
            items = items.filter(section=HomeItem.TOOL)
        for item in items:
            if item.section == HomeItem.TOOL:
                sections["tools"].append(
                    {
                        "id": item.pk,
                        "title": _lang3(item, "title"),
                        "desc": _lang3(item, "text"),
                        "url": item.url,
                        "icon": item.icon,
                        "accent": item.value == "accent",
                    }
                )
            elif item.section == HomeItem.PARTNER:
                sections["partners"].append(
                    {"id": item.pk, "name": _lang3(item, "title"), "url": item.url, "icon": item.icon}
                )
            elif item.section == HomeItem.PROJECT:
                if item.image:
                    img = request.build_absolute_uri(item.image.file.url)
                else:
                    img = item.image_path or None
                sections["projects"].append(
                    {"id": item.pk, "name": _lang3(item, "title"), "url": item.url or None, "icon": item.icon, "img": img}
                )
            elif item.section == HomeItem.VOICE:
                sections["voices"].append(
                    {"id": item.pk, "quote": _lang3(item, "text"), "name": _lang3(item, "title"), "meta": _lang3(item, "subtitle")}
                )
            elif item.section == HomeItem.FACT:
                sections["facts"].append({"id": item.pk, "value": item.value, "label": _lang3(item, "title")})
            elif item.section == HomeItem.WHY:
                sections["why"].append(
                    {
                        "id": item.pk,
                        "title": _lang3(item, "title"),
                        "desc": _lang3(item, "text"),
                        "metric": item.value,
                        "metricLabel": _lang3(item, "subtitle"),
                    }
                )
        return Response(sections)
