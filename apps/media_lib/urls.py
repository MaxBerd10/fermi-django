from rest_framework.routers import DefaultRouter

from django.urls import path

from .private import PrivateFileView
from .views import GalleryPhotoViewSet

router = DefaultRouter()
router.register("gallery", GalleryPhotoViewSet, basename="gallery-photo")

urlpatterns = router.urls + [
    path("private-media/<str:token>/", PrivateFileView.as_view(), name="private-media"),
]
