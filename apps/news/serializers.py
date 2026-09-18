from rest_framework import serializers

from apps.content.serializers import PageSerializer
from apps.media_lib.serializers import ImageSerializer

from .models import NewsCategory, NewsPost


class NewsCategorySerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = NewsCategory
        fields = ["id", "slug", "name"]

    def get_name(self, obj):
        return {"uz": obj.name_uz, "ru": obj.name_ru, "en": obj.name_en}


class NewsPostListSerializer(serializers.ModelSerializer):
    cover = ImageSerializer(read_only=True)
    category = NewsCategorySerializer(read_only=True)
    title = serializers.SerializerMethodField()
    excerpt = serializers.SerializerMethodField()

    class Meta:
        model = NewsPost
        fields = ["id", "slug", "title", "excerpt", "cover", "category", "published_at", "view_count"]

    def get_title(self, obj):
        return {"uz": obj.title_uz, "ru": obj.title_ru, "en": obj.title_en}

    def get_excerpt(self, obj):
        return {"uz": obj.excerpt_uz, "ru": obj.excerpt_ru, "en": obj.excerpt_en}


class NewsPostDetailSerializer(NewsPostListSerializer):
    page = PageSerializer(read_only=True)

    class Meta(NewsPostListSerializer.Meta):
        fields = NewsPostListSerializer.Meta.fields + ["page"]
