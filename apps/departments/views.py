from rest_framework import viewsets

from .models import Department
from .serializers import DepartmentDetailSerializer, DepartmentListSerializer


class DepartmentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Department.objects.select_related("logo", "page").prefetch_related(
        "staff", "staff__photo", "page__blocks"
    )
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return DepartmentListSerializer
        return DepartmentDetailSerializer
