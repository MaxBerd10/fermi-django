"""The page editor shows a table, a YouTube/map embed or a document card as a chip. A chip can now be EDITED (and a new table or embed ADDED): the editor stages the new
payload of every language in a `data-block-json` attribute of the chip (or in a `data-new-block` marker for a new one), as base64 of JSON, and the server applies it when the page
is saved -- validated like any block, and only for blocks of THIS page and of the three types that have a form."""
import base64
import json

import pytest
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from rest_framework.test import APIClient

from apps.content.admin_content import blocks_to_html, write_blocks_from_html
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document

LANGS = ("uz", "ru", "en")


def b64(obj) -> str:
    return base64.b64encode(json.dumps(obj, ensure_ascii=False).encode("utf8")).decode("ascii")


def same(payload):
    return {lang: dict(payload) for lang in LANGS}


@pytest.fixture
def page(db):
    return Page.objects.create(slug="blok-sahifa")


def make_document(name, title):
    doc = Document(title=title)
    doc.file.save(name, ContentFile(b"%PDF-1.4 test"), save=True)
    return doc


@pytest.fixture
def document(db):
    return make_document("x.pdf", "X")


def add(page, order, block_type, data):
    block = ContentBlock(page=page, order=order, block_type=block_type, data=data)
    block.full_clean()
    block.save()
    return block


def chip(block, **attrs):
    extra = "".join(f' {k.replace("_", "-")}="{v}"' for k, v in attrs.items())
    return f'<div data-preserved-block="{block.id}" data-block-type="{block.block_type}"{extra} class="preserved-block">chip</div>'


def save(page, uz, ru=None, en=None):
    write_blocks_from_html(page, {"uz": uz, "ru": ru if ru is not None else uz, "en": en if en is not None else uz})


def table_data(cell="9"):
    return {lang: {"headers": ["A", "B"], "rows": [["1", cell]]} for lang in LANGS}


# ---------------------------------------------------------------- editing a block that exists

def test_an_edited_table_is_saved_in_its_own_place_with_its_own_id(page):
    first = add(page, 1, "paragraph", same({"text": "Oldin"}))
    table = add(page, 2, "table", same({"headers": ["A", "B"], "rows": [["1", "2"]]}))
    html = f"<p>Oldin</p>{chip(table, data_block_json=b64(table_data('9')))}"

    save(page, html)

    table.refresh_from_db()
    assert table.order == 2 and table.data["uz"]["rows"] == [["1", "9"]]
    assert ContentBlock.objects.get(pk=first.pk).order == 1


def test_a_table_may_have_group_headings_and_every_language_its_own_words(page):
    table = add(page, 1, "table", same({"headers": ["A", "B"], "rows": [["1", "2"]]}))
    data = {lang: {"headers": ["Jami", "Rus"], "rows": [["1", "2"]], "header_groups": [{"label": f"Guruh {lang}", "span": 2}]} for lang in LANGS}

    save(page, chip(table, data_block_json=b64(data)))

    table.refresh_from_db()
    assert table.data["ru"]["header_groups"] == [{"label": "Guruh ru", "span": 2}]


def test_an_invalid_table_is_refused_and_nothing_is_written(page):
    table = add(page, 1, "table", same({"headers": ["A", "B"], "rows": [["1", "2"]]}))
    broken = {lang: {"headers": ["A", "B"], "rows": [["1"]]} for lang in LANGS}  # a row with one cell under two headings

    with pytest.raises(ValidationError):
        save(page, chip(table, data_block_json=b64(broken)))

    table.refresh_from_db()
    assert table.data["uz"]["rows"] == [["1", "2"]]


def test_a_cell_is_plain_text_never_markup(page):
    table = add(page, 1, "table", same({"headers": ["A"], "rows": [["1"]]}))
    data = {lang: {"headers": ["A"], "rows": [["<script>x</script>"]]} for lang in LANGS}

    with pytest.raises(ValidationError):
        save(page, chip(table, data_block_json=b64(data)))


def test_an_edited_document_changes_its_caption_and_style_but_never_its_file(page, document):
    other = make_document("y.pdf", "Y")
    card = add(page, 1, "document", same({"document_id": document.id, "caption": "Eski", "style": "card"}))
    data = {lang: {"caption": f"Yangi {lang}", "style": "button", "document_id": other.id} for lang in LANGS}  # the file id in the request is ignored

    save(page, chip(card, data_block_json=b64(data)))

    card.refresh_from_db()
    assert card.data["ru"] == {"document_id": document.id, "caption": "Yangi ru", "style": "button"}


