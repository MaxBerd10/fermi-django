from rest_framework import serializers

from .models import AcceptanceSubmission, ContactSubmission, VirtualSubmission


class ContactSubmissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContactSubmission
        fields = ["name", "email", "phone", "subject", "message"]


class AcceptanceSubmissionSerializer(serializers.ModelSerializer):
    categoryId = serializers.IntegerField(source="category_id", required=False, allow_null=True)
    regionId = serializers.IntegerField(source="region_id", required=False, allow_null=True)
    districtId = serializers.IntegerField(source="district_id", required=False, allow_null=True)
    quarterId = serializers.IntegerField(source="quarter_id", required=False, allow_null=True)

    class Meta:
        model = AcceptanceSubmission
        fields = ["categoryId", "subject", "fish", "phone", "email", "regionId", "districtId", "quarterId"]


class VirtualSubmissionSerializer(serializers.ModelSerializer):
    provinceId = serializers.IntegerField(source="region_id", required=False, allow_null=True)
    districtId = serializers.IntegerField(source="district_id", required=False, allow_null=True)
    facultyId = serializers.IntegerField(source="faculty_id", required=False, allow_null=True)

    class Meta:
        model = VirtualSubmission
        # "file" is a raw upload on the way in (multipart -- see
        # submitVirtualReception's FormData), not an id -- the view wraps
        # it into a Document itself rather than through this serializer.
        fields = ["fish", "provinceId", "districtId", "address", "phone", "email", "gender", "facultyId", "text"]
