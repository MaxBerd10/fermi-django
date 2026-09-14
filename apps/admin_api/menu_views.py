"""admin/menu-tree -- MenuTreePage.tsx / api/adminMenu.ts::AdminMenuNode.

MenuItem (apps.menu.models) only ever had label_uz/ru/en + a flat `url`
string -- the old Yii2 url_type/url_value split was a routing scheme for
composing a href from a type+value pair, and this project's real
MenuSectionNav already reads the flat `url` directly (see this session's
earlier urlType-bug fix). There's nothing to compose here, so urlType/
status/active/disabled are accepted but inert, same convention as News's
seen/meta_key fields (see news_views.py's docstring): always read back as
a fixed "nothing happened" value. url_value is url_value only.
"""
from django.db import transaction
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.menu.models import MenuItem

from .common import IsAdminStaff


def _serialize_node(item: MenuItem, lvl: int = 0) -> dict:
    return {
        "id": item.id,
        "titleUz": item.label_uz,
        "titleRu": item.label_ru,
        "titleEn": item.label_en,
        "urlType": "other",
        "urlValue": item.url,
        "status": 1,
        "active": 1,
        "disabled": 0,
        "lvl": lvl,
        "children": [_serialize_node(child, lvl + 1) for child in item.children.all().order_by("order", "id")],
    }


class AdminMenuTreeView(APIView):
    permission_classes = [IsAuthenticated, IsAdminStaff]

    def get(self, request):
        roots = MenuItem.objects.filter(parent__isnull=True).order_by("order", "id")
        return Response([_serialize_node(root) for root in roots])

    def post(self, request):
        data = request.data
        title_uz = data.get("title_uz", "")
        parent_id = data.get("parentId")
        item = MenuItem.objects.create(
            parent_id=parent_id,
            label_uz=title_uz,
            label_ru=data.get("title_ru") or title_uz,
            label_en=data.get("title_en") or title_uz,
            url=data.get("url_value") or "",
            order=MenuItem.objects.filter(parent_id=parent_id).count(),
        )
        return Response(_serialize_node(item), status=status.HTTP_201_CREATED)


class AdminMenuNodeDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdminStaff]

    def put(self, request, pk):
        item = get_object_or_404(MenuItem, pk=pk)
        data = request.data
        item.label_uz = data.get("title_uz", item.label_uz)
        item.label_ru = data.get("title_ru") or item.label_uz
        item.label_en = data.get("title_en") or item.label_uz
        item.url = data.get("url_value", item.url) or ""
        item.save()
        return Response(_serialize_node(item))

    def delete(self, request, pk):
        item = get_object_or_404(MenuItem, pk=pk)
        item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class AdminMenuMoveView(APIView):
    permission_classes = [IsAuthenticated, IsAdminStaff]

    @transaction.atomic
    def post(self, request, pk):
        source = get_object_or_404(MenuItem, pk=pk)
        target = get_object_or_404(MenuItem, pk=request.data.get("targetId"))
        position = request.data.get("position")

        node = target
        while node is not None:
            if node.id == source.id:
                return Response({"detail": "Elementni o'zining ichiga ko'chirib bo'lmaydi."}, status=400)
            node = node.parent

        new_parent = target if position == "child" else target.parent
        siblings = list(MenuItem.objects.filter(parent=new_parent).exclude(id=source.id).order_by("order", "id"))
        if position == "before":
            insert_at = siblings.index(target)
        elif position == "after":
            insert_at = siblings.index(target) + 1
        else:
            insert_at = len(siblings)
        siblings.insert(insert_at, source)

        source.parent = new_parent
        for index, node in enumerate(siblings):
            node.order = index
        MenuItem.objects.bulk_update(siblings, ["order"])
        source.save(update_fields=["parent", "order"])
        return Response(status=status.HTTP_204_NO_CONTENT)
