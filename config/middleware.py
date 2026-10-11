from django.conf import settings
from django.http import Http404


class DjangoAdminGateMiddleware:
    """Django's own admin (/django-admin/) is closed unless DJANGO_ADMIN_ENABLED is switched on.

    The site is managed through its own admin panel (/admin/, API under /api/v1/admin/); nobody logs in to the stock
    Django admin, so leaving its login page open only adds a second door to guard. Checked per request, so the
    setting can be flipped by an environment change and a restart, with no code change."""

    PREFIX = "/django-admin"

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if not settings.DJANGO_ADMIN_ENABLED and (path == self.PREFIX or path.startswith(self.PREFIX + "/")):
            raise Http404
        return self.get_response(request)
