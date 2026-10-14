"""admin/dashboard -- what the admin start page shows at a glance: how many visitor messages nobody has opened yet
(per inbox) and the latest news posts (drafts included), so the editors see what needs attention without opening
every list."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

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
