from django.urls import path
from rest_framework.routers import DefaultRouter

from .media_views import MediaListView, MediaUploadView
from .news_views import AdminPostcategoryViewSet, AdminPostViewSet

router = DefaultRouter()
router.register("admin/news", AdminPostViewSet, basename="admin-news")
router.register("admin/postcategories", AdminPostcategoryViewSet, basename="admin-postcategories")

urlpatterns = router.urls + [
    path("admin/media/list", MediaListView.as_view()),
    path("admin/media/upload", MediaUploadView.as_view()),
]
