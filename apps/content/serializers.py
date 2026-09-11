from rest_framework import serializers

from apps.media_lib.models import Document, Image, Video
from apps.media_lib.serializers import DocumentSerializer, ImageSerializer, VideoSerializer

from .models import ContentBlock, Page

# Blocks that reference a media_lib object by id (see block_schemas.py) get that
# reference resolved to the real object here, so the frontend never has to make
# a second round-trip just to get a file/dimensions/poster for something it
# already has the id for.
_MEDIA_REFERENCE_RESOLVERS = {
    "image": ("image_id", "image", Image, ImageSerializer),
    "video": ("video_id", "video", Video, VideoSerializer),
    "document": ("document_id", "document", Document, DocumentSerializer),
}


class ContentBlockSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentBlock
        fields = ["id", "order", "block_type", "data"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if instance.block_type == "gallery":
            rep["data"] = {
                lang: {
                    "items": [
                        {**item, "image": self._resolve(Image, ImageSerializer, item.get("image_id"))}
                        for item in payload.get("items", [])
                    ]
                }
                for lang, payload in instance.data.items()
            }
            return rep
        resolver = _MEDIA_REFERENCE_RESOLVERS.get(instance.block_type)
        if resolver:
            id_field, out_field, model, serializer_class = resolver
            rep["data"] = {
                lang: {**payload, out_field: self._resolve(model, serializer_class, payload.get(id_field))}
                for lang, payload in instance.data.items()
            }
        return rep

    @staticmethod
    def _resolve(model, serializer_class, object_id):
        if object_id is None:
            return None
        obj = model.objects.filter(pk=object_id).first()
        return serializer_class(obj).data if obj else None


class PageSerializer(serializers.ModelSerializer):
    blocks = ContentBlockSerializer(many=True, read_only=True)

    class Meta:
        model = Page
        fields = ["id", "slug", "blocks"]
