"""Builds plan.json of script 48 (Institut kengashi, five pages) from the live pages: the fingerprint of each raw_html block and the typed blocks that replace it.
Run again right before applying on the server if a page changed:
    python deploy/content/yillik-hisobot-2026-48/make_plan.py

Notes on the sources (checked by assertions below):
  * institut-ilmiy-kengashi: the three languages hold the same text; uz and ru have 18 duties, en stops after the 13th (and repeats four of them below the list) -> the five
    missing English duties are translated from the Russian text (listed in tarjima-kerak.md for a reader of English to check).
  * ilmiy-kengash (decisions): only uz has the list of decisions (13 lines without files + 6 PDF links); ru and en have just the "registered users" line. Now all three
    languages get the same list/cards, the ru/en lines are built from the dates.
  * avtoreferatlar: 39 links = 13 defences x (council line, name, thesis title), the same 13 PDFs in the three languages; the text is Uzbek in all three languages.
    Each defence becomes four blocks: council line (paragraph), author (heading 3), thesis title (paragraph), PDF card (caption "Avtoreferat"); the CAPITALS of the old text are
    turned into normal writing (names: Title Case; thesis titles: first letter capital, proper names Fargʻona/Buxoro).
"""
import hashlib
import html
import itertools
import json
import os
import re
import subprocess
from urllib.parse import unquote

HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ("uz", "ru", "en")
SECTION_MENU_ID = 1857  # the menu section "Institut kengashi"


def sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def fetch(url):
    return json.loads(subprocess.run(["curl", "-s", url], capture_output=True, text=True).stdout)


def labels():
    found = {}

    def walk(items):
        for item in items:
            match = re.fullmatch(r"/blog/%d/([^/?#]+)" % SECTION_MENU_ID, item.get("url") or "")
            if match:
                found[match.group(1)] = item["label"]
            walk(item.get("children", []))

    menu = fetch("https://fermi.uz/api/v1/menu/?page_size=500")
    walk(menu if isinstance(menu, list) else menu.get("results", []))
    return found


def plain(fragment):
    text = html.unescape(re.sub(r"<[^>]+>", "", fragment)).replace("\xa0", " ").replace("'", "’")
    return re.sub(r"\s+", " ", text).strip()


def same(text):  # the same text in the three languages
    return {lang: text for lang in LANGS}


def block(kind, data):
    return {"block_type": kind, "data": data}


def media_of(src):
    return unquote(src.split("/media/", 1)[1])


MENU = labels()
PAGES = {}


def page_blocks(slug):
    data = fetch("https://fermi.uz/api/v1/pages/" + slug + "/")["blocks"]
    PAGES[slug] = data
    raw = [b for b in data if b["block_type"] == "raw_html"]
    assert len(raw) == 1 and raw[0]["order"] == 1, slug
    return raw[0], [b for b in data if b["block_type"] == "document"]


def entry(slug, raw, blocks, document=None):
    result = {"slug": slug, "order": 1, "fp": {lang: sha(raw["data"][lang]) for lang in LANGS}, "blocks": blocks}
    if document:
        result["existing_document"] = document
    return result


def existing_caption(documents, caption):
    assert len(documents) == 1
    block_ = documents[0]
    return {"order": block_["order"], "document_id": block_["data"]["uz"]["document_id"], "caption": caption,
            "fp": {lang: sha({k: v for k, v in block_["data"][lang].items() if k not in ("image", "document")}) for lang in LANGS}}


def image_block(src_html, slug):
    sources = {lang: re.findall(r'<img[^>]*\bsrc="([^"]+)"', src_html[lang]) for lang in LANGS}
    assert len(sources["uz"]) == 1 and sources["uz"] == sources["ru"] == sources["en"], slug
    return block("image", {lang: {"media": media_of(sources["uz"][0]), "alt": MENU[slug][lang]} for lang in LANGS})


plan = []

# ---- 1. Ilmiy kengash (the council) --------------------------------------------------------------------------------------------------------------------------
slug = "institut-ilmiy-kengashi"
raw, _ = page_blocks(slug)
paragraphs = {lang: re.findall(r"<p[^>]*>(.*?)</p>", raw["data"][lang]["html"], re.S) for lang in LANGS}


def duties(lang):
    cleaned = re.sub(r"</?span[^>]*>", "", paragraphs[lang][2])
    return [plain(part) for part in cleaned.split("&nbsp;") if part.strip()]


