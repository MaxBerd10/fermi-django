from rest_framework import viewsets

from .models import Faculty
from .serializers import FacultyDetailSerializer, FacultyListSerializer


class FacultyViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Faculty.objects.select_related("page").prefetch_related("page__blocks", "departments")
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return FacultyListSerializer
        return FacultyDetailSerializer
