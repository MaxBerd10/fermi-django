"""admin/gallery-images, admin/videos, admin/courses, admin/schedules,
admin/connect-leaders -- see entityConfigs.ts. All five are simple,
already backed by existing models with no content/page involved."""
import re

from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.geo.models import ConnectLeader
from apps.media_lib.models import GalleryPhoto
from apps.schedule.models import Course, ScheduleFile
from apps.video.models import VideoClip

from .common import (
    AdminSearchMixin,
    AdminPagination,
    IsAdminStaff,
    media_relative_path,
    resolve_or_create_document,
    resolve_or_create_image,
)


class AdminGalleryPhotoSerializer(serializers.ModelSerializer):
    title_uz = serializers.CharField(source="caption_uz", required=False, allow_blank=True)
    title_ru = serializers.CharField(source="caption_ru", required=False, allow_blank=True)
    title_en = serializers.CharField(source="caption_en", required=False, allow_blank=True)
    content_uz = serializers.SerializerMethodField()
    content_ru = serializers.SerializerMethodField()
    content_en = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    img = serializers.SerializerMethodField()

    class Meta:
        model = GalleryPhoto
        fields = ["id", "title_uz", "title_ru", "title_en", "content_uz", "content_ru", "content_en", "status", "img"]

    # GalleryPhoto has no ContentBlock body (see its own model docstring:
    # a flat, uncaptioned photo stream) -- entityConfigs.ts's "Izoh"
    # (caption) lang-html field has nowhere real to write to here, so it
    # always reads empty and any input is ignored, same treatment as
    # NewsPost's unmodeled fields.
    def get_content_uz(self, obj):
        return ""

    def get_content_ru(self, obj):
        return ""

    def get_content_en(self, obj):
        return ""

    def get_status(self, obj):
        return 1

    def get_img(self, obj):
        if not obj.image:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.image.file.url) if request else obj.image.file.url

    def create(self, validated_data):
        return self._save(GalleryPhoto(), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.caption_uz = data.get("title_uz", instance.caption_uz or "")
        instance.caption_ru = data.get("title_ru", instance.caption_ru or "")
        instance.caption_en = data.get("title_en", instance.caption_en or "")
        image = resolve_or_create_image(data.get("img"))
        if image is not None:
            instance.image = image
        if not instance.image_id:
            raise serializers.ValidationError({"img": ["Rasm tanlash majburiy."]})
        instance.save()
        return instance


class AdminGalleryPhotoViewSet(AdminSearchMixin, viewsets.ModelViewSet):
    search_fields = ('caption_uz', 'caption_ru', 'caption_en')
    queryset = GalleryPhoto.objects.select_related("image").order_by("-order", "-id")
    serializer_class = AdminGalleryPhotoSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


YOUTUBE_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")
YOUTUBE_URL_RE = re.compile(
    r"(?:youtu\.be/|youtube(?:-nocookie)?\.com/(?:watch\?(?:[^#]*&)?v=|embed/|shorts/|live/|v/))([A-Za-z0-9_-]{11})"
)


def youtube_id_from(value: str) -> str:
    """The 11-character video id from whatever an editor pasted (a watch / youtu.be / embed / shorts link or the bare
    id). The public /video page builds its embed address from the id alone, so a whole link must never be stored."""
    value = (value or "").strip()
    if not value:
        return ""
    if YOUTUBE_ID_RE.match(value):
        return value
    match = YOUTUBE_URL_RE.search(value)
    if not match:
        raise serializers.ValidationError({"url": ["YouTube havolasi tanilmadi. Masalan: https://youtu.be/dQw4w9WgXcQ"]})
    return match.group(1)


class AdminVideoClipSerializer(serializers.ModelSerializer):
    video = serializers.SerializerMethodField()
    url = serializers.CharField(source="youtube_id", required=False, allow_blank=True)
    title = serializers.SerializerMethodField()
    kind = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()

    class Meta:
        model = VideoClip
        fields = ["id", "video", "url", "title", "kind", "status"]

    def get_video(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.url) if request else obj.file.url

    def get_title(self, obj):
        if obj.youtube_id:
            return f"YouTube: {obj.youtube_id}"
        return obj.file.name.rsplit("/", 1)[-1] if obj.file else f"Video #{obj.pk}"

    def get_kind(self, obj):
        return "YouTube" if obj.youtube_id else "Yuklangan fayl"

    def get_status(self, obj):
        return 1

    def create(self, validated_data):
        return self._save(VideoClip(), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.youtube_id = youtube_id_from(str(data.get("url") or ""))
        # A record opened for editing echoes its file back as an absolute URL: normalise it, and only touch the stored
        # file when the editor really pointed at another one (re-saving an untouched form must not rewrite it).
        video_path = media_relative_path(str(data.get("video") or ""))
        if video_path and video_path != (instance.file.name if instance.file else ""):
            instance.file = video_path
        instance.save()
        return instance


class AdminVideoClipViewSet(AdminSearchMixin, viewsets.ModelViewSet):
    search_fields = ('youtube_id',)
    queryset = VideoClip.objects.order_by("-order", "-id")
    serializer_class = AdminVideoClipSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminCourseSerializer(serializers.ModelSerializer):
    title_uz = serializers.CharField()
    title_ru = serializers.CharField(required=False, allow_blank=True)
    title_en = serializers.CharField(required=False, allow_blank=True)
    status = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = ["id", "title_uz", "title_ru", "title_en", "status"]

    def get_status(self, obj):
        return 1

    def create(self, validated_data):
        instance = Course()
        return self._save(instance)

    def update(self, instance, validated_data):
        return self._save(instance)

    def _save(self, instance):
        data = self.context["request"].data
        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru") or instance.title_uz
        instance.title_en = data.get("title_en") or instance.title_uz
        instance.save()
        return instance


class AdminCourseViewSet(AdminSearchMixin, viewsets.ModelViewSet):
    search_fields = ('title_uz', 'title_ru', 'title_en')
    queryset = Course.objects.order_by("order", "id")
    serializer_class = AdminCourseSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminScheduleFileSerializer(serializers.ModelSerializer):
    title_uz = serializers.CharField()
    title_ru = serializers.CharField(required=False, allow_blank=True)
    title_en = serializers.CharField(required=False, allow_blank=True)
    course_id = serializers.IntegerField()
    status = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()

    class Meta:
        model = ScheduleFile
        fields = ["id", "title_uz", "title_ru", "title_en", "course_id", "status", "file"]

    def get_status(self, obj):
        return 1

    def get_file(self, obj):
        if not obj.document:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.document.file.url) if request else obj.document.file.url

    def create(self, validated_data):
        return self._save(ScheduleFile())

    def update(self, instance, validated_data):
        return self._save(instance)

    def _save(self, instance):
        data = self.context["request"].data
        instance.title_uz = data.get("title_uz", instance.title_uz or "")
        instance.title_ru = data.get("title_ru") or instance.title_uz
        instance.title_en = data.get("title_en") or instance.title_uz
        instance.course_id = data.get("course_id") or instance.course_id
        document = resolve_or_create_document(data.get("file"))
        if document is not None:
            instance.document = document
        if not instance.course_id:
            raise serializers.ValidationError({"course_id": ["Kursni tanlang."]})
        if not instance.document_id:
            raise serializers.ValidationError({"file": ["Fayl tanlash majburiy."]})
        instance.save()
        return instance


class AdminScheduleFileViewSet(AdminSearchMixin, viewsets.ModelViewSet):
    search_fields = ('title_uz', 'title_ru', 'title_en', 'course__title_uz')
    queryset = ScheduleFile.objects.select_related("course", "document").order_by("order", "id")
    serializer_class = AdminScheduleFileSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminConnectLeaderSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = ConnectLeader
        fields = ["id", "name", "status"]

    def get_status(self, obj):
        return 1


class AdminConnectLeaderViewSet(AdminSearchMixin, viewsets.ModelViewSet):
    search_fields = ('name',)
    queryset = ConnectLeader.objects.order_by("order", "id")
    serializer_class = AdminConnectLeaderSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
