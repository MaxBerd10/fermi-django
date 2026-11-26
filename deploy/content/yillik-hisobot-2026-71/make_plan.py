"""Builds plan.json from the database AFTER scripts 39-70 (read-only):
    python manage.py shell < deploy/content/yillik-hisobot-2026-71/make_plan.py
Every entry names the blocks it replaces by page slug + order and keeps their fingerprints; apply.py refuses a page that was edited since."""
import json
import re
from pathlib import Path

from apps.content.migration_tools import sha
from apps.content.models import Page

LANGS = ("uz", "ru", "en")
OUT = Path("deploy/content/yillik-hisobot-2026-71/plan.json")

# Headings that hold a sentence, a link or a phone number (the old HTML put them in <h2>/<h3>): they become paragraphs.
DEMOTE = {
    "bakalavriat-talim-granti-20252026": [11],
    "chet-ellik-talabalar-xavfsizligi": [3],
    "eng-kop-beriladigan-savollar": [19, 25],
    "iqtidorli-talabalarning-ilmiy-tadqiqot-faoliyatini-tashkil-etish-bolimi": [3],
    "magistratura-online-royxatdan-otish-2025": [1, 2],
    "magistratura-qabul-hujjatlari-toplami": [2, 3, 4, 13],
    "ordinatura-imtihonga-kirish-ruxsatnomasi-2025": [2],
    "qabul-komissiyasi-joylashgan-orni": [4, 5, 6],
    "qabul-komissiyasi-qoshma-talim-2025": [1, 3, 4],
    "qabul-nizomi": [4],
    "study-in-uzbekistan": [25],
    "vakant-lavozimlar-2025": [2, 3, 4],
    "xorijiy-fuqarolar-uchun-magistratura-va-klinik-ordinatura": [5],
}
# Paragraph lines that are really a list: (slug, first order, last order) -> one list block.
LISTS = [("xalqaro-qabul-hujjatlar-toplami", 7, 12)]


def fp(block):
    return {lang: sha(block.data[lang]) for lang in LANGS}


def text_of(block):
    return {lang: block.data[lang]["text"] for lang in LANGS}


entries = []
for slug, orders in DEMOTE.items():
    page = Page.objects.get(slug=slug)
    for order in orders:
        block = page.blocks.get(order=order)
        assert block.block_type == "heading", (slug, order, block.block_type)
        entries.append({"slug": slug, "order": order, "count": 1, "fp": [fp(block)],
                        "blocks": [{"block_type": "paragraph", "data": {lang: {"text": t} for lang, t in text_of(block).items()}}]})

for slug, first, last in LISTS:
    page = Page.objects.get(slug=slug)
    blocks = [page.blocks.get(order=o) for o in range(first, last + 1)]
    assert all(b.block_type == "paragraph" for b in blocks), slug
    entries.append({"slug": slug, "order": first, "count": len(blocks), "fp": [fp(b) for b in blocks],
                    "blocks": [{"block_type": "list", "data": {lang: {"items": [b.data[lang]["text"] for b in blocks]} for lang in LANGS}}]})

# magistratura-qabul-hujjatlari-toplami 8-12: "Imtihon fanlari roʻyxati" (heading) + the score lines (list) + the date sentence (paragraph).
page = Page.objects.get(slug="magistratura-qabul-hujjatlari-toplami")
b = {o: page.blocks.get(order=o) for o in range(8, 13)}
assert [b[o].block_type for o in range(8, 13)] == ["paragraph", "paragraph", "heading", "paragraph", "paragraph"]
entries.append({"slug": page.slug, "order": 8, "count": 5, "fp": [fp(b[o]) for o in range(8, 13)], "blocks": [
    {"block_type": "heading", "data": {lang: {"text": b[8].data[lang]["text"], "level": 3} for lang in LANGS}},
    {"block_type": "list", "data": {lang: {"items": [b[9].data[lang]["text"], b[11].data[lang]["text"], b[12].data[lang]["text"]]} for lang in LANGS}},
    {"block_type": "paragraph", "data": {lang: {"text": b[10].data[lang]["text"]} for lang in LANGS}},
]})

entries.sort(key=lambda e: (e["slug"], -e["order"]))  # highest order first: a replacement never shifts a block still to come
OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "entries,", len({e["slug"] for e in entries}), "pages ->", OUT)
