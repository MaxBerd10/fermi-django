from django.db.models import F
from rest_framework import viewsets
from rest_framework.response import Response

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

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # F() avoids a read-modify-write race between concurrent viewers.
        NewsPost.objects.filter(pk=instance.pk).update(view_count=F("view_count") + 1)
        instance.refresh_from_db(fields=["view_count"])
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
