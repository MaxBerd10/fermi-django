"""The admin editor's HTML <-> blocks bridge must be structure-preserving:
opening a page in the admin and saving it untouched may not change any of its
blocks. Before apps.content.admin_content learned about preserved blocks, that
save silently deleted every table and flattened every embedded PDF."""
import io

import pytest
from django.core.files.base import ContentFile
from PIL import Image as PILImage

from apps.content.admin_content import blocks_to_html, write_blocks_from_html
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document, Image

LANGS = ("uz", "ru", "en")


def _png() -> bytes:
    buf = io.BytesIO()
    PILImage.new("RGB", (4, 4), (200, 20, 20)).save(buf, "PNG")
    return buf.getvalue()


@pytest.fixture
def page(db):
    return Page.objects.create(slug="test-page")


@pytest.fixture
def image(db):
    img = Image(alt_text="x")
    img.file.save("t.png", ContentFile(_png()), save=True)
    return img


@pytest.fixture
def document(db):
    doc = Document(title="Nizom")
    doc.file.save("nizom.pdf", ContentFile(b"%PDF-1.4 test"), save=True)
    return doc


def _add(page, order, block_type, payload_by_lang):
    block = ContentBlock(page=page, order=order, block_type=block_type, data=payload_by_lang)
    block.full_clean()
    block.save()
    return block


def _same(payload):
    return {lang: dict(payload) for lang in LANGS}


def _snapshot(page):
    return [(b.id, b.block_type, b.order, b.data) for b in ContentBlock.objects.filter(page=page).order_by("order")]


def _html(page):
    return {lang: blocks_to_html(page, lang) for lang in LANGS}


def _rich_page(page, image, document):
    _add(page, 1, "heading", _same({"text": "Kirish", "level": 3}))
    _add(page, 2, "paragraph", _same({"text": "Muhim ogohlantirish", "bold": True}))
    _add(page, 3, "paragraph", _same({"text": "Oddiy matn & belgilar"}))
    _add(page, 4, "table", _same({"headers": ["A", "B"], "rows": [["1", "2"], ["3", "4"]]}))
    _add(page, 5, "list", _same({"items": ["bir", "ikki"]}))
    _add(page, 6, "document", _same({"document_id": document.id, "caption": "Nizom"}))
    _add(page, 7, "image", _same({"image_id": image.id, "alt": "Rasm", "style": "diagram"}))
    _add(page, 8, "gallery", _same({"items": [{"image_id": image.id, "alt": ""}]}))
    _add(page, 9, "staff_card", _same({"full_name": "Aliyev Vali", "title": "Mudir"}))
    _add(page, 10, "raw_html", _same({"html": "<div>eski</div>"}))
    return page


def test_saving_an_untouched_page_changes_nothing(page, image, document):
    _rich_page(page, image, document)
    before = _snapshot(page)

    write_blocks_from_html(page, _html(page))

    assert _snapshot(page) == before


def test_non_editable_blocks_appear_as_placeholders_not_as_content(page, image, document):
    _rich_page(page, image, document)
    html = blocks_to_html(page, "uz")
    for block in ContentBlock.objects.filter(page=page, block_type__in=["table", "document", "gallery", "staff_card", "raw_html"]):
        assert f'data-preserved-block="{block.id}"' in html
    # ... and their content is not smuggled into editable text
    assert "<div>eski</div>" not in html and "Mudir" not in html


def test_editing_a_paragraph_keeps_the_tables_and_documents_around_it(page, image, document):
    _rich_page(page, image, document)
    before = {b.id: b for b in ContentBlock.objects.filter(page=page)}
    html = _html(page)
    html["uz"] = html["uz"].replace("Oddiy matn &amp; belgilar", "Tuzatilgan matn")
    html["ru"] = html["ru"].replace("Oddiy matn &amp; belgilar", "Исправленный текст")

    write_blocks_from_html(page, html)

    after = ContentBlock.objects.filter(page=page).order_by("order")
    assert [b.block_type for b in after] == [
        "heading", "paragraph", "paragraph", "table", "list", "document", "image", "gallery", "staff_card", "raw_html",
    ]
    edited = after[2]
    assert edited.data["uz"]["text"] == "Tuzatilgan matn"
    assert edited.data["ru"]["text"] == "Исправленный текст"
    # untouched structured blocks are the very same rows with identical data
    for block in after:
        if block.block_type in {"table", "document", "gallery", "staff_card", "raw_html"}:
            assert block.id in before and block.data == before[block.id].data


