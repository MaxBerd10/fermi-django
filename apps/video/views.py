from rest_framework.pagination import PageNumberPagination
from rest_framework import viewsets

from .models import VideoClip
from .serializers import VideoClipSerializer


class VideoClipPagination(PageNumberPagination):
    # Matches the old site's own /video listing (9 per page, 19 pages for
    # 171 items) -- frontend/src/pages/video/page.tsx's own pageSize const
    # assumes this exact page size.
    page_size = 9


class VideoClipViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = VideoClip.objects.all()
    serializer_class = VideoClipSerializer
    pagination_class = VideoClipPagination
