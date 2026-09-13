from django.utils import timezone

import pytest
from rest_framework.test import APIClient

from apps.content.models import Page
from apps.menu.models import MenuItem
from apps.news.models import NewsPost


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def menu_items(db):
    root = MenuItem.objects.create(label_uz="Institut", label_ru="Институт", label_en="Institute", order=1)
    MenuItem.objects.create(
        parent=root, label_uz="Kafedra", label_ru="Кафедра", label_en="Department",
        url="/departments/38/test-kafedrasi", order=1,
    )
    # dead-end dropdown headers with no real destination -- must not appear in the sitemap
    MenuItem.objects.create(parent=root, label_uz="Bo'lim", label_ru="Раздел", label_en="Section", url="#", order=2)
    MenuItem.objects.create(parent=root, label_uz="Bo'sh", label_ru="Пусто", label_en="Empty", url="", order=3)
    return root


@pytest.fixture
def news_post(db):
    page = Page.objects.create(slug="test-news-post")
    return NewsPost.objects.create(
        slug="test-news-post",
        title_uz="Sarlavha",
        title_ru="Заголовок",
        title_en="Headline",
        page=page,
        published_at=timezone.now(),
    )


def test_sitemap_includes_real_menu_urls(client, menu_items, settings):
    settings.FRONTEND_URL = "https://fjsti.uz"
    res = client.get("/api/v1/sitemap.xml")
    assert res.status_code == 200
    assert res["Content-Type"] == "application/xml"
    body = res.content.decode()
    assert "<loc>https://fjsti.uz/departments/38/test-kafedrasi</loc>" in body


def test_sitemap_excludes_dead_end_menu_entries(client, menu_items, settings):
    settings.FRONTEND_URL = "https://fjsti.uz"
    res = client.get("/api/v1/sitemap.xml")
    body = res.content.decode()
    assert "<loc>https://fjsti.uz#</loc>" not in body
    assert "<loc>https://fjsti.uz</loc>" not in body


def test_sitemap_includes_news_detail_with_lastmod(client, news_post, settings):
    settings.FRONTEND_URL = "https://fjsti.uz"
    res = client.get("/api/v1/sitemap.xml")
    body = res.content.decode()
    assert "<loc>https://fjsti.uz/detail/test-news-post?menuId=72</loc>" in body
    assert f"<lastmod>{news_post.published_at.date().isoformat()}</lastmod>" in body
