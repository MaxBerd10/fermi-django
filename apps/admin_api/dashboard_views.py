"""admin/dashboard -- what the admin start page shows at a glance: how many visitor messages nobody has opened yet
(per inbox) and the latest news posts (drafts included), so the editors see what needs attention without opening
every list."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.content.models import Page
from apps.departments.models import Department
from apps.faculties.models import Faculty
from apps.forms.models import AcceptanceSubmission, ContactSubmission, ContestSubmission, VirtualSubmission
from apps.news.models import NewsPost

from .common import IsAdminStaff

INBOXES = (
    ("contacts", ContactSubmission),
    ("acceptances", AcceptanceSubmission),
    ("virtual-submissions", VirtualSubmission),
    ("contest-submissions", ContestSubmission),
)


def unread_counts() -> dict[str, int]:
    return {resource: model.objects.filter(is_read=False).count() for resource, model in INBOXES}


class AdminDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsAdminStaff]

    def get(self, request):
        latest = NewsPost.objects.order_by("-published_at", "-id")[:6]
        return Response(
            {
                "unread": unread_counts(),
                "drafts": NewsPost.objects.filter(is_published=False).count(),
                "news": [
                    {
                        "id": post.pk,
                        "title": post.title_uz,
                        "published_at": post.published_at,
                        "hidden": 0 if post.is_published else 1,
                        "views": post.view_count,
                    }
                    for post in latest
                ],
            }
        )


class AdminLocateView(APIView):
    """GET admin/locate?slug=<slug> -- where in the admin panel the page the editor is looking at on the public site is
    edited. Every public page has a slug; a news post, a faculty and a department each own one page, so they open in
    their own editors, anything else in "Sahifalar". `found: false` when no record has that slug."""

    permission_classes = [IsAuthenticated, IsAdminStaff]

    def get(self, request):
        slug = str(request.query_params.get("slug") or "").strip().lower()
        if not slug or len(slug) > 255:
            return Response({"found": False})
        news = NewsPost.objects.filter(slug=slug).first() or NewsPost.objects.filter(page__slug=slug).first()
        if news:
            return Response({"found": True, "kind": "news", "title": news.title_uz, "edit": f"/admin/news/{news.pk}"})
        faculty = Faculty.objects.filter(slug=slug).first() or Faculty.objects.filter(page__slug=slug).first()
        if faculty:
            return Response({"found": True, "kind": "faculty", "title": faculty.name_uz, "edit": f"/admin/faculty/{faculty.pk}"})
        department = Department.objects.filter(slug=slug).first() or Department.objects.filter(page__slug=slug).first()
        if department:
            return Response(
                {"found": True, "kind": "department", "title": department.name_uz, "edit": f"/admin/departments/{department.pk}"}
            )
        page = Page.objects.filter(slug=slug).first()
        if page:
            return Response({"found": True, "kind": "page", "title": page.title_uz, "edit": f"/admin/pages/{page.pk}"})
        return Response({"found": False})
