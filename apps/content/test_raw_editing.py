"""Legacy pages (raw HTML, often followed by PDF cards) are editable from the admin without risking their markup:
simple pieces are editable, everything else is an untouchable chip, an untouched language is never rewritten."""
import re

import pytest
from django.core.files.base import ContentFile
from django.core.exceptions import ValidationError

from apps.content import raw_editing
from apps.content.admin_content import blocks_to_html, write_blocks_from_html
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document

LANGS = ("uz", "ru", "en")
TABLE = "<table><tbody><tr><td>A</td><td>B</td></tr></tbody></table>"
FRAME = '<iframe src="https://www.youtube.com/embed/abc" width="560"></iframe>'
LEGACY = (
    '<p><span style="font-size:16px"><a href="https://fermi.uz/media/x/Nizom.pdf">Nizom</a></span></p>\r\n'
    "<hr />\r\n"
    "<p>Oddiy matn</p>\r\n"
    f"{TABLE}\r\n"
    f"{FRAME}\r\n"
    '<div class="row"><div class="col">Ustun</div></div>'
)


def _block(page, order, block_type, data):
    block = ContentBlock(page=page, order=order, block_type=block_type, data=data)
    block.full_clean()
    block.save()
    return block


def _raw(html_uz, html_ru=None, html_en=None):
    return {"uz": {"html": html_uz, "slug": "s"}, "ru": {"html": html_ru or html_uz, "slug": "s"}, "en": {"html": html_en or html_uz, "slug": "s"}}


@pytest.fixture
def page(db):
    return Page.objects.create(slug="s")


@pytest.fixture
def document(db):
    doc = Document(title="Nizom")
    doc.file.save("nizom.pdf", ContentFile(b"%PDF-1.4 test"), save=True)
    return doc


def _doc_block(page, order, document, caption="Nizom"):
    return _block(page, order, "document", {lang: {"style": "card", "document_id": document.id, "caption": caption} for lang in LANGS})


def _editor(page):
    return {lang: blocks_to_html(page, lang, open_raw=True) for lang in LANGS}


def _save(page, html_by_lang):
    write_blocks_from_html(page, html_by_lang, open_raw=True)


def _snapshot(page):
    return [(b.id, b.block_type, b.order, b.data) for b in ContentBlock.objects.filter(page=page).order_by("order")]


def test_capability_needs_raw_html_and_only_non_text_blocks_besides(page, document):
    assert not raw_editing.is_raw_capable(page)  # empty
    raw = _block(page, 1, "raw_html", _raw("<p>x</p>"))
    assert raw_editing.is_raw_capable(page)
    _doc_block(page, 2, document)
    assert raw_editing.is_raw_capable(page)
    _block(page, 3, "paragraph", {lang: {"text": "Matn"} for lang in LANGS})
    assert not raw_editing.is_raw_capable(page)  # a text block: the older block-by-block bridge owns that page


def test_simple_pieces_are_editable_and_the_rest_are_numbered_chips(page):
    block = _block(page, 1, "raw_html", _raw(LEGACY))

    html = blocks_to_html(page, "uz", open_raw=True)

    assert "Oddiy matn" in html and "Nizom.pdf" in html and "<hr" in html
    chips = re.findall(r'data-preserved-block="(raw:\d+:\d+)"', html)
    assert len(chips) == 3 and all(c.startswith(f"raw:{block.id}:") for c in chips)
    assert "<table" not in html and "<iframe" not in html and "col" not in html  # nothing exotic reaches the editor


def test_without_open_raw_the_page_is_still_one_locked_chip(page):
    _block(page, 1, "raw_html", _raw(LEGACY))

    html = blocks_to_html(page, "uz")

    assert html.count("data-preserved-block") == 1 and "Oddiy matn" not in html


def test_saving_untouched_changes_nothing_byte_for_byte(page, document):
    _block(page, 1, "raw_html", _raw(LEGACY))
    _doc_block(page, 2, document)
    before = _snapshot(page)

    _save(page, _editor(page))

    assert _snapshot(page) == before


def test_editing_one_paragraph_keeps_every_other_piece_byte_for_byte(page):
    _block(page, 1, "raw_html", _raw(LEGACY))
    posted = _editor(page)
    posted["uz"] = posted["uz"].replace("Oddiy matn", "Yangi matn")

    _save(page, posted)

    block = ContentBlock.objects.get(page=page)
    uz = block.data["uz"]["html"]
    assert "Yangi matn" in uz and "Oddiy matn" not in uz
    assert TABLE in uz and FRAME in uz and '<div class="row"><div class="col">Ustun</div></div>' in uz  # chips came back whole
    assert block.data["ru"]["html"] == LEGACY and block.data["en"]["html"] == LEGACY  # untouched languages: exactly as stored


