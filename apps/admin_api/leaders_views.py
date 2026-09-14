"""admin/leaders + admin/leadercategories -- see entityConfigs.ts's
leaderConfig/leadercategoryConfig.

StaffMember belongs to exactly one of department/faculty/institute_role
(see its own model docstring: a deliberate design choice covering rector/
prorektorlar, a faculty's leadership, and a kafedra's staff with one
model instead of three). The old admin's "leadercategories" is a free-
form, separately-managed category table with no such structure -- there's
no real table on our side to back arbitrary category CRUD without
undoing that design. Categories here are computed instead of stored:
id 1/2 for the two institute roles, 1000+faculty.id for each faculty,
2000+department.id for each department. That covers exactly what
LeaderConfig's category_id dropdown needs (pick which group a person
belongs to) and reads real, always-current names -- but it means
leadercategories is read-only here (nothing to validly create/edit/
delete into): a category "exists" only because a real faculty/department
does.
"""
from rest_framework import serializers, viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.departments.models import Department, StaffMember
from apps.faculties.models import Faculty

from .common import AdminPagination, IsAdminStaff, resolve_or_create_image

_ROLE_REKTOR = 1
_ROLE_PROREKTOR = 2
_FACULTY_OFFSET = 1000
_DEPARTMENT_OFFSET = 2000


def _category_id_for(staff: StaffMember) -> int | None:
    if staff.institute_role == StaffMember.INSTITUTE_ROLE_RECTOR:
        return _ROLE_REKTOR
    if staff.institute_role == StaffMember.INSTITUTE_ROLE_VICE_RECTOR:
        return _ROLE_PROREKTOR
    if staff.faculty_id:
        return _FACULTY_OFFSET + staff.faculty_id
    if staff.department_id:
        return _DEPARTMENT_OFFSET + staff.department_id
    return None


def _apply_category_id(staff: StaffMember, category_id: int | None) -> None:
    staff.institute_role = ""
    staff.faculty = None
    staff.department = None
    if category_id == _ROLE_REKTOR:
        staff.institute_role = StaffMember.INSTITUTE_ROLE_RECTOR
    elif category_id == _ROLE_PROREKTOR:
        staff.institute_role = StaffMember.INSTITUTE_ROLE_VICE_RECTOR
    elif category_id and category_id >= _DEPARTMENT_OFFSET:
        staff.department_id = category_id - _DEPARTMENT_OFFSET
    elif category_id and category_id >= _FACULTY_OFFSET:
        staff.faculty_id = category_id - _FACULTY_OFFSET


class AdminLeaderCategoryViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination

    def list(self, request):
        rows = [
            {"id": _ROLE_REKTOR, "title_uz": "Rektor", "title_ru": "Ректор", "title_en": "Rector", "status": 1},
            {"id": _ROLE_PROREKTOR, "title_uz": "Prorektorlar", "title_ru": "Проректоры", "title_en": "Vice-rectors", "status": 1},
        ]
        for f in Faculty.objects.order_by("order", "id"):
            rows.append({"id": _FACULTY_OFFSET + f.id, "title_uz": f"Fakultet: {f.name_uz}", "title_ru": f.name_ru, "title_en": f.name_en, "status": 1})
        for d in Department.objects.order_by("name_uz"):
            rows.append({"id": _DEPARTMENT_OFFSET + d.id, "title_uz": f"Kafedra: {d.name_uz}", "title_ru": d.name_ru, "title_en": d.name_en, "status": 1})
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("pageSize", 100))
        start = (page - 1) * page_size
        return Response({
            "count": len(rows),
            "next": None,
            "previous": None,
            "results": rows[start:start + page_size],
        })

    def retrieve(self, request, pk=None):
        for row in self.list(request).data["results"]:
            if str(row["id"]) == str(pk):
                return Response(row)
        return Response({"detail": "Not found."}, status=404)


