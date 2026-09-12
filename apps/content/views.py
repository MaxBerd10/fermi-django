from rest_framework import viewsets

from .models import Page
from .serializers import PageSerializer


class PageViewSet(viewsets.ReadOnlyModelViewSet):
    """A standalone Page fetched by its own slug — used for pages that aren't
    nested under a department/faculty/news post (e.g. "institut", "about/...").
    Same Page/ContentBlock/PageSerializer already exercised there."""

    queryset = Page.objects.prefetch_related("blocks")
    serializer_class = PageSerializer
    lookup_field = "slug"