def test_an_edited_block_keeps_its_hidden_formatting(page):
    _add(page, 1, "paragraph", _same({"text": "Qalin satr", "bold": True}))
    _add(page, 2, "heading", _same({"text": "Bo'lim", "level": 3}))
    html = _html(page)
    html = {lang: text.replace("Qalin satr", "Qalin satr tuzatildi").replace("Bo'lim", "Bo'lim 2") for lang, text in html.items()}

    write_blocks_from_html(page, html)

    paragraph, heading = ContentBlock.objects.filter(page=page).order_by("order")
    assert paragraph.data["uz"] == {"text": "Qalin satr tuzatildi", "bold": True}
    assert heading.data["uz"] == {"text": "Bo'lim 2", "level": 3}


def test_deleting_a_placeholder_deletes_its_block(page, image, document):
    _rich_page(page, image, document)
    table = ContentBlock.objects.get(page=page, block_type="table")
    html = _html(page)
    html = {lang: text.replace(
        f'<div data-preserved-block="{table.id}" data-block-type="table" class="preserved-block">'
        f"Jadval (2 qator) — tahrirlanmaydi</div>", "") for lang, text in html.items()}
    assert str(table.id) not in html["uz"]

    write_blocks_from_html(page, html)

    assert not ContentBlock.objects.filter(page=page, block_type="table").exists()
    assert ContentBlock.objects.filter(page=page, block_type="document").exists()


def test_moving_a_placeholder_moves_its_block(page, image, document):
    _add(page, 1, "paragraph", _same({"text": "Birinchi"}))
    table = _add(page, 2, "table", _same({"headers": ["A"], "rows": [["1"]]}))
    _add(page, 3, "paragraph", _same({"text": "Uchinchi"}))
    placeholder = f'<div data-preserved-block="{table.id}" data-block-type="table" class="preserved-block">Jadval</div>'
    html = {lang: f"<p>Birinchi</p>\n<p>Uchinchi</p>\n{placeholder}" for lang in LANGS}

    write_blocks_from_html(page, html)

    assert [b.block_type for b in ContentBlock.objects.filter(page=page).order_by("order")] == [
        "paragraph", "paragraph", "table",
    ]
    assert ContentBlock.objects.get(page=page, block_type="table").id == table.id


def test_a_placeholder_pasted_twice_or_from_another_page_is_harmless(page):
    other = Page.objects.create(slug="other")
    foreign = _add(other, 1, "table", _same({"headers": ["A"], "rows": [["1"]]}))
    mine = _add(page, 1, "table", _same({"headers": ["B"], "rows": [["2"]]}))
    chip = lambda i: f'<div data-preserved-block="{i}" data-block-type="table" class="preserved-block">Jadval</div>'
    html = {lang: f"{chip(mine.id)}<p>Matn</p>{chip(mine.id)}{chip(foreign.id)}" for lang in LANGS}

    write_blocks_from_html(page, html)

    blocks = list(ContentBlock.objects.filter(page=page).order_by("order"))
    assert [b.block_type for b in blocks] == ["table", "paragraph"]
    assert blocks[0].id == mine.id
    assert ContentBlock.objects.filter(page=other).count() == 1  # untouched


def test_a_brand_new_page_still_builds_blocks_from_plain_html(page):
    write_blocks_from_html(page, {
        "uz": "<h2>Sarlavha</h2><p>Matn</p><ul><li>a</li><li>b</li></ul>",
        "ru": "<h2>Заголовок</h2><p>Текст</p><ul><li>а</li><li>б</li></ul>",
        "en": "<h2>Title</h2><p>Text</p><ul><li>a</li><li>b</li></ul>",
    })
    blocks = list(ContentBlock.objects.filter(page=page).order_by("order"))
    assert [b.block_type for b in blocks] == ["heading", "paragraph", "list"]
    assert blocks[1].data["ru"]["text"] == "Текст"


def test_news_style_save_drops_the_gallery_the_form_manages_itself(page, image):
    """A news post's gallery has its own picker; blocks_to_html(skip_types=...) hides it from
    the editor and a save without a placeholder removes the old block (the view re-appends it)."""
    _add(page, 1, "paragraph", _same({"text": "Matn"}))
    _add(page, 2, "gallery", _same({"items": [{"image_id": image.id, "alt": ""}]}))
    html = {lang: blocks_to_html(page, lang, skip_types=("gallery",)) for lang in LANGS}
    assert "gallery" not in html["uz"]

    write_blocks_from_html(page, html)

    assert [b.block_type for b in ContentBlock.objects.filter(page=page)] == ["paragraph"]


