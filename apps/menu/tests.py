import pytest
from rest_framework.test import APIClient

from apps.menu.models import MenuItem


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def menu_tree(db):
    root = MenuItem.objects.create(label_uz="Institut", label_ru="Институт", label_en="Institute", order=1)
    child = MenuItem.objects.create(
        parent=root, label_uz="Kafedralar", label_ru="Кафедры", label_en="Departments", order=1
    )
    MenuItem.objects.create(
        parent=child, label_uz="Akusherlik", label_ru="Акушерство", label_en="Obstetrics",
        url="/departments/38/akusherlik-va-ginekologiya-kafedrasi", order=1,
    )
    # a second top-level item, to prove only roots are listed and ordering holds
    MenuItem.objects.create(label_uz="Qabul", label_ru="Приём", label_en="Admission", order=2)
    return root


def test_menu_only_lists_top_level_items(client, menu_tree):
    res = client.get("/api/v1/menu/")
    assert res.status_code == 200
    assert len(res.data) == 2
    assert [item["label"]["uz"] for item in res.data] == ["Institut", "Qabul"]


def test_menu_nests_children_recursively(client, menu_tree):
    res = client.get("/api/v1/menu/")
    institut = res.data[0]
    assert len(institut["children"]) == 1
    kafedralar = institut["children"][0]
    assert kafedralar["label"]["ru"] == "Кафедры"
    assert len(kafedralar["children"]) == 1
    assert kafedralar["children"][0]["url"] == "/departments/38/akusherlik-va-ginekologiya-kafedrasi"
