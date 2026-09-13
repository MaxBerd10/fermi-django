from xml.sax.saxutils import escape

from django.conf import settings
from django.http import HttpResponse

from apps.news.models import NewsPost

from .models import MenuItem

# Matches buildNewsDetailHref()'s default in frontend/src/lib/newsSection.ts --
# individual article pages aren't in the menu tree (only their category is),
# so this is the one URL shape reconstructed here rather than read verbatim
# off a MenuItem.
NEWS_DETAIL_MENU_ID = 72


def _menu_item_urls():
    # `#` and "" are dead-end / decorative entries in the real site's own nav
    # (dropdown headers with no destination) -- not real pages, so they don't
    # belong in a sitemap. Every other `url` here is already the exact,
    # real, reachable frontend path (see MenuItem's own docstring), so no
    # per-content-type URL reconstruction is needed for anything already in
    # the menu tree (departments, faculties, static/"blog" pages, news
    # categories, leaders, gallery, etc.).
    return (
        MenuItem.objects.exclude(url="").exclude(url="#").values_list("url", flat=True).distinct()
    )


def _news_detail_entries():
    # The only content type genuinely absent from the menu tree: each
    # article's own detail page. `published_at` is a required field (every
    # row is "published" -- see NewsPost's own fields), so no draft filter
    # is needed, and it doubles as a real, meaningful <lastmod>.
    for slug, published_at in NewsPost.objects.values_list("slug", "published_at"):
        yield f"/detail/{slug}?menuId={NEWS_DETAIL_MENU_ID}", published_at


def sitemap_xml(request):
    base = settings.FRONTEND_URL.rstrip("/")
    entries: list[tuple[str, str | None]] = [(path, None) for path in _menu_item_urls()]
    entries.extend(
        (path, published_at.date().isoformat()) for path, published_at in _news_detail_entries()
    )

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for path, lastmod in entries:
        lines.append("<url>")
        lines.append(f"<loc>{escape(base + path)}</loc>")
        if lastmod:
            lines.append(f"<lastmod>{lastmod}</lastmod>")
        lines.append("</url>")
    lines.append("</urlset>")

    return HttpResponse("".join(lines), content_type="application/xml")
