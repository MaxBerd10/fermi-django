from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import ResultCategory, ResultsPage
from .serializers import ResultCategorySerializer, ResultsPageSerializer


class ResultCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = ResultCategory.objects.prefetch_related("files", "files__document")
    serializer_class = ResultCategorySerializer
    # A fixed, short list of categories -- same reasoning as
    # CourseScheduleViewSet.
    pagination_class = None


class ResultsPageView(APIView):
    def get(self, request):
        page = ResultsPage.get_solo()
        return Response(ResultsPageSerializer(page).data)
