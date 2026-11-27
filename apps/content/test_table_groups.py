"""A table may have a row of GROUP headings above its column headings (`header_groups`: label + how many columns it spans), so a table with nine
number columns says "2025/2026 ... grant" once above three short columns (Jami / oʻzbek / rus) instead of repeating a nine-line heading in every column."""
import pytest
from django.core.exceptions import ValidationError

from apps.content.models import ContentBlock, Page

LANGS = ("uz", "ru", "en")


def table(**extra):
    payload = {"headers": ["№", "Nomi", "Jami", "Oʻzbek", "Rus"], "rows": [["1", "Stomatologiya", "16", "14", "2"]], **extra}
    return {lang: dict(payload) for lang in LANGS}


def make(db, data):
    return ContentBlock(page=Page.objects.get_or_create(slug="jadval")[0], order=1, block_type="table", data=data)


def test_a_table_without_groups_is_still_valid(db):
    make(db, table()).full_clean()


def test_groups_that_cover_every_column_are_valid(db):
    make(db, table(header_groups=[{"label": "", "span": 2}, {"label": "2025/2026 taʻlim granti*", "span": 3}])).full_clean()


@pytest.mark.parametrize("groups", [
    [{"label": "", "span": 2}, {"label": "x", "span": 2}],   # covers 4 of 5 columns
    [{"label": "", "span": 2}, {"label": "x", "span": 4}],   # covers 6 of 5 columns
    [{"label": "x", "span": 0}, {"label": "y", "span": 5}],  # a group of no columns
    [{"label": "x", "span": "5"}],                           # the span is a number
    [{"label": "<b>x</b>", "span": 5}],                      # plain text only
    [{"span": 5}],                                           # a label (may be empty) is required
    [],                                                      # an empty list is no list of groups: leave the field out
    "x",
])
def test_groups_that_do_not_fit_the_table_are_refused(db, groups):
    with pytest.raises(ValidationError):
        make(db, table(header_groups=groups)).full_clean()
