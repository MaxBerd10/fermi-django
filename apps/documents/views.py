from rest_framework import viewsets

from .models import Document
from .serializers import DocumentDetailSerializer


class DocumentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Document.objects.prefetch_related("items")
    serializer_class = DocumentDetailSerializer
    lookup_field = "slug"
    # A handful of fixed document collections, not a feed — same reasoning
    # as DepartmentViewSet's pagination_class = None.
    pagination_class = None
