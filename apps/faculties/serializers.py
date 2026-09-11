from rest_framework import serializers

from apps.content.serializers import PageSerializer

from .models import Faculty


class FacultyListSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField()

    class Meta:
        model = Faculty
        fields = ["id", "slug", "name", "order"]

    def get_name(self, obj):
        return {"uz": obj.name_uz, "ru": obj.name_ru, "en": obj.name_en}


class FacultyDetailSerializer(FacultyListSerializer):
    page = PageSerializer(read_only=True)
    departments = serializers.SerializerMethodField()

    class Meta(FacultyListSerializer.Meta):
        fields = FacultyListSerializer.Meta.fields + ["page", "departments"]

    def get_departments(self, obj):
        return [{"id": d.id, "slug": d.slug, "name_uz": d.name_uz} for d in obj.departments.all()]
