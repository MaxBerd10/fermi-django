from django.db.models import Q
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.admin_api.uz_script import to_latin
from apps.menu.models import MenuItem
from apps.news.models import NewsPost

# Cap results per section -- this is a simple substring search across a
# fixed, non-huge dataset, not a paged results feed (the frontend renders
# both sections in full on one page, no "load more").
_MAX_RESULTS = 20


_MAX_TERMS = 6


def _terms(q):
    return q.split()[:_MAX_TERMS]


def _term_matches(term, uz_fields, other_fields):
    """One search word against a record: any of its fields contains the word. An Uzbek field is also tried
    with the word converted to Latin, so a query typed in Cyrillic Uzbek still finds the (Latin) Uzbek text."""
    latin = to_latin(term)
    condition = Q()
    for field in uz_fields:
        condition |= Q(**{f"{field}__icontains": term})
        if latin != term:
            condition |= Q(**{f"{field}__icontains": latin})
    for field in other_fields:
        condition |= Q(**{f"{field}__icontains": term})
    return condition


def _all_terms(terms, uz_fields, other_fields):
    """Every word of the query must appear (in any field) -- word order and endings don't matter, so
    "konferensiya tillar" finds "Tillar konferensiyasi materiallari"."""
    condition = Q()
    for term in terms:
        condition &= _term_matches(term, uz_fields, other_fields)
    return condition


def _matching_news_posts(q):
    terms = _terms(q)
    published = NewsPost.objects.published()
    # Posts whose TITLE matches come first, then the ones that only match in the excerpt.
    in_title = list(
        published.filter(_all_terms(terms, ["title_uz"], ["title_ru", "title_en"])).order_by("-published_at")[:_MAX_RESULTS]
    )
    posts = in_title
    if len(posts) < _MAX_RESULTS:
        seen = {post.id for post in posts}
        in_text = published.filter(
            _all_terms(terms, ["title_uz", "excerpt_uz"], ["title_ru", "title_en", "excerpt_ru", "excerpt_en"])
        ).exclude(id__in=seen).order_by("-published_at")[: _MAX_RESULTS - len(posts)]
        posts = posts + list(in_text)

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
        .filter(_all_terms(_terms(q), ["label_uz"], ["label_ru", "label_en"]))
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
    news posts and generic content pages: every word of the query must match somewhere, titles rank before
    excerpts; not full-text ranked search."""

    def get(self, request):
        q = request.query_params.get("q", "").strip()
        if not q:
            return Response({"posts": [], "pages": []})

        return Response({
            "posts": _matching_news_posts(q),
            "pages": _matching_blog_pages(q),
        })
