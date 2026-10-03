"""Uzbek text typed in Cyrillic must reach the database -- and the translator -- in Latin."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.admin_api.uz_script import latinize_payload, to_latin
from apps.content.models import ContentBlock, Page
from apps.news.models import NewsPost


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_user(username="uzscript", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


@pytest.mark.parametrize("cyrillic, latin", [
    ("Ўзбекистон", "Oʻzbekiston"),
    ("Фарғона жамоат саломатлиги", "Fargʻona jamoat salomatligi"),
    ("Қабул", "Qabul"),
    ("шаҳар чорсу", "shahar chorsu"),
    ("Елка безова маъно", "Yelka bezova maʼno"),
    ("ТАДБИР", "TADBIR"),
    ("ШАҲАР", "SHAHAR"),
    ("Тадбирлар", "Tadbirlar"),
    ("Юсупова Яна", "Yusupova Yana"),
])
def test_cyrillic_uzbek_becomes_latin(cyrillic, latin):
    assert to_latin(cyrillic) == latin


def test_latin_text_is_untouched_and_conversion_is_idempotent():
    text = "Fargʻona, Oʻzbekiston — 2026-yil 5-oktabr, 120 ta oʻrin"
    assert to_latin(text) == text
    once = to_latin("Қабул 2026")
    assert to_latin(once) == once


def test_cyrillic_lookalikes_inside_a_latin_word_become_the_latin_letter():
    # "bahola" typed with Cyrillic a, o -- looks right on screen, breaks search and translation
    assert to_latin("bаhоlаsh") == "baholash"


def test_html_only_converts_text_between_tags():
    html = '<p class="класс"><strong>Қабул</strong> бошланди</p><img src="/a.png" alt="x">'
    assert to_latin(html) == '<p class="класс"><strong>Qabul</strong> boshlandi</p><img src="/a.png" alt="x">'


def test_payload_walk_converts_only_uzbek_keys():
    body = {
        "title_uz": "Қабул",
        "title_ru": "Приём",
        "data": {"uz": {"text": "Шаҳар", "items": ["бир", "икки"]}, "ru": {"text": "Город"}},
        "id": 5,
    }
    latinize_payload(body)
    assert body["title_uz"] == "Qabul"
    assert body["title_ru"] == "Приём"          # ru stays Russian
    assert body["data"]["uz"] == {"text": "Shahar", "items": ["bir", "ikki"]}
    assert body["data"]["ru"]["text"] == "Город"
    assert body["id"] == 5


def test_news_saved_with_cyrillic_uzbek_is_stored_in_latin(admin_client, db):
    res = admin_client.post("/api/v1/admin/news", {
        "title_uz": "Тадбир ўтказилди",
        "title_ru": "Мероприятие прошло",
        "content_uz": "<p>Қабул бошланди</p>",
        "content_ru": "<p>Приём начался</p>",
    }, format="json")
    assert res.status_code == 201, res.content
    post = NewsPost.objects.get(pk=res.data["id"])
    assert post.title_uz == "Tadbir oʻtkazildi"
    assert not any("Ѐ" <= ch <= "ӿ" for ch in post.title_uz)
    assert post.title_ru.startswith("Меро")             # Russian untouched
    uz_block = ContentBlock.objects.get(page=post.page, order=1)
    assert uz_block.data["uz"]["text"] == "Qabul boshlandi"
    assert uz_block.data["ru"]["text"] == "Приём начался"


def test_public_endpoints_are_not_rewritten(client, db):
    """Only /api/v1/admin/ is touched -- a public form field that happens to end in _uz is not."""
    res = client.post("/api/v1/auth/login", {"username": "админ", "password": "x"}, content_type="application/json")
    assert res.status_code == 401
