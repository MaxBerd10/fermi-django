from django.urls import path

from .views import SiteSettingsView, SiteTextsView

urlpatterns = [
    path("settings", SiteSettingsView.as_view()),
    path("site-texts", SiteTextsView.as_view()),
]
