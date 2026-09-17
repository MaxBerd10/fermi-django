from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import ResultCategoryViewSet, ResultsPageView

router = DefaultRouter()
router.register("admission-results", ResultCategoryViewSet, basename="admission-results")

urlpatterns = router.urls + [
    path("admission-results-page", ResultsPageView.as_view()),
]