def test_translated_placeholders_in_ru_en_never_become_stray_paragraphs(page):
    """The editor's translate button round-trips the uz HTML through Google Translate, which
    may rewrite the placeholder's attributes/quotes. ru/en are text-only, so any such variant
    must be stripped, not parsed as a paragraph that shifts every later block out of alignment."""
    table = _add(page, 1, "table", _same({"headers": ["A"], "rows": [["1"]]}))
    _add(page, 2, "paragraph", _same({"text": "Matn"}))
    uz = (f'<div data-preserved-block="{table.id}" data-block-type="table" class="preserved-block">Jadval</div>'
          "<p>Matn</p>")
    mangled = (f"<div class='preserved-block' data-block-type='table' data-preserved-block='{table.id}'>Таблица</div>"
               "<p>Текст</p>")

    write_blocks_from_html(page, {"uz": uz, "ru": mangled, "en": mangled})

    blocks = list(ContentBlock.objects.filter(page=page).order_by("order"))
    assert [b.block_type for b in blocks] == ["table", "paragraph"]
    assert blocks[1].data["uz"]["text"] == "Matn" and blocks[1].data["ru"]["text"] == "Текст"


@pytest.mark.parametrize("name", ["\u0421hina-1.png", "Rasm nomi bilan.png", "foto (2) \u02bbtest.png", "a%b.png"])
def test_images_with_cyrillic_spaces_or_percent_in_the_file_name_survive_a_save(page, name):
    """image.file.url percent-encodes the name; the lookup must decode it again or the block is dropped."""
    img = Image(alt_text="x")
    img.file.save(name, ContentFile(_png()), save=True)
    _add(page, 1, "paragraph", _same({"text": "Oldin"}))
    _add(page, 2, "image", _same({"image_id": img.id, "alt": ""}))
    _add(page, 3, "paragraph", _same({"text": "Keyin"}))
    before = _snapshot(page)

    write_blocks_from_html(page, _html(page))

    assert _snapshot(page) == before


def test_a_one_character_block_in_one_language_does_not_shift_the_others(page):
    """extract() drops one-character paragraphs. Legacy news-163 had a lone 'O' in ru only, so
    on save every later ru block slid one position out of line with Uzbek."""
    _add(page, 1, "paragraph", {"uz": {"text": "FARMONI"}, "ru": {"text": "О"}, "en": {"text": "DECREE"}})
    _add(page, 2, "paragraph", {"uz": {"text": "2022-2026 yillarga"}, "ru": {"text": "СТРАТЕГИИ"}, "en": {"text": "STRATEGY"}})
    _add(page, 3, "paragraph", _same({"text": "Oxirgi"}))
    before = _snapshot(page)

    write_blocks_from_html(page, _html(page))

    assert _snapshot(page) == before


def test_an_edit_next_to_a_protected_block_still_lands_on_the_right_block(page):
    _add(page, 1, "paragraph", {"uz": {"text": "A"}, "ru": {"text": "О"}, "en": {"text": "A"}})
    _add(page, 2, "paragraph", _same({"text": "Ikkinchi"}))
    html = {lang: text.replace("Ikkinchi", "Ikkinchi tuzatildi") for lang, text in _html(page).items()}

    write_blocks_from_html(page, html)

    first, second = ContentBlock.objects.filter(page=page).order_by("order")
    assert first.data["ru"] == {"text": "О"}
    assert second.data["uz"]["text"] == "Ikkinchi tuzatildi"


def test_a_zero_width_space_bold_paragraph_is_kept_not_dropped(page):
    _add(page, 1, "paragraph", _same({"text": "Matn"}))
    _add(page, 2, "paragraph", _same({"text": "​", "bold": True}))
    before = _snapshot(page)

    write_blocks_from_html(page, _html(page))

    assert _snapshot(page) == before


def test_an_image_block_whose_file_row_is_gone_is_kept(page):
    _add(page, 1, "paragraph", _same({"text": "Oldin"}))
    _add(page, 2, "image", _same({"image_id": 987654, "alt": ""}))
    _add(page, 3, "paragraph", _same({"text": "Keyin"}))
    before = _snapshot(page)

    write_blocks_from_html(page, _html(page))

    assert _snapshot(page) == before
