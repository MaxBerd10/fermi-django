from rest_framework import viewsets

from .models import NewsPost
from .serializers import NewsPostDetailSerializer, NewsPostListSerializer


class NewsPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NewsPost.objects.select_related("cover", "page").prefetch_related("page__blocks")
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return NewsPostListSerializer
        return NewsPostDetailSerializer