def test_each_language_is_edited_on_its_own(page):
    _block(page, 1, "raw_html", _raw(LEGACY, LEGACY.replace("Oddiy matn", "Obychnyj tekst"), LEGACY.replace("Oddiy matn", "Plain text")))
    posted = _editor(page)
    posted["ru"] = posted["ru"].replace("Obychnyj tekst", "Novyj tekst")

    _save(page, posted)

    block = ContentBlock.objects.get(page=page)
    assert "Novyj tekst" in block.data["ru"]["html"] and TABLE in block.data["ru"]["html"]
    assert block.data["uz"]["html"] == LEGACY and "Plain text" in block.data["en"]["html"]


def test_deleting_a_raw_chip_removes_that_piece_only(page):
    _block(page, 1, "raw_html", _raw(LEGACY))
    posted = _editor(page)
    table_chip = re.search(r'<div[^>]*raw:\d+:\d+[^>]*>Jadval[^<]*</div>', posted["uz"]).group(0)
    posted = {lang: html.replace(table_chip, "") for lang, html in posted.items()}

    _save(page, posted)

    uz = ContentBlock.objects.get(page=page).data["uz"]["html"]
    assert TABLE not in uz and FRAME in uz and "Oddiy matn" in uz


def test_a_pdf_card_survives_a_text_edit_and_keeps_its_id(page, document):
    _block(page, 1, "raw_html", _raw(LEGACY))
    card = _doc_block(page, 2, document)
    posted = _editor(page)
    posted["uz"] = posted["uz"].replace("Oddiy matn", "Boshqa matn")

    _save(page, posted)

    assert ContentBlock.objects.filter(pk=card.pk, block_type="document").exists()
    assert [b.block_type for b in ContentBlock.objects.filter(page=page).order_by("order")] == ["raw_html", "document"]


def test_deleting_the_pdf_chip_deletes_the_card_and_adding_a_file_adds_a_new_one(page, document):
    _block(page, 1, "raw_html", _raw("<p>Matn</p>"))
    card = _doc_block(page, 2, document)
    posted = _editor(page)
    chip = re.search(rf'<div[^>]*data-preserved-block="{card.id}"[^>]*>.*?</div>', posted["uz"]).group(0)
    new_file = Document(title="Yangi")
    new_file.file.save("yangi.pdf", ContentFile(b"%PDF-1.4 new"), save=True)
    marker = f'<div data-new-document="{new_file.file.name}" data-title="Yangi hujjat">x</div>'
    posted = {"uz": posted["uz"].replace(chip, marker), "ru": posted["ru"].replace(chip, ""), "en": posted["en"].replace(chip, "")}

    _save(page, posted)

    blocks = list(ContentBlock.objects.filter(page=page).order_by("order"))
    assert not ContentBlock.objects.filter(pk=card.pk).exists()
    assert [b.block_type for b in blocks] == ["raw_html", "document"]
    assert blocks[1].data["uz"]["document_id"] == Document.objects.get(file=new_file.file.name).id
    assert blocks[1].data["uz"]["caption"] == "Yangi hujjat"


def test_moving_a_pdf_chip_above_the_text_reorders_the_blocks(page, document):
    _block(page, 1, "raw_html", _raw("<p>Birinchi</p>"))
    card = _doc_block(page, 2, document)
    posted = _editor(page)
    chip = re.search(rf'<div[^>]*data-preserved-block="{card.id}"[^>]*>.*?</div>', posted["uz"]).group(0)
    posted = {lang: chip + "\n" + html.replace(chip, "") for lang, html in posted.items()}

    _save(page, posted)

    assert [b.block_type for b in ContentBlock.objects.filter(page=page).order_by("order")] == ["document", "raw_html"]


def test_text_typed_between_two_cards_becomes_its_own_run(page, document):
    _block(page, 1, "raw_html", _raw("<p>Tepada</p>"))
    first = _doc_block(page, 2, document, "Bir")
    second = _doc_block(page, 3, document, "Ikki")
    posted = _editor(page)
    chip1 = re.search(rf'<div[^>]*data-preserved-block="{first.id}"[^>]*>.*?</div>', posted["uz"]).group(0)
    posted = {lang: html.replace(chip1, chip1 + "\n<p>Orada</p>") for lang, html in posted.items()}

    _save(page, posted)

    blocks = list(ContentBlock.objects.filter(page=page).order_by("order"))
    assert [b.block_type for b in blocks] == ["raw_html", "document", "raw_html", "document"]
    assert "Tepada" in blocks[0].data["uz"]["html"] and "Orada" in blocks[2].data["uz"]["html"]
    assert "Orada" in blocks[2].data["ru"]["html"]  # ru/en follow uz's structure, paired by position


