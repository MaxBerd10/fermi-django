from django.urls import path

from .views import HomeSectionsView, SiteSettingsView, SiteTextsView

urlpatterns = [
    path("settings", SiteSettingsView.as_view()),
    path("site-texts", SiteTextsView.as_view()),
    path("home-sections", HomeSectionsView.as_view()),
]
