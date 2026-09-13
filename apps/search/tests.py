import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.content.models import Page
from apps.menu.models import MenuItem
from apps.news.models import NewsPost


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def news_post(db):
    page = Page.objects.create(slug="qabul-jarayoni")
    return NewsPost.objects.create(
        slug="qabul-jarayoni",
        title_uz="Qabul jarayoni boshlandi",
        title_ru="Начался приём",
        title_en="Admissions have started",
        excerpt_uz="Qisqacha", excerpt_ru="Кратко", excerpt_en="Short",
        page=page,
        published_at=timezone.now(),
    )


@pytest.fixture
def blog_menu_item(db):
    return MenuItem.objects.create(
        label_uz="Qabul qoidalari", label_ru="Правила приёма", label_en="Admission rules",
        url="/blog/1827/qabul-qoidalari",
    )


def test_search_matches_news_post_by_title(client, news_post):
    res = client.get("/api/v1/search", {"q": "qabul"})
    assert res.status_code == 200
    assert res.data["posts"] == [
        {
            "id": news_post.id,
            "slug": "qabul-jarayoni",
            "title": {"uz": "Qabul jarayoni boshlandi", "ru": "Начался приём", "en": "Admissions have started"},
            "content": {"uz": "Qisqacha", "ru": "Кратко", "en": "Short"},
        }
    ]


def test_search_matches_blog_menu_item_by_label(client, blog_menu_item):
    res = client.get("/api/v1/search", {"q": "qoidalari"})
    assert res.data["pages"] == [
        {
            "slug": "qabul-qoidalari",
            "title": {"uz": "Qabul qoidalari", "ru": "Правила приёма", "en": "Admission rules"},
        }
    ]


def test_search_ignores_non_blog_menu_items(client, db):
    MenuItem.objects.create(
        label_uz="Kafedra qoidalari", label_ru="X", label_en="X", url="/departments/38/kafedra-qoidalari",
    )
    res = client.get("/api/v1/search", {"q": "qoidalari"})
    assert res.data["pages"] == []


def test_search_with_empty_query_returns_empty_results(client, db):
    res = client.get("/api/v1/search", {"q": ""})
    assert res.data == {"posts": [], "pages": []}


def test_search_with_no_query_param_returns_empty_results(client, db):
    res = client.get("/api/v1/search")
    assert res.data == {"posts": [], "pages": []}
