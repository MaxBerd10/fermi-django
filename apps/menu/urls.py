from django.urls import path
from rest_framework.routers import DefaultRouter

from .sitemap import sitemap_xml
from .views import MenuItemViewSet

router = DefaultRouter()
router.register("menu", MenuItemViewSet, basename="menu")

urlpatterns = [path("sitemap.xml", sitemap_xml, name="sitemap-xml")] + router.urls
