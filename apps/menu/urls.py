from rest_framework.routers import DefaultRouter

from .views import MenuItemViewSet

router = DefaultRouter()
router.register("menu", MenuItemViewSet, basename="menu")

urlpatterns = router.urls
