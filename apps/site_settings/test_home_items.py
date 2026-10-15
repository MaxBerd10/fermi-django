"""Editable home-page lists (partners, projects, student quotes, figures, "why us" cards): the seed carries the
content the frontend used to hard-code, the public JSON serves only what is shown, and staff manage each list."""
import base64

import pytest
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.media_lib.models import Image
from apps.site_settings.models import HomeItem

PNG = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")

PUBLIC = "/api/v1/home-sections"
ADMIN = "/api/v1/admin"


@pytest.fixture
def admin_client(db):
    user = get_user_model().objects.create_user(username="homeeditor", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def test_the_seed_carries_todays_content(db, client):
    data = client.get(PUBLIC).json()

    assert [len(data[k]) for k in ("partners", "projects", "voices", "facts", "why")] == [8, 6, 4, 4, 4]
    assert data["partners"][0]["name"]["ru"] == "Портал Президента"
    assert data["voices"][0]["name"]["uz"] == "Madina Aliyeva"
    assert data["facts"][0]["value"] == "92%"
    assert data["why"][1]["metric"] == "275+"
    live = [p for p in data["projects"] if p["url"]]
    assert [p["name"]["uz"] for p in live] == ["AiShifokor", "iMentor", "iTest"]
    assert data["projects"][0]["img"] == "/images/projects/aishifokor.jpg"


def test_hidden_items_are_not_served_and_a_blank_language_shows_uzbek(db, client, admin_client):
    HomeItem.objects.filter(section="partner").delete()
    HomeItem.objects.create(section="partner", order=1, title_uz="Faqat o'zbekcha", url="https://a.uz")
    HomeItem.objects.create(section="partner", order=2, title_uz="Yashirin", is_active=False)

    partners = client.get(PUBLIC).json()["partners"]

    assert [p["name"] for p in partners] == [{"uz": "Faqat o'zbekcha", "ru": "Faqat o'zbekcha", "en": "Faqat o'zbekcha"}]


def test_staff_create_edit_reorder_and_delete_a_partner(admin_client, client):
    created = admin_client.post(
        f"{ADMIN}/home-partners",
        {"title_uz": "Yangi hamkor", "title_ru": "Новый партнёр", "url": " https://x.uz ", "icon": "ri-links-line"},
        format="json",
    )
    assert created.status_code == 201
    pid = created.data["id"]
    assert created.data["order"] == 9 and created.data["hidden"] == 0  # appended after the seeded 8, shown

    assert admin_client.put(f"{ADMIN}/home-partners/{pid}", {"title_uz": "Hamkor 2", "order": 0, "hidden": 1}, format="json").status_code == 200
    assert pid not in [p["id"] for p in client.get(PUBLIC).json()["partners"]]  # hidden

    admin_client.put(f"{ADMIN}/home-partners/{pid}", {"hidden": 0}, format="json")
    assert client.get(PUBLIC).json()["partners"][0]["name"]["uz"] == "Hamkor 2"  # order 0 sorts before the seeded 1..8

    assert admin_client.delete(f"{ADMIN}/home-partners/{pid}").status_code == 204
    assert pid not in [p["id"] for p in client.get(PUBLIC).json()["partners"]]


def test_each_resource_lists_only_its_own_section(admin_client):
    counts = {r: admin_client.get(f"{ADMIN}/home-{r}").data["count"] for r in ("partners", "projects", "voices", "facts", "why")}
    assert counts == {"partners": 8, "projects": 6, "voices": 4, "facts": 4, "why": 4}
    assert admin_client.get(f"{ADMIN}/home-partners", {"search": "zzz-yoq"}).data["count"] == 0
    assert admin_client.get(f"{ADMIN}/home-partners", {"search": "hemis"}).data["count"] == 1


def test_a_project_keeps_its_built_in_picture_until_an_upload_replaces_it(admin_client, client):
    project = HomeItem.objects.get(section="project", title_uz="iMentor")
    opened = admin_client.get(f"{ADMIN}/home-projects/{project.pk}")
    assert opened.data["img"] == "/images/projects/imentor.jpg"

    # saving the form untouched echoes the built-in path back
    admin_client.put(f"{ADMIN}/home-projects/{project.pk}", {"img": opened.data["img"], "title_uz": "iMentor"}, format="json")
    project.refresh_from_db()
    assert project.image_path == "/images/projects/imentor.jpg" and project.image is None

    uploaded = Image(alt_text="")
    uploaded.file.save("new.png", ContentFile(PNG), save=True)
    admin_client.put(f"{ADMIN}/home-projects/{project.pk}", {"img": uploaded.file.name}, format="json")
    project.refresh_from_db()
    assert project.image is not None and project.image_path == ""
    served = next(p for p in client.get(PUBLIC).json()["projects"] if p["id"] == project.pk)
    assert served["img"].endswith(uploaded.file.url)


def test_a_project_without_a_link_is_served_as_coming_soon(admin_client, client):
    admin_client.put(f"{ADMIN}/home-projects/{HomeItem.objects.get(title_uz='iTest').pk}", {"url": ""}, format="json")
    served = {p["name"]["uz"]: p["url"] for p in client.get(PUBLIC).json()["projects"]}
    assert served["iTest"] is None and served["iMentor"] == "https://imentor.uz"


def test_only_staff_may_use_the_admin_resources(db, client):
    for resource in ("partners", "projects", "voices", "facts", "why"):
        assert client.get(f"{ADMIN}/home-{resource}").status_code in (401, 403)
        assert client.post(f"{ADMIN}/home-{resource}", {"title_uz": "x"}, format="json").status_code in (401, 403)


def test_the_seed_keeps_wording_editors_already_changed_in_site_texts(db):
    import importlib

    from django.apps import apps as django_apps

    from apps.site_settings.models import SiteText

    seed = importlib.import_module("apps.site_settings.migrations.0005_seed_home_items").seed
    HomeItem.objects.all().delete()
    SiteText.objects.create(key="partners.item1.name", text_uz="Prezident sayti", text_ru="")
    SiteText.objects.create(key="voices.fact2.value", text_uz="5.0")

    seed(django_apps, None)

    first = HomeItem.objects.get(section="partner", order=1)
    assert first.title_uz == "Prezident sayti" and first.title_ru == "Портал Президента"  # blank language keeps the default
    assert HomeItem.objects.get(section="fact", order=2).value == "5.0"
    count = HomeItem.objects.count()
    seed(django_apps, None)  # a second run changes nothing
    assert HomeItem.objects.count() == count == 26


def test_the_six_quick_buttons_are_seeded_and_served(db, client):
    tools = client.get(PUBLIC).json()["tools"]
    assert [t["url"] for t in tools] == [
        "/virtual-reception/17", "/qabul", "#pathfinder", "https://online-imtixon.uz", "https://hemis.fjsti.uz", "/aloqa",
    ]
    assert tools[1]["accent"] is True and tools[0]["accent"] is False
    assert tools[0]["title"]["ru"] == "Виртуальная приёмная" and tools[0]["desc"]["en"].startswith("Send an official")
    only = client.get(PUBLIC, {"only": "tools"}).json()
    assert list(only) == ["tools"] and len(only["tools"]) == 6


def test_staff_edit_a_quick_button_and_move_the_highlight(admin_client, client):
    tool = HomeItem.objects.get(section="tool", url="/aloqa")
    opened = admin_client.get(f"{ADMIN}/home-tools/{tool.pk}").json()
    assert opened["accent"] == 0
    opened.update({"accent": 1, "url": "/aloqa/xabar", "title_uz": "Bog'lanish"})
    assert admin_client.put(f"{ADMIN}/home-tools/{tool.pk}", opened, format="json").status_code == 200
    served = next(t for t in client.get(PUBLIC, {"only": "tools"}).json()["tools"] if t["id"] == tool.pk)
    assert served["accent"] is True and served["url"] == "/aloqa/xabar" and served["title"]["uz"] == "Bog'lanish"
    opened.update({"accent": 0})
    admin_client.put(f"{ADMIN}/home-tools/{tool.pk}", opened, format="json")
    tool.refresh_from_db()
    assert tool.value == ""
    assert admin_client.get(f"{ADMIN}/home-partners").json()["count"] == 8  # the other lists are untouched


def test_the_tool_seed_keeps_wording_editors_already_changed(db):
    import importlib

    from django.apps import apps as django_apps
    from apps.site_settings.models import SiteText

    HomeItem.objects.filter(section="tool").delete()
    SiteText.objects.create(key="hero.tools.hemis.title", text_uz="HEMIS kabineti", text_ru="", text_en="")
    importlib.import_module("apps.site_settings.migrations.0007_seed_home_tools").seed(django_apps, None)
    hemis = HomeItem.objects.get(section="tool", url="https://hemis.fjsti.uz")
    assert hemis.title_uz == "HEMIS kabineti" and hemis.title_ru == "HEMIS"


def test_a_dangerous_link_is_refused(admin_client):
    for bad in ("javascript:alert(1)", "data:text/html,x", "//evil.example", "  JaVaScRiPt:alert(1)"):
        res = admin_client.post(f"{ADMIN}/home-tools", {"title_uz": "x", "url": bad}, format="json")
        assert res.status_code == 400, bad
    for good in ("/qabul", "#pathfinder", "https://hemis.fjsti.uz", "tel:+998950622345", "mailto:info@fjsti.uz"):
        assert admin_client.post(f"{ADMIN}/home-tools", {"title_uz": "ok", "url": good}, format="json").status_code == 201
