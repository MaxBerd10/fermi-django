from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .models import GalleryPhoto
from .serializers import GalleryPhotoSerializer


class GalleryPagination(PageNumberPagination):
    # The frontend hardcodes 12-per-page for its own totalPages math (see
    # frontend/src/pages/galereya/page.tsx) — matching the old site's own
    # page size exactly rather than the project's normal default of 20.
    page_size = 12


class GalleryPhotoViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = GalleryPhoto.objects.select_related("image")
    serializer_class = GalleryPhotoSerializer
    pagination_class = GalleryPagination
