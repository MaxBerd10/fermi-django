from rest_framework import viewsets

from .models import Department
from .serializers import DepartmentDetailSerializer, DepartmentListSerializer


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