uz_duties, ru_duties, en_duties = duties("uz"), duties("ru"), duties("en")
assert len(uz_duties) == 17 and len(ru_duties) == 18 and len(en_duties) == 12
# uz: the last item holds two duties ("... kiritadi;Fakultet (institut) dekanlari ...", no space)
head, tail = uz_duties[16].split("kiritadi;", 1)
uz_duties[16:17] = [head + "kiritadi;", tail]
assert len(uz_duties) == 18
# en: the first item holds the first two duties
first, second = en_duties[0].split(" Ensuring ", 1)
en_duties[0:1] = [first, "Ensuring " + second]
assert len(en_duties) == 13
en_duties += [  # translated from the Russian text, the English page stops here
    "Hears the annual reports of the Institute’s departments on their scientific and technical activities;",
    "The Scientific Secretary, in accordance with their job duties, is in charge of the organizational management of the Scientific Council’s day-to-day work.",
    "Recommends candidates from among the teaching staff for internships at foreign universities in accordance with the plans;",
    "Submits proposals on awarding academic titles to the staff of the educational and scientific departments of the faculty (institute);",
    "Reviews the reports of the deans of the faculty (institute), heads of departments and heads of the structural divisions of the faculty (institute);",
]
duty = {"uz": uz_duties, "ru": ru_duties, "en": en_duties}
intro = {lang: plain(paragraphs[lang][0]) for lang in LANGS}
intro["uz"] = intro["uz"].replace("hisoblanadi.Kengashning", "hisoblanadi. Kengashning")
lead = {lang: plain(paragraphs[lang][1]).rstrip(":") for lang in LANGS}
for lang in LANGS:
    assert duty[lang][5].endswith(":"), (lang, duty[lang][5])
plan.append(entry(slug, raw, [
    block("paragraph", {lang: {"text": intro[lang]} for lang in LANGS}),
    block("heading", {lang: {"text": lead[lang], "level": 3} for lang in LANGS}),
    block("list", {lang: {"items": duty[lang][:5]} for lang in LANGS}),
    block("paragraph", {lang: {"text": duty[lang][5]} for lang in LANGS}),
    block("list", {lang: {"items": duty[lang][6:]} for lang in LANGS}),
]))

# ---- 2. Ilmiy kengash tarkibi (the composition: a scan) ----------------------------------------------------------------------------------------------------------
slug = "ilmiy-kengash-tarkibi"
raw, documents = page_blocks(slug)
plan.append(entry(slug, raw, [image_block({lang: raw["data"][lang]["html"] for lang in LANGS}, slug)],
                  existing_caption(documents, {lang: MENU[slug][lang] for lang in LANGS})))

# ---- 3. Kun tartibi (the agenda) -------------------------------------------------------------------------------------------------------------------------------
slug = "kengash-kun-tartibi"
raw, documents = page_blocks(slug)
decision_28 = {"uz": "FJSTI Kengash qarori 28.12.2024", "ru": "Решение Совета от 28.12.2024", "en": "Council decision of 28.12.2024"}
registered = {lang: plain(re.sub(r"<img[^>]*>", "", raw["data"][lang]["html"])) for lang in LANGS}
assert all(registered[lang] for lang in LANGS)
plan.append(entry(slug, raw, [image_block({lang: raw["data"][lang]["html"] for lang in LANGS}, slug),
                              block("paragraph", {lang: {"text": registered[lang]} for lang in LANGS})],
                  existing_caption(documents, decision_28)))

# ---- 4. Qarorlar (decisions) ------------------------------------------------------------------------------------------------------------------------------------
slug = "ilmiy-kengash"
raw, documents = page_blocks(slug)
registered = {lang: plain(re.sub(r"<img[^>]*>", "", raw["data"][lang]["html"])) for lang in LANGS}
uz_html = raw["data"]["uz"]["html"]
old_lines = [plain(p) for p in re.findall(r"<p>((?:(?!<a ).)*?)</p>", uz_html.split("<hr />")[0], re.S)]
old_lines = [x for x in old_lines if x.startswith("FJSTI")]
assert len(old_lines) == 13, old_lines
KINDS = {"bayoni": ("Kengash bayoni", "Протокол Совета", "Council minutes"), "qaror": ("Kengash qarori", "Решение Совета", "Council decision")}
DATE = re.compile(r"(\d{2}\.\d{2}\.\d{2,4})")
items = {lang: [] for lang in LANGS}
for line in old_lines:
    date = DATE.search(line).group(1)
    if len(date) == 8:
        date = date[:6] + "20" + date[6:]
    extra = bool(re.search(r"navbatdan", line, re.I))
    kind = KINDS["bayoni" if "bayon" in line else "qaror"]
    items["uz"].append("FJSTI %s %s%s" % (kind[0], date, " (navbatdan tashqari)" if extra else ""))
    items["ru"].append("%s%s от %s" % ("Внеочередное решение Совета" if extra and kind is KINDS["qaror"] else kind[1], "", date))
    items["en"].append("%s%s of %s" % ("Extraordinary Council decision" if extra and kind is KINDS["qaror"] else kind[2], "", date))
links = re.findall(r'<a href="([^"]+)"[^>]*>(.*?)</a>', uz_html, re.S)
assert len(links) == 6
cards = []
for href, text in links[:5]:
    date = DATE.search(plain(text)).group(1)
    cards.append(block("document", {"uz": {"media": media_of(href), "caption": "FJSTI Kengash qarori " + date},
                                    "ru": {"media": media_of(href), "caption": "Решение Совета от " + date},
                                    "en": {"media": media_of(href), "caption": "Council decision of " + date}}))
