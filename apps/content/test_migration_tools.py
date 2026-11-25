"""The toolkit every content script (deploy/content/*/apply.py) is built on: fingerprints, block replacement, backups, the dry/apply/undo
skeleton, pictures from files -- and the guarantee that the typed block structures the layout engine reads survive the admin editor."""
import os

import pytest
from PIL import Image as PILImage

from apps.content import migration_tools as tools
from apps.content.admin_content import blocks_to_html, write_blocks_from_html
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image

LANGS = ("uz", "ru", "en")


def _typed(block_type, make):
    return {"block_type": block_type, "data": {lang: make(lang) for lang in LANGS}}


def _paragraph(text):
    return _typed("paragraph", lambda lang: {"text": f"{text} {lang}"})


def _add(page, order, spec):
    block = ContentBlock(page=page, order=order, block_type=spec["block_type"], data=spec["data"])
    block.full_clean()
    block.save()
    return block


@pytest.fixture
def page(db):
    return Page.objects.create(slug="t")


@pytest.fixture
def backup_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("BACKUP_DIR", str(tmp_path))
    return tmp_path


def _png(path, size=(40, 30)):
    PILImage.new("RGB", size, (200, 30, 30)).save(path)
    return str(path)


def test_replace_block_shifts_later_orders(page):
    for order in (1, 2, 3, 4):
        _add(page, order, _paragraph(f"b{order}"))
    pks = tools.replace_block(page, 2, [_paragraph("x"), _paragraph("y"), _paragraph("z")])
    assert len(pks) == 3
    texts = [b.data["uz"]["text"] for b in page.blocks.order_by("order")]
    assert texts == ["b1 uz", "x uz", "y uz", "z uz", "b3 uz", "b4 uz"]
    assert [b.order for b in page.blocks.order_by("order")] == [1, 2, 3, 4, 5, 6]


def test_replace_blocks_undoes_a_replacement_and_can_only_insert(page):
    for order in (1, 2, 3):
        _add(page, order, _paragraph(f"b{order}"))
    old = {"block_type": "paragraph", "data": page.blocks.get(order=2).data}
    tools.replace_block(page, 2, [_paragraph("x"), _paragraph("y"), _paragraph("z")])
    tools.replace_blocks(page, 2, 3, [old])  # three blocks back to the one
    assert [b.data["uz"]["text"] for b in page.blocks.order_by("order")] == ["b1 uz", "b2 uz", "b3 uz"]
    tools.replace_blocks(page, 2, 0, [_paragraph("new")])  # count 0: only insert, later blocks move up
    assert [b.data["uz"]["text"] for b in page.blocks.order_by("order")] == ["b1 uz", "new uz", "b2 uz", "b3 uz"]
    assert [b.order for b in page.blocks.order_by("order")] == [1, 2, 3, 4]


def test_make_document_keeps_the_file_and_title(db, tmp_path):
    path = tmp_path / "Report.pdf"
    path.write_bytes(b"%PDF-1.4 test")
    document = tools.make_document(str(path), "Annual report")
    assert document.title == "Annual report" and document.file.name.endswith(".pdf")
    assert document.file.size == len(b"%PDF-1.4 test")


def test_fingerprint_ok_detects_admin_edit(page):
    block = _add(page, 1, _paragraph("a"))
    expected = {lang: tools.sha(block.data[lang]) for lang in LANGS}
    assert tools.fingerprint_ok(block, expected)
    block.data["ru"]["text"] = "edited in the admin"
    assert not tools.fingerprint_ok(block, expected)


def test_backup_second_apply_is_refused(backup_dir):
    backup = tools.Backup("unit-test")
    assert not backup.exists()
    backup.save(rows=[1, 2])
    assert backup.exists() and backup.load()["rows"] == [1, 2]
    backup.retire()
    assert not backup.exists()


def test_run_modes_dry_writes_nothing_apply_once_undo_restores(db, backup_dir, monkeypatch):
    calls = []

    def build(apply):
        calls.append(("build", apply))
        return {"made": [7]} if apply else {}

    def undo(rows):
        calls.append(("undo", rows["made"]))

    monkeypatch.setenv("MODE", "dry")
    tools.run_modes("unit-test", build, undo)
    assert calls == [("build", False)] and not tools.Backup("unit-test").exists()

    monkeypatch.setenv("MODE", "apply")
    tools.run_modes("unit-test", build, undo)
    assert tools.Backup("unit-test").exists()
    with pytest.raises(SystemExit):
        tools.run_modes("unit-test", build, undo)  # the second apply is refused
    assert calls.count(("build", True)) == 1

    monkeypatch.setenv("MODE", "undo")
    tools.run_modes("unit-test", build, undo)
    assert ("undo", [7]) in calls and not tools.Backup("unit-test").exists()


