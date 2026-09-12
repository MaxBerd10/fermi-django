from rest_framework import viewsets
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Department, StaffMember
from .serializers import DepartmentDetailSerializer, DepartmentListSerializer, StaffMemberSerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.select_related("logo", "page").prefetch_related(
        "staff", "staff__photo", "page__blocks"
    )
    lookup_field = "slug"
    # There are ~30 departments total, ever — this is a fixed reference list
    # the frontend renders as one grid, not a feed a visitor pages through.
    # Paginating it would silently truncate at PAGE_SIZE (20).
    pagination_class = None

    def get_serializer_class(self):
        if self.action == "list":
            return DepartmentListSerializer
        return DepartmentDetailSerializer


# Maps the old site's leader-category URL slugs to our institute_role values —
# only the two categories that have a real institute-wide (not
# department/faculty-scoped) data source; "kafedra-mudirlari" from the old
# site is just every department's is_head staff, already served via
# /departments, so it isn't duplicated here.
_INSTITUTE_LEADER_CATEGORIES = {
    "rektor": (StaffMember.INSTITUTE_ROLE_RECTOR, "Rektor"),
    "prorektorlar": (StaffMember.INSTITUTE_ROLE_VICE_RECTOR, "Prorektorlar"),
}


class InstituteLeadersView(APIView):
    """
    GET /api/v1/leaders/<category_slug>/ — institute-wide leadership
    (rector, prorektorlar), matching the old site's leaders/<slug> shape
    closely enough that the frontend only needs its own adapter (see
    frontend/src/api/leaders.ts), not a schema change here.
    """

    def get(self, request, category_slug):
        role = _INSTITUTE_LEADER_CATEGORIES.get(category_slug)
        if role is None:
            raise NotFound(f"Unknown leader category: {category_slug}")
        institute_role, title = role

        leaders = StaffMember.objects.filter(institute_role=institute_role).select_related("photo")
        return Response(
            {
                "category": {"id": institute_role, "title": title},
                "menu": None,
                "leaders": StaffMemberSerializer(leaders, many=True, context={"request": request}).data,
            }
        )
