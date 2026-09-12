from rest_framework.routers import DefaultRouter

from .views import GalleryPhotoViewSet

router = DefaultRouter()
router.register("gallery", GalleryPhotoViewSet, basename="gallery-photo")

urlpatterns = router.urls
