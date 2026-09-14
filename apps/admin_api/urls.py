from django.urls import path
from rest_framework.routers import DefaultRouter

from .media_content_views import (
    AdminConnectLeaderViewSet,
    AdminCourseViewSet,
    AdminGalleryPhotoViewSet,
    AdminScheduleFileViewSet,
    AdminVideoClipViewSet,
)
from .leaders_views import AdminLeaderCategoryViewSet, AdminLeaderViewSet
from .media_views import MediaListView, MediaUploadView
from .news_views import AdminPostcategoryViewSet, AdminPostViewSet
from .pages_views import AdminPageViewSet
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
router.register("admin/pages", AdminPageViewSet, basename="admin-pages")
router.register("admin/leaders", AdminLeaderViewSet, basename="admin-leaders")
router.register("admin/leadercategories", AdminLeaderCategoryViewSet, basename="admin-leadercategories")

urlpatterns = router.urls + [
    path("admin/media/list", MediaListView.as_view()),
    path("admin/media/upload", MediaUploadView.as_view()),
]
