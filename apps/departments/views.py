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
# the two categories that have a real institute-wide (not
# department/faculty-scoped) data source. "kafedra-mudirlari" is handled
# separately below (its data source is every department's is_head staff,
# not an institute_role), but the frontend's leader/page.tsx has full,
# linked-from-the-menu support for it, so it still needs a real endpoint.
_INSTITUTE_LEADER_CATEGORIES = {
    "rektor": (StaffMember.INSTITUTE_ROLE_RECTOR, "Rektor"),
    "prorektorlar": (StaffMember.INSTITUTE_ROLE_VICE_RECTOR, "Prorektorlar"),
}


class InstituteLeadersView(APIView):
    """
    GET /api/v1/leaders/<category_slug>/ — institute-wide leadership
    (rector, prorektorlar, or every department head under
    "kafedra-mudirlari"), matching the old site's leaders/<slug> shape
    closely enough that the frontend only needs its own adapter (see
    frontend/src/api/leaders.ts), not a schema change here.
    """

    def get(self, request, category_slug):
        if category_slug == "kafedra-mudirlari":
            category_id, title = category_slug, "Kafedra mudirlari"
            leaders = StaffMember.objects.filter(is_head=True, department__isnull=False).select_related("photo")
        else:
            role = _INSTITUTE_LEADER_CATEGORIES.get(category_slug)
            if role is None:
                raise NotFound(f"Unknown leader category: {category_slug}")
            category_id, title = role
            leaders = StaffMember.objects.filter(institute_role=category_id).select_related("photo")

        return Response(
            {
                "category": {"id": category_id, "title": title},
                "menu": None,
                "leaders": StaffMemberSerializer(leaders, many=True, context={"request": request}).data,
            }
        )