last = DATE.search(plain(links[5][1])).group(1)
assert last == "28.12.2024" and links[5][0].endswith("%E2%84%96%205.pdf") or "5.%20Kengash" in links[5][0]  # the last link is the document the page already has as a card
plan.append(entry(slug, raw, [image_block({lang: raw["data"][lang]["html"] for lang in LANGS}, slug),
                              block("paragraph", {lang: {"text": registered[lang]} for lang in LANGS}),
                              block("list", {lang: {"items": items[lang]} for lang in LANGS})] + cards,
                  existing_caption(documents, decision_28)))

# ---- 5. Avtoreferatlar ------------------------------------------------------------------------------------------------------------------------------------------
slug = "avtoreferatlar"
raw, _ = page_blocks(slug)
found = {lang: [(media_of(m.group(1)), plain(m.group(2))) for m in re.finditer(r'<a href="([^"]+)"[^>]*>(.*?)</a>', raw["data"][lang]["html"], re.S)] for lang in LANGS}
assert [u for u, _ in found["uz"]] == [u for u, _ in found["ru"]] == [u for u, _ in found["en"]] and len(found["uz"]) == 39
defences = []
for path, group in itertools.groupby(found["uz"], key=lambda x: x[0]):
    council, name, title = [text for _, text in group]
    defences.append((path, council, name, title))
assert len(defences) == 13
councils = {}
for _, council, _, _ in defences:
    code = re.search(r"122\.0(\d)", council).group(1)
    councils.setdefault(code, council)
HEAD = {"1": {"uz": "FARGʻONA JAMOAT SALOMATLIGI TIBBIYOT INSTITUTI HUZURIDAGI ILMIY DARAJALAR BERUVCHI PhD. 04/30.09.2020. Tib. 122.01 RAQAMLI ILMIY KENGASH ASOSIDA TUZILGAN BIR MARTALIK ILMIY KENGASH",
              "ru": "Разовый научный совет, созданный на базе научного совета PhD.04/30.09.2020.Tib.122.01 по присуждению учёных степеней при Ферганском медицинском институте общественного здоровья",
              "en": "One-time scientific council formed on the basis of the scientific council PhD.04/30.09.2020.Tib.122.01 awarding academic degrees at the Fergana Medical Institute of Public Health"},
        "2": {"uz": "FARGʻONA JAMOAT SALOMATLIGI TIBBIYOT INSTITUTI HUZURIDAGI ILMIY DARAJALAR BERUVCHI PhD. 04/02.07.2024. Tib. 122.02 RAQAMLI ILMIY KENGASH",
              "ru": "Научный совет PhD.04/02.07.2024.Tib.122.02 по присуждению учёных степеней при Ферганском медицинском институте общественного здоровья",
              "en": "Scientific council PhD.04/02.07.2024.Tib.122.02 awarding academic degrees at the Fergana Medical Institute of Public Health"}}
assert set(HEAD) == set(councils)
PROPER = {"FARGʻONA": "Fargʻona", "BUXORO": "Buxoro"}  # the capitals of proper names in the thesis titles


def name_case(text):  # "YOʻLDOSHEV SOBITALI ZOXIDJON OʻGʻLI" -> "Yoʻldoshev Sobitali Zoxidjon oʻgʻli"
    words = []
    for word in text.split():
        low = word.lower()
        words.append(low if low in ("oʻgʻli", "qizi") else low[:1].upper() + low[1:])
    return " ".join(words)


def title_case(text):  # "TIBBIY TAʻLIM ... (FARGʻONA SHAHRI MISOLIDA)" -> "Tibbiy taʻlim ... (Fargʻona shahri misolida)"
    low = text.lower()
    low = re.sub(r"covid\s*-\s*19", "COVID-19", low)
    low = re.sub(r"\b(\d)d\b", lambda m: m.group(1) + "D", low)
    for upper, proper in PROPER.items():
        low = low.replace(upper.lower(), proper)
    return re.sub(r"[^\W\d_]", lambda m: m.group(0).upper(), low, count=1)


CAPTION = {"uz": "Avtoreferat", "ru": "Автореферат", "en": "Abstract of the dissertation"}
blocks = []  # per defence: the council line (small grey), the author, the thesis title, the PDF card
for path, council, name, title in defences:
    code = re.search(r"122\.0(\d)", council).group(1)
    blocks.append(block("paragraph", {lang: {"text": HEAD[code][lang]} for lang in LANGS}))
    blocks.append(block("heading", {lang: {"text": name_case(name), "level": 3} for lang in LANGS}))
    blocks.append(block("paragraph", {lang: {"text": title_case(title)} for lang in LANGS}))
    blocks.append(block("document", {lang: {"media": path, "caption": CAPTION[lang]} for lang in LANGS}))
plan.append(entry(slug, raw, blocks))

json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"], len(e["blocks"])) for e in plan])
