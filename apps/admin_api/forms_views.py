"""admin/contacts, admin/acceptances, admin/virtual-submissions,
admin/contest-submissions -- lets an admin actually review what the public
/aloqa, /qabul, /virtual-qabulxona and "tanlovlar" forms collect (see
apps.forms for the public side of this same pipeline, previously entirely
missing).

All four are inbound submissions, so they share one review workflow
(SubmissionReviewMixin): `status` is 1 while a submission is still unread and
0 once somebody has looked at it -- opening it counts as looking, and the
form's own status select can flip it back to "new" to keep it on the todo
list. Each also reports `created_at` so the list can show when it arrived."""
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.faculties.models import Faculty
from apps.forms.models import AcceptanceSubmission, ContactSubmission, ContestSubmission, VirtualSubmission
from apps.news.models import NewsPost

from .common import AdminSearchMixin, AdminPagination, IsAdminStaff


class SubmissionReviewMixin:
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if not instance.is_read:
            instance.is_read = True
            instance.save(update_fields=["is_read"])
        return Response(self.get_serializer(instance).data)

    def perform_update(self, serializer):
        serializer.save()
        instance = serializer.instance
        status = str(self.request.data.get("status", ""))
        # An explicit status from the form wins; a bare PATCH of some other
        # field (no status sent) still counts as the submission being handled.
        instance.is_read = status != "1"
        instance.save(update_fields=["is_read"])


class StatusFieldMixin(serializers.Serializer):
    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return 1 if not obj.is_read else 0


def _file_fields(obj, request):
    if not obj.file:
        return None, None
    url = request.build_absolute_uri(obj.file.file.url) if request else obj.file.file.url
    return url, (obj.file.title or obj.file.filename)


class AdminContactSerializer(StatusFieldMixin, serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = ["id", "name", "subject", "phone", "email", "message", "status", "created_at"]
        read_only_fields = ["created_at"]


class AdminContactViewSet(AdminSearchMixin, SubmissionReviewMixin, viewsets.ModelViewSet):
    search_fields = ('name', 'subject', 'phone', 'email', 'message')
    queryset = ContactSubmission.objects.all()
    serializer_class = AdminContactSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminAcceptanceSerializer(StatusFieldMixin, serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)
    region_id = serializers.IntegerField(required=False, allow_null=True)
    district_id = serializers.IntegerField(required=False, allow_null=True)
    quater_id = serializers.IntegerField(source="quarter_id", required=False, allow_null=True)

    class Meta:
        model = AcceptanceSubmission
        fields = [
            "id", "category_id", "fish", "subject", "phone", "email",
            "region_id", "district_id", "quater_id", "status", "created_at",
        ]
        read_only_fields = ["created_at"]


class AdminAcceptanceViewSet(AdminSearchMixin, SubmissionReviewMixin, viewsets.ModelViewSet):
    search_fields = ('fish', 'subject', 'phone', 'email')
    queryset = AcceptanceSubmission.objects.all()
    serializer_class = AdminAcceptanceSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminVirtualSubmissionSerializer(StatusFieldMixin, serializers.ModelSerializer):
    # PrimaryKeyRelatedField, not IntegerField -- faculty is a real
    # ForeignKey, so a bad id must fail validation with a clean 400 rather
    # than reach save() and raise an unhandled IntegrityError.
    faculty_id = serializers.PrimaryKeyRelatedField(
        source="faculty", queryset=Faculty.objects.all(), required=False, allow_null=True
    )
    # The attachment is whatever the visitor uploaded -- shown (as a download
    # link) but never writable from here.
    file = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = VirtualSubmission
        fields = [
            "id", "fish", "faculty_id", "region_id", "district_id", "address",
            "phone", "email", "gender", "text", "file", "file_name", "status", "created_at",
        ]
        read_only_fields = ["created_at"]

    def get_file(self, obj):
        return _file_fields(obj, self.context.get("request"))[0]

    def get_file_name(self, obj):
        return _file_fields(obj, self.context.get("request"))[1]


class AdminVirtualSubmissionViewSet(AdminSearchMixin, SubmissionReviewMixin, viewsets.ModelViewSet):
    search_fields = ('fish', 'address', 'phone', 'email', 'text')
    queryset = VirtualSubmission.objects.select_related("faculty", "file").all()
    serializer_class = AdminVirtualSubmissionSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminContestSubmissionSerializer(StatusFieldMixin, serializers.ModelSerializer):
    contest_id = serializers.PrimaryKeyRelatedField(
        source="contest", queryset=NewsPost.objects.all(), required=False, allow_null=True
    )
    contest_title = serializers.SerializerMethodField()
    file = serializers.SerializerMethodField()
    file_name = serializers.SerializerMethodField()

    class Meta:
        model = ContestSubmission
        fields = [
            "id", "contest_id", "contest_title", "full_name", "phone", "email",
            "message", "status", "created_at", "file", "file_name",
        ]
        read_only_fields = ["created_at"]

    def get_contest_title(self, obj):
        return obj.contest.title_uz if obj.contest else None

    def get_file(self, obj):
        return _file_fields(obj, self.context.get("request"))[0]

    def get_file_name(self, obj):
        return _file_fields(obj, self.context.get("request"))[1]


class AdminContestSubmissionViewSet(AdminSearchMixin, SubmissionReviewMixin, viewsets.ModelViewSet):
    search_fields = ('full_name', 'phone', 'email', 'message', 'contest__title_uz')
    queryset = ContestSubmission.objects.select_related("contest", "file").all()
    serializer_class = AdminContestSubmissionSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
