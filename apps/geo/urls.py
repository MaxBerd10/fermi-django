from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ConnectLeaderViewSet, DistrictListView, QuarterListView, RegionViewSet

router = DefaultRouter()
router.register("regions", RegionViewSet, basename="region")
router.register("connect-leaders", ConnectLeaderViewSet, basename="connect-leader")

urlpatterns = router.urls + [
    path("districts", DistrictListView.as_view(), name="districts"),
    path("quarters", QuarterListView.as_view(), name="quarters"),
]
