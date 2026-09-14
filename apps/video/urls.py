from rest_framework.routers import DefaultRouter

from .views import VideoClipViewSet

router = DefaultRouter()
router.register("video", VideoClipViewSet, basename="video")

urlpatterns = router.urls
