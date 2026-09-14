from rest_framework import serializers

from .models import VideoClip


class VideoClipSerializer(serializers.ModelSerializer):
    video = serializers.SerializerMethodField()
    url = serializers.SerializerMethodField()

    class Meta:
        model = VideoClip
        fields = ["id", "video", "url"]

    def get_video(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        url = obj.file.url
        return request.build_absolute_uri(url) if request else url

    def get_url(self, obj):
        return obj.youtube_id or None
