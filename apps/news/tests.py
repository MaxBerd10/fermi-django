import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.content.models import ContentBlock, Page
from apps.news.models import NewsPost


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def news_post(db):
    page = Page.objects.create(slug="test-news-post")
    ContentBlock.objects.create(
        page=page,
        order=1,
        block_type="paragraph",
        data={
            "uz": {"text": "Qisqa xabar."},
            "ru": {"text": "Короткая новость."},
            "en": {"text": "Short news item."},
        },
    )
    return NewsPost.objects.create(
        slug="test-news-post",
        title_uz="Sarlavha",
        title_ru="Заголовок",
        title_en="Headline",
        page=page,
        published_at=timezone.now(),
    )


def test_news_list_returns_localized_title(client, news_post):
    res = client.get("/api/v1/news/")
    assert res.status_code == 200
    item = res.data["results"][0]
    assert item["title"] == {"uz": "Sarlavha", "ru": "Заголовок", "en": "Headline"}


def test_news_detail_includes_page_blocks(client, news_post):
    res = client.get(f"/api/v1/news/{news_post.slug}/")
    assert res.status_code == 200
    assert len(res.data["page"]["blocks"]) == 1
    assert res.data["page"]["blocks"][0]["data"]["ru"]["text"] == "Короткая новость."


def test_news_list_orders_newest_first(client, db):
    old = timezone.now() - timezone.timedelta(days=5)
    new = timezone.now()
    p1 = Page.objects.create(slug="old-post")
    p2 = Page.objects.create(slug="new-post")
    NewsPost.objects.create(slug="old-post", title_uz="Eski", title_ru="Старая", title_en="Old", page=p1, published_at=old)
    NewsPost.objects.create(slug="new-post", title_uz="Yangi", title_ru="Новая", title_en="New", page=p2, published_at=new)

    res = client.get("/api/v1/news/")
    slugs = [item["slug"] for item in res.data["results"]]
    assert slugs == ["new-post", "old-post"]
