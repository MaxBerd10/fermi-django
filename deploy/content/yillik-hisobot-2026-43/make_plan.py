"""Builds plan.json of script 43: "Institut tarixi" (the page of the department institut-tarixi, slug department-42) in the block order the layout engine reads:
    heading 2 (section) ... heading 3 (the person's name) + image (portrait) + paragraphs per person ... dated lists ... "Tarix sahifasi" / "Xalqaro hamkorlik".
The 59 live blocks are parallel in uz, ru and en (block N is the same part of the text in all three), so one program, written below by the order numbers of the live blocks,
gives the same structure in every language; the script checks the shape of every block it reads in every language and stops at the first surprise.
Run again right before applying on the server if the page changed:  python deploy/content/yillik-hisobot-2026-43/make_plan.py"""
import hashlib
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ("uz", "ru", "en")
SLUG = "department-42"
ZERO_WIDTH = re.compile("[​-‍﻿]")
DATED = re.compile(r"^((?:(?:с|since|from)\s+)?\d{4}(?:\s*[–—-]\s*\d{4})?(?:\s+(?:yildan|года?|гг?\.?|onwards))?)\s*[–—-]\s*(.+)$", re.I)


def sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def db_data(block):
    """The data of a block as the database holds it: the API adds the expanded `image` / `document` next to image_id / document_id."""
    return {lang: {k: v for k, v in block["data"][lang].items() if k not in ("image", "document")} for lang in LANGS}


page = json.loads(subprocess.run(["curl", "-s", "https://fermi.uz/api/v1/departments/institut-tarixi/?menu_id=1827"], capture_output=True, text=True).stdout)["page"]
live = {block["order"]: block for block in page["blocks"]}
assert len(live) == 59, len(live)


def text(order, lang):
    block = live[order]
    assert block["block_type"] == "paragraph", (order, block["block_type"])
    return ZERO_WIDTH.sub("", block["data"][lang]["text"]).strip()


def paragraph(order):
    return {"block_type": "paragraph", "data": {lang: {"text": text(order, lang)} for lang in LANGS}}


def heading(order, level):
    return {"block_type": "heading", "data": {lang: {"text": text(order, lang), "level": level} for lang in LANGS}}


def split_name(value):
    """'MIRZAEV KOMILJON MIRZAEVICH Tibbiyot fanlari ...' -> (the capital-letter name of two to four words, the rest)."""
    words = value.split(" ")
    count = 0
    while count < min(4, len(words)) and re.fullmatch(r"[^\W\d_a-z]+(?:[ʻ‘’'’-][^\W\d_a-z]+)*", words[count].rstrip(",.").replace("Ъ", "Ь"), re.U) and words[count].rstrip(",.").isupper():
        count += 1
    assert count >= 2, value
    return " ".join(words[:count]).rstrip(","), " ".join(words[count:]).lstrip(",.; ").strip()


def person(name_order, portrait, body, split=False, extra_after_portrait=()):
    """Blocks of one person: heading 3 (name), the portrait, then paragraphs. `split`: the name and the first sentences are one live paragraph.
    `body`: orders of the paragraphs that belong to the person (their text, in order)."""
    names, intros = {}, {}
    for lang in LANGS:
        names[lang], intros[lang] = split_name(text(name_order, lang)) if split else (text(name_order, lang), None)
    blocks = [{"block_type": "heading", "data": {lang: {"text": names[lang], "level": 3} for lang in LANGS}},
              {"block_type": "image", "data": {lang: {"repo_image": f"{portrait}.webp", "alt": names[lang]} for lang in LANGS}}]
    if split:
        assert all(intros[lang] for lang in LANGS), ("an empty introduction in one language", name_order, intros)
        blocks.append({"block_type": "paragraph", "data": {lang: {"text": intros[lang]} for lang in LANGS}})
    blocks += [paragraph(order) for order in body]
    return blocks


def list_items(order):
    return {lang: live[order]["data"][lang]["items"] for lang in LANGS}


def dated_list(items_by_lang):
    assert all(DATED.match(item.strip()) for lang in LANGS for item in items_by_lang[lang]), items_by_lang
    return {"block_type": "list", "data": {lang: {"items": items_by_lang[lang]} for lang in LANGS}}


items = list_items(3)
assert all(len(items[lang]) == 10 and not any(DATED.match(i.strip()) for i in items[lang][:3]) and all(DATED.match(i.strip()) for i in items[lang][3:]) for lang in LANGS)
blocks = [
    heading(1, 2), paragraph(2),
    {"block_type": "list", "data": {lang: {"items": items[lang][:3]} for lang in LANGS}},
    dated_list({lang: items[lang][3:] for lang in LANGS}),
    *person(5, "mirzayev", [6], split=True),
    *person(7, "nishonov", [9, 10]),
    *person(11, "abduraxmonov", [13]),
    *person(14, "usmanov", []),
    *person(15, "mamatqulov", [17]),
    *person(18, "sultanov", [19]),
    *person(20, "sidikov", [21, 23]),
    heading(24, 2), paragraph(25),
    dated_list({lang: [text(27, lang)] for lang in LANGS}),
    *person(29, "rasulov", [30], split=True),
    *person(32, "isakov", [], split=True),
    *person(33, "botirov", [35]),
    *person(36, "normatova", [38]),
    *person(39, "qodirova", [40, 42]),
    *person(43, "boltaboyev", [45, 46]),
    heading(47, 2),
    {"block_type": "image", "data": {lang: {"repo_image": "archive.webp", "alt": text(47, lang)} for lang in LANGS}},
    *[paragraph(order) for order in range(49, 57)],
    heading(57, 2), paragraph(58),
    {"block_type": "image", "data": {lang: {"image_id": live[59]["data"][lang]["image_id"], "alt": text(57, lang)} for lang in LANGS}},
]
assert sum(1 for b in blocks if b["block_type"] == "heading" and b["data"]["uz"]["level"] == 3) == 13
# every live image the program does not reuse is replaced by the local portrait; none of the other live blocks may be left out by accident
used = {1, 2, 3, 5, 6, 7, 9, 10, 11, 13, 14, 15, 17, 18, 19, 20, 21, 23, 24, 25, 27, 29, 30, 32, 33, 35, 36, 38, 39, 40, 42, 43, 45, 46, 47, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59}
images = {4, 8, 12, 16, 22, 28, 31, 34, 37, 41, 44, 48}  # the portraits and the archive picture: replaced by the files of the repository
dropped = {26}  # a paragraph of zero-width spaces
assert used | images | dropped == set(live), sorted(set(live) - (used | images | dropped))
plan = {"slug": SLUG, "fp": {str(order): {lang: sha(db_data(block)[lang]) for lang in LANGS} for order, block in live.items()}, "blocks": blocks}
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", len(blocks), "blocks (13 persons) from", len(live), "live blocks")
