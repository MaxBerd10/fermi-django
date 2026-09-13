from rest_framework import serializers

from .models import Document, DocumentItem


class DocumentItemSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    content = serializers.SerializerMethodField()

    class Meta:
        model = DocumentItem
        fields = ["id", "slug", "title", "content"]

    def get_title(self, obj):
        return {"uz": obj.title_uz, "ru": obj.title_ru, "en": obj.title_en}

    def get_content(self, obj):
        return {"uz": obj.content_uz, "ru": obj.content_ru, "en": obj.content_en}


class DocumentDetailSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    items = DocumentItemSerializer(many=True, read_only=True)
    # Django has no per-document menu-branch concept, same as Department's
    # own "menu" field — real navigation comes from apps.menu instead (see
    # frontend/src/api/departments.ts's identical `menu: null` mapping).
    menu = serializers.SerializerMethodField()

    class Meta:
        model = Document
        fields = ["id", "slug", "title", "items", "menu"]

    def get_title(self, obj):
        return {"uz": obj.title_uz, "ru": obj.title_ru, "en": obj.title_en}

    def get_menu(self, obj):
        return None
