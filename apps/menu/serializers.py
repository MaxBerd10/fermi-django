from rest_framework import serializers

from .models import MenuItem


class MenuItemSerializer(serializers.ModelSerializer):
    label = serializers.SerializerMethodField()
    children = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = ["id", "label", "url", "order", "children"]

    def get_label(self, obj):
        return {"uz": obj.label_uz, "ru": obj.label_ru, "en": obj.label_en}

    def get_children(self, obj):
        # obj.children is prefetched (see MenuItemViewSet) two levels deep —
        # .all() below hits that cache rather than issuing a new query per node.
        return MenuItemSerializer(obj.children.all(), many=True).data