class AdminLeaderSerializer(serializers.ModelSerializer):
    name_uz = serializers.CharField(source="full_name_uz")
    name_ru = serializers.CharField(source="full_name_ru", required=False, allow_blank=True)
    name_en = serializers.CharField(source="full_name_en", required=False, allow_blank=True)
    position_uz = serializers.CharField(source="title_uz", required=False, allow_blank=True)
    position_ru = serializers.CharField(source="title_ru", required=False, allow_blank=True)
    position_en = serializers.CharField(source="title_en", required=False, allow_blank=True)
    reception_days_uz = serializers.CharField(required=False, allow_blank=True)
    reception_days_ru = serializers.CharField(required=False, allow_blank=True)
    reception_days_en = serializers.CharField(required=False, allow_blank=True)
    activity_uz = serializers.CharField(required=False, allow_blank=True)
    activity_ru = serializers.CharField(required=False, allow_blank=True)
    activity_en = serializers.CharField(required=False, allow_blank=True)
    biography_uz = serializers.CharField(source="bio_uz", required=False, allow_blank=True)
    biography_ru = serializers.CharField(source="bio_ru", required=False, allow_blank=True)
    biography_en = serializers.CharField(source="bio_en", required=False, allow_blank=True)
    category_id = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    rasm = serializers.SerializerMethodField()
    faks = serializers.SerializerMethodField()

    class Meta:
        model = StaffMember
        fields = [
            "id", "name_uz", "name_ru", "name_en",
            "position_uz", "position_ru", "position_en",
            "category_id", "rasm", "phone", "faks", "email",
            "reception_days_uz", "reception_days_ru", "reception_days_en",
            "status", "activity_uz", "activity_ru", "activity_en",
            "biography_uz", "biography_ru", "biography_en",
        ]

    def get_category_id(self, obj):
        return _category_id_for(obj)

    def get_status(self, obj):
        return 1

    def get_rasm(self, obj):
        if not obj.photo:
            return None
        request = self.context.get("request")
        return request.build_absolute_uri(obj.photo.file.url) if request else obj.photo.file.url

    # StaffMember has no fax field (see api/leaders.ts's own mapLeader --
    # "the old CMS's was unused everywhere it mattered") -- accepted but
    # not persisted, same treatment as News's unmodeled fields.
    def get_faks(self, obj):
        return None

    def create(self, validated_data):
        return self._save(StaffMember(), validated_data)

    def update(self, instance, validated_data):
        return self._save(instance, validated_data)

    def _save(self, instance, validated_data):
        data = self.context["request"].data
        instance.full_name_uz = data.get("name_uz", instance.full_name_uz or "")
        instance.full_name_ru = data.get("name_ru") or instance.full_name_uz
        instance.full_name_en = data.get("name_en") or instance.full_name_uz
        instance.title_uz = data.get("position_uz", instance.title_uz or "")
        instance.title_ru = data.get("position_ru") or instance.title_uz
        instance.title_en = data.get("position_en") or instance.title_uz
        instance.phone = data.get("phone", instance.phone or "")
        instance.email = data.get("email", instance.email or "")
        instance.reception_days_uz = data.get("reception_days_uz", instance.reception_days_uz or "")
        instance.reception_days_ru = data.get("reception_days_ru") or instance.reception_days_uz
        instance.reception_days_en = data.get("reception_days_en") or instance.reception_days_uz
        instance.activity_uz = data.get("activity_uz", instance.activity_uz or "")
        instance.activity_ru = data.get("activity_ru", instance.activity_ru or "")
        instance.activity_en = data.get("activity_en", instance.activity_en or "")
        instance.bio_uz = data.get("biography_uz", instance.bio_uz or "")
        instance.bio_ru = data.get("biography_ru", instance.bio_ru or "")
        instance.bio_en = data.get("biography_en", instance.bio_en or "")
        category_id = data.get("category_id")
        if category_id is not None:
            _apply_category_id(instance, int(category_id))
        image = resolve_or_create_image(data.get("rasm"))
        if image is not None:
            instance.photo = image
        instance.full_clean()
        instance.save()
        return instance


class AdminLeaderViewSet(viewsets.ModelViewSet):
    queryset = StaffMember.objects.select_related("photo", "department", "faculty").order_by("order", "id")
    serializer_class = AdminLeaderSerializer
    permission_classes = [IsAuthenticated, IsAdminStaff]
    pagination_class = AdminPagination
