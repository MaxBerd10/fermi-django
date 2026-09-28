from rest_framework import serializers

from apps.faculties.models import Faculty
from apps.news.models import NewsPost

from .models import AcceptanceSubmission, ContactSubmission, ContestSubmission, VirtualSubmission


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


class ContestSubmissionSerializer(serializers.ModelSerializer):
    # PrimaryKeyRelatedField (not IntegerField, unlike category/region/district
    # ids elsewhere in this app) -- contest is a real ForeignKey, so a bad id
    # must fail validation here with a clean 400 rather than reach save() and
    # raise an unhandled IntegrityError.
    contestId = serializers.PrimaryKeyRelatedField(
        source="contest", queryset=NewsPost.objects.all(), required=False, allow_null=True
    )
    fullName = serializers.CharField(source="full_name")

    class Meta:
        model = ContestSubmission
        # "file" is a raw upload on the way in (multipart), not an id --
        # the view wraps it into a Document itself rather than through
        # this serializer, same as VirtualSubmissionSerializer.
        fields = ["contestId", "fullName", "phone", "email", "message"]


class VirtualSubmissionSerializer(serializers.ModelSerializer):
    provinceId = serializers.IntegerField(source="region_id", required=False, allow_null=True)
    districtId = serializers.IntegerField(source="district_id", required=False, allow_null=True)
    # PrimaryKeyRelatedField (not IntegerField, unlike category/region/district
    # ids elsewhere in this app) -- faculty is a real ForeignKey, so a bad id
    # must fail validation here with a clean 400 rather than reach save() and
    # raise an unhandled IntegrityError.
    facultyId = serializers.PrimaryKeyRelatedField(
        source="faculty", queryset=Faculty.objects.all(), required=False, allow_null=True
    )

    class Meta:
        model = VirtualSubmission
        # "file" is a raw upload on the way in (multipart -- see
        # submitVirtualReception's FormData), not an id -- the view wraps
        # it into a Document itself rather than through this serializer.
        fields = ["fish", "provinceId", "districtId", "address", "phone", "email", "gender", "facultyId", "text"]
