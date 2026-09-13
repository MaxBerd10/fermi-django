from rest_framework.routers import DefaultRouter

from .views import CourseScheduleViewSet

router = DefaultRouter()
router.register("schedule", CourseScheduleViewSet, basename="schedule")

urlpatterns = router.urls
