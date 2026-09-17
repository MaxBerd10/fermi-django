from rest_framework import serializers

from .models import ResultCategory, ResultFile, ResultsPage


class ResultsPageSerializer(serializers.ModelSerializer):
    heading = serializers.SerializerMethodField()
    intro = serializers.SerializerMethodField()
    announcement = serializers.SerializerMethodField()

    class Meta:
        model = ResultsPage
        fields = ["heading", "intro", "announcement"]

    def get_heading(self, obj):
        return {"uz": obj.heading_uz, "ru": obj.heading_ru, "en": obj.heading_en}

    def get_intro(self, obj):
        return {"uz": obj.intro_uz, "ru": obj.intro_ru, "en": obj.intro_en}

    def get_announcement(self, obj):
        return {"uz": obj.announcement_uz, "ru": obj.announcement_ru, "en": obj.announcement_en}


class ResultFileSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    # DRF's FileField renders an absolute URL automatically when the
    # serializer context carries the request -- matches
    # ScheduleFileSerializer's own "file" field.
    file = serializers.FileField(source="document.file", read_only=True)

    class Meta:
        model = ResultFile
        fields = ["id", "title", "file"]

    def get_title(self, obj):
        return {"uz": obj.title_uz, "ru": obj.title_ru, "en": obj.title_en}


class ResultCategorySerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    files = ResultFileSerializer(many=True, read_only=True)

    class Meta:
        model = ResultCategory
        fields = ["id", "title", "files"]

    def get_title(self, obj):
        return {"uz": obj.title_uz, "ru": obj.title_ru, "en": obj.title_en}
