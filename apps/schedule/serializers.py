from rest_framework import serializers

from .models import Course, ScheduleFile


class ScheduleFileSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    # DRF's FileField renders an absolute URL automatically when the
    # serializer context carries the request (see ScheduleViewSet) --
    # matches how ImageSerializer's plain "file" field behaves elsewhere.
    file = serializers.FileField(source="document.file", read_only=True)

    class Meta:
        model = ScheduleFile
        fields = ["id", "title", "file"]

    def get_title(self, obj):
        return {"uz": obj.title_uz, "ru": obj.title_ru, "en": obj.title_en}


class CourseScheduleSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    schedules = ScheduleFileSerializer(many=True, read_only=True)

    class Meta:
        model = Course
        fields = ["id", "title", "schedules"]

    def get_title(self, obj):
        return {"uz": obj.title_uz, "ru": obj.title_ru, "en": obj.title_en}
