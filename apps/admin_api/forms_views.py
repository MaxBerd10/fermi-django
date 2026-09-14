"""admin/contacts, admin/acceptances, admin/virtual-submissions -- lets an
admin actually review what the public /aloqa, /qabul, and
/virtual-qabulxona forms collect (see apps.forms for the public side of
this same pipeline, previously entirely missing)."""
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated

from apps.forms.models import AcceptanceSubmission, ContactSubmission, VirtualSubmission

from .common import AdminPagination, IsAdminStaff


class AdminContactSerializer(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    class Meta:
        model = ContactSubmission
        fields = ["id", "name", "subject", "phone", "email", "message", "status"]

    def get_status(self, obj):
        return 1 if not obj.is_read else 0


class AdminContactViewSet(viewsets.ModelViewSet):
    queryset = ContactSubmission.objects.all()
    serializer_class = AdminContactSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination

    def perform_update(self, serializer):
        serializer.save()
        serializer.instance.is_read = True
        serializer.instance.save(update_fields=["is_read"])


class AdminAcceptanceSerializer(serializers.ModelSerializer):
    category_id = serializers.IntegerField(required=False, allow_null=True)
    region_id = serializers.IntegerField(required=False, allow_null=True)
    district_id = serializers.IntegerField(required=False, allow_null=True)
    quater_id = serializers.IntegerField(source="quarter_id", required=False, allow_null=True)

    class Meta:
        model = AcceptanceSubmission
        fields = ["id", "category_id", "fish", "subject", "phone", "email", "region_id", "district_id", "quater_id"]


class AdminAcceptanceViewSet(viewsets.ModelViewSet):
    queryset = AcceptanceSubmission.objects.all()
    serializer_class = AdminAcceptanceSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination


class AdminVirtualSubmissionSerializer(serializers.ModelSerializer):
    faculty_id = serializers.IntegerField(required=False, allow_null=True)
    file = serializers.SerializerMethodField()

    class Meta:
        model = VirtualSubmission
        fields = [
            "id", "fish", "faculty_id", "region_id", "district_id", "address",
            "phone", "email", "gender", "text", "file",
        ]

    def get_file(self, obj):
        if not obj.file:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.file.file.url) if request else obj.file.file.url


class AdminVirtualSubmissionViewSet(viewsets.ModelViewSet):
    queryset = VirtualSubmission.objects.select_related("faculty", "file").all()
    serializer_class = AdminVirtualSubmissionSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
