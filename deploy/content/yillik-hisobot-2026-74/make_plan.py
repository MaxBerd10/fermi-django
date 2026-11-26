"""Builds plan.json from the database AFTER scripts 39-73 (read-only):
    python manage.py shell < deploy/content/yillik-hisobot-2026-74/make_plan.py
Each entry is one block: its page slug, its order, the fingerprint of every language's payload and the new data."""
import copy
import json
from pathlib import Path

from apps.content.migration_tools import sha
from apps.content.models import Page

LANGS = ("uz", "ru", "en")
OUT = Path("deploy/content/yillik-hisobot-2026-74/plan.json")
entries = []


def change(slug, block_type, uz_text_test, edit, why):
    """Finds the ONE block of `block_type` whose Uzbek text passes `uz_text_test` and applies `edit(lang, data)` to a copy of its payload."""
    page = Page.objects.get(slug=slug)
    found = []
    for block in page.blocks.order_by("order"):
        if block.block_type != block_type:
            continue
        uz = block.data["uz"]
        text = uz.get("text") if block_type == "paragraph" else " ".join(uz.get("items", []))
        if uz_text_test(text or ""):
            found.append(block)
    assert len(found) == 1, (slug, why, len(found))
    block = found[0]
    new = copy.deepcopy(block.data)
    for lang in LANGS:
        edit(lang, new[lang])
    assert new != block.data, (slug, why, "nothing changed")
    entries.append({"slug": slug, "order": block.order, "why": why, "fp": {lang: sha(block.data[lang]) for lang in LANGS}, "data": new})


def replace_in(data, old, new, count=None):
    """Replaces `old` by `new` in the text (or in every list item) of one language's payload; `count` is how many replacements are expected."""
    n = 0
    if "text" in data:
        n += data["text"].count(old)
        data["text"] = data["text"].replace(old, new)
    else:
        n += sum(item.count(old) for item in data["items"])
        data["items"] = [item.replace(old, new) for item in data["items"]]
    if count is not None:
        assert n == count, (old, n, count)
    return n


# 1. The closing day of the master's admission is 30 July (the Ministry of Higher Education's own announcement for 2025/2026), as the page says
#    in its other sentence and as the page on the online registration says: the one "31" was a leftover.
DATES = {"uz": ("1-iyuldan 31-iyulgacha", "1-iyuldan 30-iyulgacha"), "ru": ("с 1 по 31 июля", "с 1 по 30 июля"), "en": ("1 July to 31 July", "1 July to 30 July")}
change("magistratura-qabul-hujjatlari-toplami", "paragraph", lambda t: t.startswith("Hujjatlar 1-iyuldan 31-iyulgacha"),
       lambda lang, d: replace_in(d, *DATES[lang], count=1), "master's admission: 31 July -> 30 July")

# 2. Two sentences had been glued ("...nomiga arizaAbituriyent..."): split, and the line that introduces the list of documents is said in uz too
#    (ru and en already say "The following documents are required").
change("xalqaro-qabul-hujjatlar-toplami", "paragraph", lambda t: "rektori nomiga arizaAbituriyent" in t,
       lambda lang, d: replace_in(d, "rektori nomiga arizaAbituriyent toʻgʻrisida toʻliq maʻlumot berilishi lozim (yashash manzili, elektron manzili, telefon raqamlari);",
                                  "rektori nomiga ariza. Abituriyent toʻgʻrisida toʻliq maʻlumot berilishi lozim (yashash manzili, elektron manzili, telefon raqamlari). Quyidagi hujjatlar talab qilinadi:", count=1) if lang == "uz" else None,
       "joint programme: glued sentences")

# 3. "Akademiya" / "Академия" / "Academy" is the word of another institution; this page says "Institut rektori" in the same lists.
AKAD = {"uz": [("Akademiyaning", "Institutning"), ("Akademiya rahbariga", "Institut rahbariga")],
        "ru": [("и Академии;", "и Института;"), ("деятельностью Академии", "деятельностью Института"), ("руководителю Академии", "руководителю Института")],
        "en": [("and the Academy;", "and the Institute;"), ("activity of the Academy", "activity of the Institute"), ("head of the Academy", "head of the Institute")]}


def akademiya(lang, d):
    for old, new in AKAD[lang]:
        replace_in(d, old, new)


for needle in ("Akademiyaning meʻyoriy", "Akademiyaning moliya-xoʻjalik"):
    change("buxgalteriya-bolimi", "list", lambda t, needle=needle: needle in t, akademiya, "accounting: 'Akademiya' -> 'Institut' (%s)" % needle)

# 4. The Uzbek title of the report stopped one word short ("... taxliliy yozma"); the word is the heading right below it ("Axborot"), as in ru and en.
change("fuqarolar-murojaatlari-statistikasi", "paragraph", lambda t: t.endswith("taxliliy yozma"),
       lambda lang, d: replace_in(d, "taxliliy yozma", "taxliliy yozma axborot", count=1) if lang == "uz" else None, "appeals report: the cut title")

# the akademiya edits touch several items of the same two blocks: every language must have no "Akademiya"/"Академии"/"Academy" left in them
for e in entries:
    if e["slug"] == "buxgalteriya-bolimi":
        for lang, bad in (("uz", "Akademiya"), ("ru", "Академии"), ("en", "Academy")):
            assert bad not in json.dumps(e["data"][lang], ensure_ascii=False), (e["order"], lang)

entries.sort(key=lambda e: (e["slug"], e["order"]))
OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "blocks ->", OUT)
for e in entries:
    print(" ", e["slug"][:50], "#%d" % e["order"], e["why"])
