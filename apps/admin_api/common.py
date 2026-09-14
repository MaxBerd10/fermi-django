"""Shared plumbing for every admin_api resource endpoint -- see
frontend/src/api/admin.ts::adminResource() for the exact contract every
view here has to satisfy (list/get/create/update/delete against
/api/v1/admin/<resource>, all requiring a signed-in staff user)."""
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission

from apps.media_lib.models import Image


class AdminPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "pageSize"
    max_page_size = 200


class IsAdminStaff(BasePermission):
    def has_permission(self, request, view) -> bool:
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


def resolve_or_create_image(path: str | None) -> Image | None:
    """MediaPicker (see its own docstring) hands back a bare storage path,
    not an Image id -- a field bound to it (e.g. NewsPost.cover) needs a
    real Image row to point its FK at. Reuses one if this exact file was
    already picked for something else; otherwise wraps the already-
    uploaded file (it exists on disk via MediaUploadView/MediaLibraryModal
    already) in a new Image row rather than re-uploading it."""
    if not path:
        return None
    path = path.lstrip("/")
    existing = Image.objects.filter(file=path).first()
    if existing:
        return existing
    image = Image(file=path, alt_text="")
    image.save()
    return image
