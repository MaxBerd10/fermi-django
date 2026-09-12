from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.departments.urls")),
    path("api/v1/", include("apps.content.urls")),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.news.urls")),
    path("api/v1/", include("apps.faculties.urls")),
    path("api/v1/", include("apps.menu.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
