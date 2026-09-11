from rest_framework import serializers

from apps.media_lib.models import Image
from apps.media_lib.serializers import ImageSerializer

from .models import ContentBlock, Page


class ContentBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentBlock
        fields = ["id", "order", "block_type", "data"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        # "image" blocks store only an image_id per language (see block_schemas.py) —
        # resolve it to the real Image here so the frontend never has to make a
        # second round-trip just to get width/height/file for something it already
        # has the id for.
        if instance.block_type == "image":
            rep["data"] = {
                lang: {**payload, "image": self._resolve_image(payload.get("image_id"))}
                for lang, payload in instance.data.items()
            }
        return rep

    @staticmethod
    def _resolve_image(image_id):
        if image_id is None:
            return None
        image = Image.objects.filter(pk=image_id).first()
        return ImageSerializer(image).data if image else None


class PageSerializer(serializers.ModelSerializer):
    blocks = ContentBlockSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = ["id", "slug", "blocks"]
