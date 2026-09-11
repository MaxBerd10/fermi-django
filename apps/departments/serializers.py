from rest_framework import serializers

from apps.content.serializers import PageSerializer
from apps.media_lib.serializers import ImageSerializer

from .models import Department, StaffMember


class StaffMemberSerializer(serializers.ModelSerializer):
    photo = ImageSerializer(read_only=True)
    title = serializers.SerializerMethodField()
    bio = serializers.SerializerMethodField()

    class Meta:
        model = StaffMember
        fields = ["id", "full_name", "title", "bio", "photo", "is_head", "order"]

    def get_title(self, obj):
        return {"uz": obj.title_uz, "ru": obj.title_ru, "en": obj.title_en}

    def get_bio(self, obj):
        return {"uz": obj.bio_uz, "ru": obj.bio_ru, "en": obj.bio_en}


class DepartmentListSerializer(serializers.ModelSerializer):
    logo = ImageSerializer(read_only=True)
    name = serializers.SerializerMethodField()

    class Meta:
        model = Department
        fields = ["id", "slug", "name", "logo"]

    def get_name(self, obj):
        return {"uz": obj.name_uz, "ru": obj.name_ru, "en": obj.name_en}


class DepartmentDetailSerializer(DepartmentListSerializer):
    page = PageSerializer(read_only=True)
    staff = StaffMemberSerializer(many=True, read_only=True)

    class Meta(DepartmentListSerializer.Meta):
        fields = DepartmentListSerializer.Meta.fields + ["page", "staff"]
