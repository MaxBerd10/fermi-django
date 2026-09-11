from rest_framework import serializers

from .models import ContentBlock, Page


class ContentBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentBlock
        fields = ["id", "order", "block_type", "data"]


class PageSerializer(serializers.ModelSerializer):
    blocks = ContentBlockSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = ["id", "slug", "blocks"]