def test_an_unknown_document_style_is_refused(page, document):
    card = add(page, 1, "document", same({"document_id": document.id, "caption": "Eski", "style": "card"}))
    data = {lang: {"caption": "x", "style": "evil"} for lang in LANGS}

    with pytest.raises(ValidationError):
        save(page, chip(card, data_block_json=b64(data)))


def test_an_edited_youtube_embed_and_an_edited_map(page):
    video = add(page, 1, "embed", same({"provider": "youtube", "video_id": "Mg6MBqg4f5o", "title": "Eski"}))
    place = add(page, 2, "embed", same({"provider": "map", "src": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d6078", "height": 450, "title": "Xarita"}))
    new_video = {lang: {"provider": "youtube", "video_id": "dQw4w9WgXcQ", "title": f"Video {lang}"} for lang in LANGS}
    new_map = {lang: {"provider": "map", "src": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3!1d9999", "height": 500, "title": "Yangi"} for lang in LANGS}

    save(page, chip(video, data_block_json=b64(new_video)) + chip(place, data_block_json=b64(new_map)))

    video.refresh_from_db(), place.refresh_from_db()
    assert video.data["en"]["video_id"] == "dQw4w9WgXcQ" and place.data["uz"]["height"] == 500


@pytest.mark.parametrize("data", [
    {lang: {"provider": "youtube", "video_id": "kisqa", "title": "x"} for lang in LANGS},
    {lang: {"provider": "map", "src": "https://evil.example/maps/embed?pb=!1m18!1m12!1m3", "height": 450} for lang in LANGS},
    {lang: {"provider": "map", "src": "https://www.google.com/maps/embed?pb=!1m18!1m12!1m3", "height": 5} for lang in LANGS},
])
def test_an_invalid_embed_is_refused(page, data):
    video = add(page, 1, "embed", same({"provider": "youtube", "video_id": "Mg6MBqg4f5o", "title": "Eski"}))

    with pytest.raises(ValidationError):
        save(page, chip(video, data_block_json=b64(data)))


def test_all_three_languages_are_required(page):
    table = add(page, 1, "table", same({"headers": ["A"], "rows": [["1"]]}))
    only_uz = {"uz": {"headers": ["A"], "rows": [["2"]]}}

    with pytest.raises(ValidationError):
        save(page, chip(table, data_block_json=b64(only_uz)))


def test_a_block_type_without_a_form_cannot_be_rewritten_through_the_attribute(page):
    gallery = add(page, 1, "gallery", same({"items": [{"image_id": 1, "alt": ""}]}))

    with pytest.raises(ValidationError):
        save(page, chip(gallery, data_block_json=b64(same({"items": []}))))


def test_the_attribute_cannot_reach_a_block_of_another_page(page):
    stranger_page = Page.objects.create(slug="boshqa")
    stranger = add(stranger_page, 1, "table", same({"headers": ["A"], "rows": [["1"]]}))
    mine = add(page, 1, "paragraph", same({"text": "Mening"}))

    save(page, f"<p>Mening</p>{chip(stranger, data_block_json=b64(table_data('9')))}")

    stranger.refresh_from_db()
    assert stranger.data["uz"]["rows"] == [["1"]] and ContentBlock.objects.filter(page=page).count() == 1 and mine.pk


def test_a_garbled_attribute_is_refused_not_ignored(page):
    table = add(page, 1, "table", same({"headers": ["A"], "rows": [["1"]]}))

    with pytest.raises(ValidationError):
        save(page, chip(table, data_block_json="@@not-base64@@"))


# ---------------------------------------------------------------- adding a block

def new_marker(block_type, data):
    return f'<div data-new-block="{b64({"block_type": block_type, "data": data})}" data-block-type="{block_type}" class="preserved-block">yangi</div>'


def test_a_new_table_lands_where_its_chip_was_put(page):
    add(page, 1, "paragraph", same({"text": "Bir"}))
    add(page, 2, "paragraph", same({"text": "Uch"}))

    save(page, f"<p>Bir</p>{new_marker('table', table_data())}<p>Uch</p>")

    kinds = [(b.order, b.block_type) for b in ContentBlock.objects.filter(page=page).order_by("order")]
    assert kinds == [(1, "paragraph"), (2, "table"), (3, "paragraph")]


def test_a_new_youtube_video_and_the_marker_is_not_a_paragraph_in_ru_or_en(page):
    data = {lang: {"provider": "youtube", "video_id": "dQw4w9WgXcQ", "title": "Video"} for lang in LANGS}
    marker = new_marker("embed", data)

    save(page, marker, ru=marker, en=marker)

    blocks = list(ContentBlock.objects.filter(page=page))
    assert [b.block_type for b in blocks] == ["embed"]


def test_an_invalid_new_block_is_refused_and_the_page_is_unchanged(page):
    add(page, 1, "paragraph", same({"text": "Bir"}))
    bad = {lang: {"headers": ["A"], "rows": []} for lang in LANGS}

    with pytest.raises(ValidationError):
        save(page, f"<p>Bir</p>{new_marker('table', bad)}")

    assert ContentBlock.objects.filter(page=page).count() == 1


@pytest.mark.parametrize("block_type", ["gallery", "raw_html", "document", "staff_card", "video"])
def test_only_a_table_and_an_embed_can_be_created_this_way(page, block_type):
    with pytest.raises(ValidationError):
        save(page, new_marker(block_type, table_data()))


def test_a_new_block_survives_the_next_untouched_save(page):
    save(page, new_marker("table", table_data()))
    first = ContentBlock.objects.get(page=page)

    save(page, blocks_to_html(page, "uz"), ru=blocks_to_html(page, "ru"), en=blocks_to_html(page, "en"))

    assert ContentBlock.objects.get(page=page).pk == first.pk


# ---------------------------------------------------------------- what the editor is shown and asks

def test_the_chips_of_editable_blocks_say_they_can_be_edited(page, document):
    add(page, 1, "table", same({"headers": ["A"], "rows": [["1"]]}))
    add(page, 2, "embed", same({"provider": "youtube", "video_id": "Mg6MBqg4f5o", "title": "V"}))
    add(page, 3, "document", same({"document_id": document.id, "caption": "H", "style": "card"}))
    add(page, 4, "gallery", same({"items": [{"image_id": 1, "alt": ""}]}))

    html = blocks_to_html(page, "uz")

    assert html.count("tahrirlash uchun bosing") == 3 and html.count("tahrirlanmaydi") == 1


@pytest.fixture
def admin_client(db):
    from django.contrib.auth import get_user_model
    from rest_framework_simplejwt.tokens import RefreshToken

    user = get_user_model().objects.create_user(username="blok-admin", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def test_the_editor_reads_the_payload_of_a_block_it_is_about_to_edit(admin_client, page):
    table = add(page, 1, "table", same({"headers": ["A"], "rows": [["1"]]}))

    body = admin_client.get(f"/api/v1/admin/pages/{page.pk}/blocks/{table.pk}").json()

    assert body == {"id": table.pk, "block_type": "table", "data": table.data}


def test_a_block_of_another_page_or_without_a_form_is_not_readable_this_way(admin_client, page):
    other = Page.objects.create(slug="boshqa-2")
    stranger = add(other, 1, "table", same({"headers": ["A"], "rows": [["1"]]}))
    gallery = add(page, 1, "gallery", same({"items": [{"image_id": 1, "alt": ""}]}))

    assert admin_client.get(f"/api/v1/admin/pages/{page.pk}/blocks/{stranger.pk}").status_code == 404
    assert admin_client.get(f"/api/v1/admin/pages/{page.pk}/blocks/{gallery.pk}").status_code == 404


def test_the_block_reader_needs_an_admin(page):
    table = add(page, 1, "table", same({"headers": ["A"], "rows": [["1"]]}))

    assert APIClient().get(f"/api/v1/admin/pages/{page.pk}/blocks/{table.pk}").status_code in (401, 403)


def test_saving_an_invalid_block_through_the_page_form_is_a_400_not_a_500(admin_client, page):
    table = add(page, 1, "table", same({"headers": ["A", "B"], "rows": [["1", "2"]]}))
    broken = {lang: {"headers": ["A", "B"], "rows": [["1"]]} for lang in LANGS}
    uz = chip(table, data_block_json=b64(broken))

    response = admin_client.put(f"/api/v1/admin/pages/{page.pk}", {"title_uz": "T", "slug": page.slug, "layout": "default", "content_uz": uz, "content_ru": uz, "content_en": uz}, format="json")

    assert response.status_code == 400
