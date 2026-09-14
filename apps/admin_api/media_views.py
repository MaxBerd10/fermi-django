"""GET admin/media/list and POST admin/media/upload -- see
frontend/src/api/adminMediaLibrary.ts and admin/components/MediaPicker.tsx.
Browses MEDIA_ROOT directly as a real folder tree (matching the old site's
own upload-a-file-into-a-folder-you-choose model) rather than only ever
listing Image/Document rows -- a picked file's stored value is just its
path, not a foreign key to one of our own tables, so anything already on
disk under MEDIA_ROOT is choosable even if no Image/Document row happens
to reference it."""
import mimetypes
import os

from django.conf import settings
from django.core.files.storage import default_storage
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .common import IsAdminStaff

_IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}


def _safe_join(relative: str) -> str:
    """Resolves a client-supplied path under MEDIA_ROOT, refusing anything
    that would escape it (../, an absolute path, ...)."""
    relative = (relative or "").strip("/")
    root = os.path.realpath(settings.MEDIA_ROOT)
    target = os.path.realpath(os.path.join(root, relative))
    if target != root and not target.startswith(root + os.sep):
        raise ValueError("path escapes MEDIA_ROOT")
    return target


class MediaListView(APIView):
    permission_classes = [IsAuthenticated, IsAdminStaff]

    def get(self, request):
        rel_path = request.query_params.get("path", "")
        try:
            abs_path = _safe_join(rel_path)
        except ValueError:
            abs_path = os.path.realpath(settings.MEDIA_ROOT)
            rel_path = ""

        if not os.path.isdir(abs_path):
            abs_path = os.path.realpath(settings.MEDIA_ROOT)
            rel_path = ""

        folders, files = [], []
        for entry in sorted(os.scandir(abs_path), key=lambda e: e.name.lower()):
            entry_rel = f"{rel_path}/{entry.name}".strip("/")
            if entry.is_dir():
                folders.append({"name": entry.name, "path": entry_rel})
            else:
                ext = os.path.splitext(entry.name)[1].lower()
                files.append({
                    "name": entry.name,
                    "path": entry_rel,
                    "url": request.build_absolute_uri(default_storage.url(entry_rel)),
                    "size": entry.stat().st_size,
                    "isImage": ext in _IMAGE_EXTS,
                })

        parent = "/".join(rel_path.split("/")[:-1]) if rel_path else None
        return Response({
            "currentPath": rel_path,
            "parentPath": parent,
            "folders": folders,
            "files": files,
        })


class MediaUploadView(APIView):
    permission_classes = [IsAuthenticated, IsAdminStaff]
    parser_classes = [MultiPartParser]

    def post(self, request):
        upload = request.FILES.get("file")
        if not upload:
            return Response({"detail": "file talab qilinadi."}, status=400)
        folder = request.data.get("path", "uploads/admin")
        content_type = mimetypes.guess_type(upload.name)[0] or "application/octet-stream"
        saved_path = default_storage.save(f"{folder.strip('/')}/{upload.name}", upload)
        return Response({
            "path": saved_path,
            "url": request.build_absolute_uri(default_storage.url(saved_path)),
            "contentType": content_type,
        }, status=201)
