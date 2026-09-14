from django.conf import settings
from django.contrib import admin
from django.urls import include, path
from django.views.static import serve

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
    path("api/v1/", include("apps.video.urls")),
    path("api/v1/", include("apps.admin_api.urls")),
    path("api/v1/", include("apps.site_settings.urls")),
    path("api/v1/", include("apps.forms.urls")),
    # Not DEBUG-gated (Django's static() helper is a no-op when DEBUG=False,
    # which is exactly what silently 404'd every uploaded image/document/video
    # in production -- see this session's readiness audit). This is a same-box
    # deploy with production-server.mjs proxying "/media/*" straight through to
    # here (see its own streamProxy calls), with no separate nginx-level static
    # file serving in front of it. Fine at this site's traffic scale; move to
    # nginx `alias` or S3/CDN if that ever becomes a bottleneck.
    path("media/<path:path>", serve, {"document_root": settings.MEDIA_ROOT}),
]
