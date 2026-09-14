from django.urls import path
from rest_framework.routers import DefaultRouter

from .media_content_views import (
    AdminConnectLeaderViewSet,
    AdminCourseViewSet,
    AdminGalleryPhotoViewSet,
    AdminScheduleFileViewSet,
    AdminVideoClipViewSet,
)
from .media_views import MediaListView, MediaUploadView
from .news_views import AdminPostcategoryViewSet, AdminPostViewSet
from .structure_views import AdminDepartmentViewSet, AdminFacultyViewSet

router = DefaultRouter()
router.register("admin/news", AdminPostViewSet, basename="admin-news")
router.register("admin/postcategories", AdminPostcategoryViewSet, basename="admin-postcategories")
router.register("admin/faculty", AdminFacultyViewSet, basename="admin-faculty")
router.register("admin/departments", AdminDepartmentViewSet, basename="admin-departments")
router.register("admin/gallery-images", AdminGalleryPhotoViewSet, basename="admin-gallery-images")
router.register("admin/videos", AdminVideoClipViewSet, basename="admin-videos")
router.register("admin/courses", AdminCourseViewSet, basename="admin-courses")
router.register("admin/schedules", AdminScheduleFileViewSet, basename="admin-schedules")
router.register("admin/connect-leaders", AdminConnectLeaderViewSet, basename="admin-connect-leaders")

urlpatterns = router.urls + [
    path("admin/media/list", MediaListView.as_view()),
    path("admin/media/upload", MediaUploadView.as_view()),
]
