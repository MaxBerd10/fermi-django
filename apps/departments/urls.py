from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import DepartmentViewSet, InstituteLeadersView

router = DefaultRouter()
router.register("departments", DepartmentViewSet, basename="department")

urlpatterns = router.urls + [
    path("leaders/<str:category_slug>/", InstituteLeadersView.as_view(), name="institute-leaders"),
]
