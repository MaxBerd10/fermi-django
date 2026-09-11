from rest_framework.routers import DefaultRouter

from .views import NewsPostViewSet

router = DefaultRouter()
router.register("news", NewsPostViewSet, basename="news")

urlpatterns = router.urls