def test_emptying_a_language_leaves_a_valid_blank_block(page):
    _block(page, 1, "raw_html", _raw("<p>Matn</p>"))
    posted = _editor(page)
    posted["en"] = ""

    _save(page, posted)

    block = ContentBlock.objects.get(page=page)
    assert block.data["en"]["html"] == "<p></p>" and block.data["uz"]["html"] == "<p>Matn</p>"


def test_a_stale_form_for_a_page_that_changed_shape_is_refused_not_applied(page):
    block = _block(page, 1, "raw_html", _raw(LEGACY))
    posted = _editor(page)
    _block(page, 2, "paragraph", {lang: {"text": "Yangi blok"} for lang in LANGS})  # someone else added a text block

    with pytest.raises(ValidationError):
        _save(page, posted)

    assert ContentBlock.objects.filter(pk=block.pk).exists()


def test_scripts_and_javascript_links_stay_out_of_the_editable_pieces(page):
    _block(page, 1, "raw_html", _raw('<p><a href="javascript:alert(1)">x</a></p><script>alert(2)</script><p onclick="a()">y</p>'))

    html = blocks_to_html(page, "uz", open_raw=True)

    assert "javascript:" not in html and "<script" not in html and "onclick" not in html
    assert html.count("data-preserved-block") == 3


# --- through the admin API --------------------------------------------------------------------------------

@pytest.fixture
def admin_client(db):
    from django.contrib.auth import get_user_model
    from rest_framework.test import APIClient
    from rest_framework_simplejwt.tokens import RefreshToken

    user = get_user_model().objects.create_user(username="pageeditor", password="x", is_staff=True)
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {RefreshToken.for_user(user).access_token}")
    return client


def test_the_admin_api_opens_a_legacy_page_and_saves_an_edit(admin_client, page):
    from apps.menu.models import MenuItem

    block = _block(page, 1, "raw_html", _raw(LEGACY))
    MenuItem.objects.create(label_uz="Monografiya", label_ru="Монография", label_en="Monograph", url="/blog/2042/s", order=1)

    row = admin_client.get(f"/api/v1/admin/pages/{page.id}").json()
    assert row["raw_editing"] is True and row["menu_title"] == "Monografiya"
    assert "Oddiy matn" in row["content_uz"] and "<table" not in row["content_uz"]

    body = {**row, "content_uz": row["content_uz"].replace("Oddiy matn", "Yangilangan matn")}
    saved = admin_client.put(f"/api/v1/admin/pages/{page.id}", body, format="json")

    assert saved.status_code == 200
    stored = ContentBlock.objects.get(pk=block.pk).data
    assert "Yangilangan matn" in stored["uz"]["html"] and TABLE in stored["uz"]["html"]
    assert stored["ru"]["html"] == LEGACY and stored["en"]["html"] == LEGACY


def test_the_page_list_is_searchable_by_menu_label(admin_client, page):
    from apps.menu.models import MenuItem

    _block(page, 1, "raw_html", _raw("<p>x</p>"))
    MenuItem.objects.create(label_uz="Monografiya", label_ru="Монография", label_en="Monograph", url="/blog/2042/s", order=1)
    Page.objects.create(slug="boshqa")

    hit = admin_client.get("/api/v1/admin/pages", {"search": "monograf"}).json()
    miss = admin_client.get("/api/v1/admin/pages", {"search": "zzz-yoq"}).json()

    assert [r["slug"] for r in hit["results"]] == ["s"] and hit["results"][0]["menu_title"] == "Monografiya"
    assert miss["count"] == 0


def test_a_picture_in_a_sized_wrapper_is_editable_but_a_floated_block_is_not(page):
    cover = '<div style="max-width:320px;margin:0 auto 24px"><img src="https://fermi.uz/media/a.jpg" alt="Muqova" width="10" height="20" /></div>'
    floated = '<div style="float:left;width:50%"><img src="https://fermi.uz/media/b.jpg" /></div>'
    _block(page, 1, "raw_html", _raw(cover + floated))

    html = blocks_to_html(page, "uz", open_raw=True)

    assert "a.jpg" in html and "b.jpg" not in html  # the cover is editable, the floated block stays a chip
    assert html.count("data-preserved-block") == 1


def test_the_empty_paragraph_the_editor_leaves_after_a_last_chip_does_not_become_a_block(page, document):
    _block(page, 1, "raw_html", _raw("<p>Matn</p>"))
    _doc_block(page, 2, document)
    posted = {lang: html + "\n<p></p>\n<p>&nbsp;</p>" for lang, html in _editor(page).items()}
    posted["uz"] = posted["uz"].replace("Matn", "Matn 2")

    _save(page, posted)

    assert [b.block_type for b in ContentBlock.objects.filter(page=page).order_by("order")] == ["raw_html", "document"]