def test_make_image_reads_the_real_size(db, tmp_path):
    image = tools.make_image(_png(tmp_path / "a.png", (40, 30)), "alt")
    assert (image.width, image.height, image.alt_text) == (40, 30, "alt")
    assert Image.objects.filter(pk=image.pk).exists()


def test_typed_structure_survives_the_admin_editor(page, tmp_path):
    one = tools.make_image(_png(tmp_path / "1.png"), "one")
    two = tools.make_image(_png(tmp_path / "2.png"), "two")
    specs = [
        _typed("heading", lambda lang: {"text": f"Section {lang}", "level": 2}),
        _paragraph("intro"),
        _typed("heading", lambda lang: {"text": f"Article {lang}", "level": 3}),
        _typed("list", lambda lang: {"items": [f"a {lang}", f"b {lang}"]}),
        _typed("image", lambda lang: {"image_id": one.pk, "alt": f"one {lang}"}),
        _typed("image", lambda lang: {"image_id": two.pk, "alt": f"two {lang}"}),
    ]
    for order, spec in enumerate(specs, start=1):
        _add(page, order, spec)
    before = [(b.block_type, b.data) for b in page.blocks.order_by("order")]
    write_blocks_from_html(page, {lang: blocks_to_html(page, lang) for lang in LANGS})
    after = [(b.block_type, b.data) for b in page.blocks.order_by("order")]
    assert after == before


def test_image_from_media_uses_the_file_already_in_the_media_folder(db, tmp_path, settings):
    settings.MEDIA_ROOT = str(tmp_path)
    (tmp_path / "migrated").mkdir()
    _png(tmp_path / "migrated" / "cover.png", (50, 20))
    image = tools.image_from_media("migrated/cover.png", "alt")
    assert (image.file.name, image.width, image.height, image.alt_text) == ("migrated/cover.png", 50, 20, "alt")
    assert tools.image_from_media("migrated/cover.png", "other alt").pk == image.pk  # the same file is one Image row
    assert Image.objects.count() == 1
    with pytest.raises(FileNotFoundError):
        tools.image_from_media("migrated/missing.png", "x")


def _html_to_blocks():
    import importlib.util
    spec = importlib.util.spec_from_file_location("_html_to_blocks", os.path.join(os.path.dirname(__file__), "..", "..", "deploy", "content", "_html_to_blocks.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _html(lang, extra=""):
    return (f'<p style="text-align:center"><img alt="" src="https://fermi.uz/media/migrated/a.jpg"></p>'
            f'<h2>Mission {lang}</h2><p>Text {lang}</p><ul><li>one {lang}</li><li>two {lang}</li></ul>'
            f'<p><strong>1-bob. Chapter {lang}</strong></p><h3>1-modda. Article {lang}</h3><p>More {lang}</p>{extra}')


def test_html_to_blocks_same_structure_in_three_languages():
    blocks = _html_to_blocks().build({lang: _html(lang) for lang in LANGS}, resolve_image=lambda src: 7)
    assert [b["block_type"] for b in blocks] == ["image", "heading", "paragraph", "list", "heading", "heading", "paragraph"]
    assert [b["data"]["ru"].get("level") for b in blocks if b["block_type"] == "heading"] == [2, 2, 3]
    assert all(b["data"][lang]["image_id"] == 7 for b in blocks[:1] for lang in LANGS)
    assert blocks[3]["data"]["en"]["items"] == ["one en", "two en"]
    assert blocks[1]["data"]["uz"]["text"] == "Mission uz"


def test_html_to_blocks_refuses_languages_that_differ():
    other = {"uz": _html("uz"), "ru": _html("ru", "<p>one more paragraph</p>"), "en": _html("en")}
    with pytest.raises(ValueError, match="ru: expected"):
        _html_to_blocks().build(other, resolve_image=lambda src: 7)


def test_reuse_or_make_image_does_not_duplicate_a_file_already_in_the_library(db, tmp_path):
    source = _png(tmp_path / "photo.png", (40, 30))
    first = tools.make_image(source, "first")
    again = tools.reuse_or_make_image(source, "second")
    assert again.pk == first.pk and Image.objects.count() == 1
    other = tools.reuse_or_make_image(_png(tmp_path / "other.png", (10, 10)), "third")
    assert other.pk != first.pk and Image.objects.count() == 2
