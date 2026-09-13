from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.menu.models import MenuItem
from apps.news.models import NewsPost

# Cap results per section -- this is a simple substring search across a
# fixed, non-huge dataset, not a paged results feed (the frontend renders
# both sections in full on one page, no "load more").
_MAX_RESULTS = 20


def _matching_news_posts(q):
    posts = NewsPost.objects.filter(
        Q(title_uz__icontains=q) | Q(title_ru__icontains=q) | Q(title_en__icontains=q)
        | Q(excerpt_uz__icontains=q) | Q(excerpt_ru__icontains=q) | Q(excerpt_en__icontains=q)
    ).order_by("-published_at")[:_MAX_RESULTS]

    return [
        {
            "id": post.id,
            "slug": post.slug,
            "title": {"uz": post.title_uz, "ru": post.title_ru, "en": post.title_en},
            # Matches what the frontend's own listNews() mapping already puts in
            # NewsArticle.content for list items -- the excerpt, not full blocks
            # (search results don't fetch each post's Page/ContentBlocks).
            "content": {"uz": post.excerpt_uz, "ru": post.excerpt_ru, "en": post.excerpt_en},
        }
        for post in posts
    ]


def _matching_blog_pages(q):
    # Generic "/blog/:menuId/:slug" content pages: MenuItem.label is already
    # the real, displayed title for these (see frontend's BlogPage.tsx ->
    # findTitleBySlug, which looks title up the same way -- off the menu
    # entry, not the Page itself, which has no title field of its own).
    items = (
        MenuItem.objects.filter(url__startswith="/blog/")
        .filter(Q(label_uz__icontains=q) | Q(label_ru__icontains=q) | Q(label_en__icontains=q))
        .order_by("order", "id")
    )

    results = []
    seen_slugs = set()
    for item in items:
        slug = item.url.rstrip("/").rsplit("/", 1)[-1]
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        results.append({"slug": slug, "title": {"uz": item.label_uz, "ru": item.label_ru, "en": item.label_en}})
        if len(results) >= _MAX_RESULTS:
            break
    return results


class SearchView(APIView):
    """GET /api/v1/search?q=... -- see frontend/src/api/search.ts and
    SearchResults. A plain substring search (ILIKE via icontains) across
    news posts and generic content pages; not full-text ranked search."""

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"posts": [], "pages": []})

        return Response({
            "posts": _matching_news_posts(q),
            "pages": _matching_blog_pages(q),
        })
