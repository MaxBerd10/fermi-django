from rest_framework import serializers

from .models import Image, Video


class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ["id", "file", "width", "height", "alt_text"]


class VideoSerializer(serializers.ModelSerializer):
    poster = ImageSerializer(read_only=True)

    class Meta:
        model = Video
        fields = ["id", "file", "poster"]
