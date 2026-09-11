"""
Tests for the legacy HTML extraction logic (see html_extract.py) -- no
Django/database dependency, this module only ever parses strings. Covers
the behaviors found and fixed while migrating real department/faculty
content from the old site, so a future tweak to the heuristics doesn't
silently regress on the exact patterns that motivated them.
"""
from .html_extract import extract


def test_adjacent_inline_elements_keep_a_space_between_them():
    # Real bug found migrating a faculty page: get_text(strip=True) strips
    # each fragment individually then joins with nothing, so adjacent
    # <span> elements with no whitespace between their tags in the source
    # glued into one run-on word ("fakultetidaDavolash ishiyo'nalishi...").
    html = (
        "<p><span>Davolash ishi fakultetida</span>"
        "<span>Davolash ishi</span> yo'nalishi bo'yicha "
        "<span>bakalavriat</span><span>mutaxasislari</span> tayyorlanadi.</p>"
    )
    result = extract(html)
    assert len(result.blocks) == 1
    assert result.blocks[0].block_type == "paragraph"
    text = result.blocks[0].payload["text"]
    assert "fakultetidaDavolash" not in text
    assert "bakalavriatmutaxasislari" not in text
    assert text == "Davolash ishi fakultetida Davolash ishi yo'nalishi bo'yicha bakalavriat mutaxasislari tayyorlanadi."


def test_bold_short_div_is_a_heading():
    html = '<div style="text-align: center;"><strong>Kafedraning tarixi</strong></div>'
    result = extract(html)
    assert len(result.blocks) == 1
    assert result.blocks[0].block_type == "heading"
    assert result.blocks[0].payload["text"] == "Kafedraning tarixi"


def test_bold_full_sentence_is_a_paragraph_not_a_heading():
    html = "<p><strong>Bu gap nuqta bilan tugaydi va uzunroq.</strong></p>"
    result = extract(html)
    assert len(result.blocks) == 1
    assert result.blocks[0].block_type == "paragraph"


def test_photo_name_title_bio_pattern_extracts_a_staff_member():
    html = (
        '<img src="/uploads/x.png" />'
        "<div><strong>Ism Familiya<br/>Lavozim nomi</strong></div>"
        "<div>"
        + "Bu yerda uzun tarjimai hol matni keladi. " * 6
        + "</div>"
    )
    result = extract(html)
    assert len(result.staff) == 1
    staff = result.staff[0]
    assert staff.full_name == "Ism Familiya"
    assert staff.title == "Lavozim nomi"
    assert staff.photo_src == "/uploads/x.png"


def test_short_bold_line_that_is_not_a_real_name_stays_a_heading():
    # A single-word or comma-containing "name" candidate is almost
    # certainly not a person's name (see _looks_like_person_name) -- e.g. a
    # title fragment that happened to be the first <br>-separated line.
    html = "<div><strong>Kafedra ma'lumoti,<br/>davom etadi</strong></div>" + "<div>" + "matn " * 30 + "</div>"
    result = extract(html)
    assert len(result.staff) == 0


def test_empty_html_produces_no_blocks():
    assert extract("").blocks == []
    assert extract("   ").blocks == []
