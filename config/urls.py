from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    # Not "admin/" -- the deployed frontend's own SPA also claims that path
    # (a leftover, unwired React admin panel from fjstiWeb-main, see its
    # src/admin/*) and nginx routes everything to the frontend by default,
    # so "admin/" would never actually reach Django in production. A
    # distinct prefix lets production-server.mjs proxy it through instead
    # of silently shadowing the real admin.
    path("django-admin/", admin.site.urls),
    path("api/v1/", include("apps.departments.urls")),
    path("api/v1/", include("apps.content.urls")),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.news.urls")),
    path("api/v1/", include("apps.faculties.urls")),
    path("api/v1/", include("apps.menu.urls")),
    path("api/v1/", include("apps.media_lib.urls")),
    path("api/v1/", include("apps.documents.urls")),
    path("api/v1/", include("apps.schedule.urls")),
    path("api/v1/", include("apps.search.urls")),
    path("api/v1/", include("apps.geo.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
