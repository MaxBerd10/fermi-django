import glob
import os
import tempfile
from io import StringIO

import pytest
from django.core.management import call_command

from apps.content.models import ContentBlock, Page


@pytest.fixture
def blocks(db):
    page = Page.objects.create(slug="fix-uz")
    mixed = ContentBlock.objects.create(page=page, order=1, block_type="paragraph", data={
        "uz": {"text": "Хorijiy fuqarolar"}, "ru": {"text": "Иностранцы"}, "en": {"text": "Foreigners"}})
    cyr = ContentBlock.objects.create(page=page, order=2, block_type="paragraph", data={
        "uz": {"text": "Қабул бошланди"}, "ru": {"text": "Приём"}, "en": {"text": "Admission"}})
    russian = ContentBlock.objects.create(page=page, order=3, block_type="paragraph", data={
        "uz": {"text": "Вознаграждение участников"}, "ru": {"text": "x"}, "en": {"text": "y"}})
    return mixed, cyr, russian


def _uz(block):
    block.refresh_from_db()
    return block.data["uz"]["text"]


def test_dry_run_changes_nothing(blocks):
    before = [_uz(b) for b in blocks]
    call_command("fix_uz_script", stdout=StringIO())
    assert [_uz(b) for b in blocks] == before


def test_apply_repairs_leaves_russian_alone_and_can_be_restored(blocks):
    mixed, cyr, russian = blocks
    original = [_uz(b) for b in blocks]
    out = StringIO()
    call_command("fix_uz_script", "--apply", stdout=out)

    assert _uz(mixed) == "Xorijiy fuqarolar"
    assert _uz(cyr) == "Qabul boshlandi"
    assert _uz(russian) == original[2]                      # Russian prose untouched
    assert mixed.data["ru"] == {"text": "Иностранцы"}   # other languages untouched

    path = max(glob.glob(os.path.join(tempfile.gettempdir(), "fix_uz_script_backup_*.json")), key=os.path.getmtime)
    call_command("fix_uz_script", "--restore", path, stdout=StringIO())
    assert [_uz(b) for b in blocks] == original
    os.remove(path)
