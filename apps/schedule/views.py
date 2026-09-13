from rest_framework import viewsets

from .models import Course
from .serializers import CourseScheduleSerializer


class CourseScheduleViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Course.objects.prefetch_related("schedules", "schedules__document")
    serializer_class = CourseScheduleSerializer
    # A fixed, short list of courses -- same reasoning as DepartmentViewSet.
    pagination_class = None
