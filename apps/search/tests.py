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


def test_search_words_may_come_in_any_order_and_with_other_endings(client, db):
    """"konferensiya tillar" must find "Tillar konferensiyasi materiallari" -- the whole phrase is not a substring."""
    item = MenuItem.objects.create(
        label_uz="Tillar konferensiyasi materiallari (15.10.2025)", label_ru="Материалы", label_en="Languages",
        url="/blog/1888/tillar-konferensiyasi-materiallari-15102025",
    )
    res = client.get("/api/v1/search", {"q": "konferensiya tillar"})
    assert [p["slug"] for p in res.data["pages"]] == ["tillar-konferensiyasi-materiallari-15102025"]
    assert item.label_uz == res.data["pages"][0]["title"]["uz"]
    # every word has to match: an unrelated extra word narrows the result to nothing
    assert client.get("/api/v1/search", {"q": "konferensiya tillar sport"}).data["pages"] == []


def test_search_title_matches_rank_before_excerpt_only_matches(client, db):
    def post(slug, title, excerpt, hours):
        return NewsPost.objects.create(
            slug=slug, title_uz=title, title_ru="x", title_en="x", excerpt_uz=excerpt, excerpt_ru="x", excerpt_en="x",
            page=Page.objects.create(slug=slug), published_at=timezone.now() - timezone.timedelta(hours=hours),
        )
    post("newer-excerpt-only", "Boshqa yangilik", "Qabul haqida batafsil", 1)
    post("older-title-match", "Qabul boshlandi", "Matn", 5)
    slugs = [p["slug"] for p in client.get("/api/v1/search", {"q": "qabul"}).data["posts"]]
    assert slugs == ["older-title-match", "newer-excerpt-only"]


def test_search_typed_in_cyrillic_uzbek_finds_latin_uzbek_text(client, db):
    MenuItem.objects.create(label_uz="Qabul qoidalari", label_ru="a", label_en="b", url="/blog/1/qabul-qoidalari")
    cyrillic = "қабул"   # қабул
    assert [p["slug"] for p in client.get("/api/v1/search", {"q": cyrillic}).data["pages"]] == ["qabul-qoidalari"]
