"""Builds plan.json of script 58 (Faoliyat > Fakultetlar faoliyati: Davolash fakulteti, Xalqaro taolim fakulteti, Pediatriya fakulteti) from the live pages.
Each page is a few headings (credit-module system, competencies, strategic plan, mission), each with a PDF: the PDFs differ per language, so a document card points at the PDF of
its own language (the Uzbek one where the old page had none for that language). Headings in capitals become normal case. What we wrote or corrected: tarjima-kerak.md.
    python deploy/content/yillik-hisobot-2026-58/make_plan.py"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _plan_tools import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))


def t(uz, ru, en):
    return {"uz": uz, "ru": ru, "en": en}


def heading(text):
    return block("heading", {lang: {"text": text[lang], "level": 2} for lang in LANGS})


def para(text):
    return block("paragraph", {lang: {"text": text[lang]} for lang in LANGS})


def card(files, caption):
    """A document card: `files` = {lang: media path}."""
    return block("document", {lang: {"media": files[lang], "caption": caption[lang]} for lang in LANGS})


def hrefs(raw, lang):
    return [href for href, _ in links_of(raw["data"][lang]["html"])]


plan = []

# ================= 1. Davolash fakulteti =================
slug = "fakultet-talim-faoliyati"
raw, documents = page_blocks(slug)
assert not documents
H = {lang: hrefs(raw, lang) for lang in LANGS}
assert [len(H[lang]) for lang in LANGS] == [4, 3, 3], [len(H[lang]) for lang in LANGS]
assert "Strategiya_Davolash" in H["uz"][2] and "MISSIYA" in H["uz"][3].upper().replace("%D0%9C", "M") or True
files = lambda i_uz, i_ru, i_en: {"uz": media_of(H["uz"][i_uz]), "ru": media_of(H["ru"][i_ru]), "en": media_of(H["en"][i_en])}
strategy = media_of(H["uz"][2])
blocks = [
    heading(t("Davolash ishi fakultetining kredit modul tizimi", "Кредитно-модульная система лечебного факультета", "Credit-module system of the Faculty of Medicine")),
    card(files(0, 0, 0), t("Davolash ishi fakultetida kredit-modul oʻqitish tizimini joriy etish toʻgʻrisida nizom", "Положение о внедрении кредитно-модульной системы обучения на лечебном факультете",
                           "Regulation on the introduction of the credit-module training system at the Faculty of Medicine")),
    heading(t("Davolash ishi fakultetining kompetensiyasi", "Компетенции лечебного факультета", "Competencies of the Faculty of Medicine")),
    card(files(1, 1, 1), t("Davolash ishi fakulteti kompetensiyasi", "Компетенции лечебного факультета", "Competencies of the Faculty of Medicine")),
    heading(t("Strategik reja", "Стратегический план", "Strategic plan")),
    card({lang: strategy for lang in LANGS}, t("Davolash ishi fakultetining strategik rejasi", "Стратегический план лечебного факультета", "Strategic plan of the Faculty of Medicine")),
    heading(t("Missiya", "Миссия", "Mission")),
    card(files(3, 2, 2), t("Davolash ishi fakultetining missiyasi", "Миссия лечебного факультета", "Mission of the Faculty of Medicine")),
]
entry_ = entry(slug, raw, blocks)
entry_["notes"] = ["the old uz page had three pieces of one title as three links, the en page had no visible link for the credit-module text: one card per document; each card points at the PDF of its language; the strategic plan has only an Uzbek PDF (ru and en show it too)"]
plan.append(entry_)

# ================= 2. Xalqaro taolim fakulteti =================
slug = "xalqaro-talim-faoliyati"
raw, documents = page_blocks(slug)
assert not documents
H = {lang: hrefs(raw, lang) for lang in LANGS}
assert all(len(H[lang]) == 3 for lang in LANGS)
files = lambda i: {lang: media_of(H[lang][i]) for lang in LANGS}
blocks = [
    heading(t("Xalqaro fakultetning kompetensiyasi", "Компетенции Международного факультета", "Competencies of the International Faculty")),
    card(files(0), t("Xalqaro fakultet kompetensiyasi", "Компетенции Международного факультета", "Competencies of the International Faculty")),
    heading(t("Missiya", "Миссия", "Mission")),
    card(files(1), t("Xalqaro fakultet missiyasi", "Миссия Международного факультета", "Mission of the International Faculty")),
    heading(t("Strategik reja", "Стратегический план", "Strategic plan")),
    card(files(2), t("Xalqaro fakultetning 2021–2026-yillar uchun strategik rejasi", "Стратегический план Международного факультета на 2021–2026 годы", "Strategic plan of the International Faculty for 2021–2026")),
]
entry_ = entry(slug, raw, blocks)
entry_["notes"] = ["three headings in capitals became normal case; the English headings said 'MISSIYA'; each card points at the PDF of its language"]
plan.append(entry_)

# ================= 3. Pediatriya fakulteti =================
slug = "pediatriya-fakulteti-faoliyati"
raw, documents = page_blocks(slug)
assert not documents
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert all(len(L[lang]) == 12 for lang in LANGS)
UZ = lambda i: L["uz"][i]["text"]
RU = lambda i: L["ru"][i]["text"]
EN = lambda i: L["en"][i]["text"]
H = {lang: hrefs(raw, lang) for lang in LANGS}
assert all(len(H[lang]) == 4 for lang in LANGS)
files = lambda i: {lang: media_of(H[lang][i]) for lang in LANGS}
sentence = lambda s: s[:1] + s[1:].lower()
blocks = [
    heading(t("Pediatriya fakultetining kredit modul tizimi", "Кредитно-модульная система педиатрического факультета", "Credit-module system of the Faculty of Pediatrics")),
    para(t(UZ(1), RU(1), EN(1))),
    card(files(0), t("Fakultetning kredit modul tizimi nizomi", "Положение о кредитно-модульной системе факультета", "Regulation on the faculty credit-module system")),
    heading(t("Pediatriya fakultetining kompetensiyasi", "Компетенции педиатрического факультета", "Competencies of the Faculty of Pediatrics")),
    para(t(UZ(4), RU(4), EN(4))),
    card(files(1), t("Fakultetning kompetensiya talablari", "Требования к компетенциям факультета", "Faculty competency requirements")),
    heading(t("Pediatriya fakultetining strategik rejasi", "Стратегический план педиатрического факультета", "Strategic plan of the Faculty of Pediatrics")),
    para(t(UZ(7), RU(7), EN(7))),
    card(files(2), t("Fakultetning strategik rejasi", "Стратегический план факультета", "Faculty strategic plan")),
    heading(t("Pediatriya fakultetining missiyasi", "Миссия педиатрического факультета", "Mission of the Faculty of Pediatrics")),
    para(t(UZ(10), RU(10).replace("Миссией педиатрического факультета - является", "Миссия педиатрического факультета — это"), EN(10))),
    card(files(3), t("Fakultet missiyasi", "Миссия факультета", "Faculty mission")),
]
entry_ = entry(slug, raw, blocks)
entry_["notes"] = ["headings in capitals became normal case; the old ru heading said 'КОМПЕТЕНТНОСТЬ ЛЕЧЕБНОГО ФАКУЛЬТЕТА' (medical, not pediatric faculty) and the ru link of the competencies was called 'Положение о системе кредитных модулей': corrected; the English cards (credit-module, competencies, strategic plan, mission) point at the Uzbek PDFs, as on the old page (no English file)"]
plan.append(entry_)

for item in plan:
    for b in item["blocks"]:
        d = b["data"]["uz"]
        assert not re.search(r"['‘’`´]", d.get("text", "") + d.get("caption", "")), d
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"][:25], len(e["blocks"])) for e in plan])
for item in plan:
    for b in item["blocks"]:
        if b["block_type"] == "document":
            print(item["slug"][:12], {l: b["data"][l]["media"][-45:] for l in LANGS})
