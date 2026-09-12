from rest_framework import serializers

from .models import Document, GalleryPhoto, Image, Video


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["id", "file", "width", "height", "alt_text"]


class GalleryPhotoSerializer(serializers.ModelSerializer):
    image = ImageSerializer(read_only=True)
    caption = serializers.SerializerMethodField()

    class Meta:
        model = GalleryPhoto
        fields = ["id", "image", "caption", "order"]

    def get_caption(self, obj):
        return {"uz": obj.caption_uz, "ru": obj.caption_ru, "en": obj.caption_en}


class VideoSerializer(serializers.ModelSerializer):
    poster = ImageSerializer(read_only=True)

    class Meta:
        model = Video
        fields = ["id", "file", "poster"]


class DocumentSerializer(serializers.ModelSerializer):
    filename = serializers.ReadOnlyField()

    class Meta:
        model = Document
        fields = ["id", "file", "title", "filename", "file_size"]
