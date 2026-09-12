from rest_framework import viewsets

from .models import NewsPost
from .serializers import NewsPostDetailSerializer, NewsPostListSerializer


class NewsPostViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = NewsPost.objects.select_related("cover", "category", "page").prefetch_related("page__blocks")
    lookup_field = "slug"

    def get_serializer_class(self):
        if self.action == "list":
            return NewsPostListSerializer
        return NewsPostDetailSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category_slug = self.request.query_params.get("category")
        if category_slug:
            queryset = queryset.filter(category__slug=category_slug)
        return queryset
