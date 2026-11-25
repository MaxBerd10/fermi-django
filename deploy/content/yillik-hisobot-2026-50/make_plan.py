"""Builds plan.json of script 50 (Meʻyoriy hujjatlar, seven pages) from the live pages.
Every page becomes typed blocks; the text of the Uzbek page is the base and the Russian/English text is aligned to it line by line. Where a language had no text
(or only a copy of the Uzbek text) the line is translated here (listed in tarjima-kerak.md). A link inside a line is kept as [label](address).
    python deploy/content/yillik-hisobot-2026-50/make_plan.py"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _plan_tools import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
MENU = menu_labels(1879)
MEDIA = "https://fermi.uz/media/"


def para(texts):
    return block("paragraph", {lang: {"text": texts[lang]} for lang in LANGS})


def get(slug):
    raw, documents = page_blocks(slug)
    return raw, documents, {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}


def url(path):  # a file of the media folder as an address
    return MEDIA + path.replace(" ", "%20").replace("(", "%28").replace(")", "%29")


def link(label, address):
    return "[%s](%s)" % (label, address)


plan = []

# ---- Taʻlim toʻgʻrisida: the facts of the law (the page shows them as a list of facts) --------------------------------------------------------------------------
slug = "talim-togrisia"
raw, documents, lines = get(slug)
facts = {lang: [l["text"] for l in lines[lang][1:9]] for lang in LANGS}  # line 0 is the title (the page title says it)
assert lines["uz"][0]["text"] == "Taʻlim toʻgʻrisida" and all(len(facts[lang]) == 8 for lang in LANGS)
facts["ru"][3] = "Орган: Олий Мажлис Республики Узбекистан"
facts["ru"][4] = "Номер: ЗРУ-637"
facts["en"][3] = "Issuing body: Oliy Majlis of the Republic of Uzbekistan"
facts["en"][4] = "Number: ZRU-637"
assert facts["en"][1].startswith("Document Title:") and facts["uz"][4].startswith("Raqam:")
facts["en"][1] = "Document title: On Education"
plan.append(entry(slug, raw, [para({lang: facts[lang][i] for lang in LANGS}) for i in range(8)], captions_of_cards(documents, [{
    "uz": "Oʻzbekiston Respublikasining Qonuni «Taʻlim toʻgʻrisida» OʻRQ-637 23.09.2020",
    "ru": "Закон Республики Узбекистан «Об образовании» ЗРУ-637 от 23.09.2020",
    "en": "The Law of the Republic of Uzbekistan “On Education” ZRU-637 of 23.09.2020"}])))

# ---- (Kredit modul nizomi is also a page of Institut haqida: script 42 turns its scan into an image block and script 45 captions its card)

# ---- Taraqqiyot strategiyasi -----------------------------------------------------------------------------------------------------------------------------------
slug = "taraqqiyot-strategiyasi"
raw, documents, lines = get(slug)
assert not documents and all(len(lines[lang]) == 4 for lang in LANGS)
pdf = {lang: media_of(lines[lang][3]["links"][0][0]) for lang in LANGS}
assert pdf["uz"] == pdf["ru"] == pdf["en"]
head = {"uz": ["OʻZBEKISTON RESPUBLIKASI PREZIDENTINING", "FARMONI", lines["uz"][2]["text"]],
        "ru": ["УКАЗ", "ПРЕЗИДЕНТА РЕСПУБЛИКИ УЗБЕКИСТАН", "О СТРАТЕГИИ РАЗВИТИЯ НОВОГО УЗБЕКИСТАНА НА 2022–2026 ГОДЫ"],
        "en": [lines["en"][0]["text"], lines["en"][1]["text"], lines["en"][2]["text"]]}
head["uz"][0] = head["uz"][0].replace("'", "ʻ")
assert head["en"][0] == "DECREE"
blocks = [para({lang: head[lang][i] for lang in LANGS}) for i in range(3)]
blocks.append(document_block(pdf["uz"], {"uz": "Oʻzbekiston Respublikasi Prezidentining Farmoni, 28.01.2022 yildagi PF-60-son",
                                          "ru": "Указ Президента Республики Узбекистан от 28.01.2022 г. № УП-60 (PDF, на узбекском языке)",
                                          "en": "Decree of the President of the Republic of Uzbekistan No. PF-60 of 28.01.2022 (PDF, in Uzbek)"}))
plan.append(entry(slug, raw, blocks))

# ---- Prezident farmon va qarorlari: an index of acts ------------------------------------------------------------------------------------------------------------
slug = "prezident-farmon-va-qarorlari"
raw, documents, lines = get(slug)
FARMON = "Prezident Farmonlari/"
LEX = "https://lex.uz/"
pdf_uz = {l["links"][0][0]: l["md"] for l in lines["uz"] if l["links"] and "/media/" in l["links"][0][0]}
pdf_ru = {l["links"][0][0]: l["md"] for l in lines["ru"] if l["links"] and "/media/" in l["links"][0][0]}


def find(lines_, needle):
    found = [l for l in lines_ if l["links"] and needle in l["links"][0][0]]
    assert found, needle
    return found[0]


def pdf_of(lines_, needle):
    found = find(lines_, needle)
    return found["links"][0][0], found["text"]


entries = []  # (uz, ru, en) texts
u = lambda t, a: link(t, a)  # noqa: E731
a_gem = "https://lex.uz/uz/docs/-5436849"
entries.append((u(find(lines["uz"], "-5436849")["text"], a_gem),
                u("О дальнейшем совершенствовании системы оказания гематологических и онкологических услуг населению", a_gem),
                u("On further improving the system of hematology and oncology services for the population", a_gem)))
a_6221 = "https://lex.uz/uz/docs/-5411129"
entries.append((find(lines["uz"], "-5411129")["md"], find(lines["ru"], "-5411129")["md"],
                u("Decree of the President of the Republic of Uzbekistan No. UP-6221 of 05.05.2021", a_6221)))
a_6110 = "https://lex.uz/docs/-5100677"
uz_6110 = [l for l in lines["uz"] if l["links"] and "-5100677" in l["links"][0][0] and "Farmoni" in l["text"]][0]
entries.append((uz_6110["md"], find(lines["ru"], "-5100677")["md"], u("Decree of the President of the Republic of Uzbekistan No. UP-6110 of 12.11.2020", a_6110)))
entries.append(("Oʻzbekiston Respublikasi aholisiga 2017 — 2021 yillarda ixtisoslashtirilgan tibbiy yordam koʻrsatishni yanada rivojlantirish chora-tadbirlari toʻgʻrisida",
                "О мерах по дальнейшему развитию специализированной медицинской помощи населению Республики Узбекистан в 2017–2021 годах",
                "On measures to further develop specialized medical care for the population of the Republic of Uzbekistan in 2017–2021"))
a_tab = "https://lex.uz/docs/-4785739"
entries.append((find(lines["uz"], "-4785739")["md"], u("О дополнительных мерах по развитию народной медицины в Республике Узбекистан", a_tab),
                u("On additional measures for the development of traditional medicine in the Republic of Uzbekistan", a_tab)))
EN = {"408": "On measures to improve the system of providing medical institutions with pharmaceutical products and medical equipment",
      "5199": "On measures to further improve the system of specialized medical care in the healthcare sector",
      "5124": "On additional measures for the comprehensive development of the healthcare sector",
      "4891": "On additional measures to ensure public health by further increasing the effectiveness of medical prevention work",
      "6099": "On measures to widely introduce a healthy lifestyle and further develop mass sports"}
pairs = [("PQ-408-", "PQ-408-", "408"), ("PQ-5199-", "%D0%9F%D0%9F-5199-", "5199"), ("PQ-5124-", "%D0%9F%D0%9F-5124", "5124"),
         ("PQ-4891-Tibbiy", "%D0%9F%D0%9F-408.pdf", "4891"), ("PF-6099", "%D0%A3%D0%9F-6099", "6099")]
for uz_key, ru_key, code in pairs:
    uz_line, ru_line = find(lines["uz"], uz_key), find(lines["ru"], ru_key)
    entries.append((uz_line["md"], ru_line["md"], u(EN[code], ru_line["links"][0][0])))
a_food_uz = "https://lex.uz/docs/-5090241"
ru_food = [l for l in lines["ru"] if "4887" in l["links"][0][0]] if False else [l for l in lines["ru"] if l["links"] and "%D0%9F%D0%9F-4887" in l["links"][0][0]]
assert len(ru_food) == 1
uz_food = find(lines["uz"], "-5090241")
entries.append((u("Aholini sogʻlom ovqatlanishini taʻminlash toʻgʻrisida", a_food_uz), ru_food[0]["md"],
                u("On additional measures to ensure healthy nutrition of the population", ru_food[0]["links"][0][0])))
assert uz_food["text"].startswith("Aholini sogʻlom ovqatlanishini taʻminlsh")
blocks = [para({"uz": e[0], "ru": e[1], "en": e[2]}) for e in entries]
plan.append(entry(slug, raw, blocks, captions_of_cards(documents, [{
    "uz": "Oʻzbekiston Respublikasi Prezidentining 2020-yil 3-dekabrdagi PQ-4911-son qarori «Fargʻona jamoat salomatligi tibbiyot institutini tashkil etish toʻgʻrisida»",
    "ru": "Постановление Президента Республики Узбекистан от 03.12.2020 г. № ПП-4911 «О создании Ферганского медицинского института общественного здоровья»",
    "en": "Resolution of the President of the Republic of Uzbekistan No. PP-4911 of 03.12.2020 “On the establishment of the Fergana Medical Institute of Public Health”"}])))

# ---- Davlat dasturlari: a list of the years --------------------------------------------------------------------------------------------------------------------
slug = "davlat-dasturlari"
raw, documents, lines = get(slug)
assert all(len(lines[lang]) == 31 for lang in LANGS)
blocks = [para({lang: lines[lang][i]["md"] for lang in LANGS}) for i in range(31)]
blocks[0]["data"]["en"]["text"] = blocks[0]["data"]["en"]["text"].rstrip('"')
plan.append(entry(slug, raw, blocks, captions_of_cards(documents, [{
    "uz": "Prezident Farmoni PF-37, 21.02.2024: «Oʻzbekiston — 2030» strategiyasini 2024-yilda amalga oshirishga oid davlat dasturi",
    "ru": "Указ Президента PF-37 от 21.02.2024: Государственная программа по реализации стратегии «Узбекистан — 2030» в 2024 году",
    "en": "Presidential Decree PF-37 of 21.02.2024: the State Programme for the implementation of the “Uzbekistan — 2030” strategy in 2024"}])))

# ---- the two orders of the ministry about the state standard ---------------------------------------------------------------------------------------------------
UZ_ORDER_HEAD_EN = ["ORDER", "OF THE MINISTER OF HIGHER AND SECONDARY SPECIAL EDUCATION OF THE REPUBLIC OF UZBEKISTAN"]
for slug, card_caption in (
    ("oliy-talimning-davlat-talim-standarti", {"uz": "Oliy taʻlimning davlat taʻlim standarti. Asosiy qoidalar (Oʻz DSt 3556:2021)",
                                              "ru": "Государственный стандарт высшего образования. Основные положения (O’z DSt 3556:2021)",
                                              "en": "State standard of higher education. Basic rules (O’z DSt 3556:2021)"}),
    ("oliy-talim-yonalishlari-va-mutaxassisliklari-klassifikatori", {"uz": "Oliy taʻlim yoʻnalishlari va mutaxassisliklari klassifikatori (Oʻz DSt 3557:2021)",
                                                                     "ru": "Классификатор направлений образования и специальностей высшего образования (O’z DSt 3557:2021)",
                                                                     "en": "Classifier of the fields of study and specialities of higher education (O’z DSt 3557:2021)"})):
    raw, documents, lines = get(slug)
    uz, ru, en = lines["uz"], lines["ru"], lines["en"]
    for line in en:  # the quotation marks of the English title
        line["md"] = line["md"].replace("BASIC RULES\"", "BASIC RULES”")
    if slug.startswith("oliy-talim-yonalishlari"):
        assert en[0]["text"].startswith("This is an official document")
        en = en[1:]
        texts_en = ["ORDER", "OF THE MINISTER OF HIGHER AND SECONDARY SPECIAL EDUCATION OF THE REPUBLIC OF UZBEKISTAN",
                    "ON APPROVAL OF THE STATE STANDARD OF THE REPUBLIC OF UZBEKISTAN “STATE STANDARD OF HIGHER EDUCATION. CLASSIFIER OF FIELDS OF STUDY AND SPECIALITIES OF HIGHER EDUCATION”",
                    "Technical specifications"]
        texts_en += ["(O’z DSt 3557.2021)", "[Registered by the Ministry of Justice of the Republic of Uzbekistan on October 27, 2021. Registration number 42]",
                     "The text of the act is given in [Uzbek](https://lex.uz/docs/5701176).", "Minister A. TOSHKULOV", "Tashkent,", "October 19, 2021", "No. 11"]
        en_lines = [{"md": t, "text": t} for t in texts_en]
        assert len(uz) == 13 and len(ru) == 11 and len(en_lines) == 11, (len(uz), len(ru), len(en_lines))
        head_n, tail_ru, tail_en = 5, ru[3:], en_lines[3:]
        # uz: 0-2 head, 3 (Texnik xujjatlar), 4 (Oʻz DSt), 5 registration, 6 preamble (links), 7-8 clauses, 9-12 signature
        # ru/en: 0-2 head, 3 technical conditions, 4 (O'z DSt), 5 registration, 6 note (+link), 7-10 signature
        offsets = (3, 3)
    else:
        assert len(uz) == 12 and len(ru) == 10 and len(en) == 10, (len(uz), len(ru), len(en))
        en_lines = en
        tail_ru, tail_en = ru[3:], en_lines[3:]
    blocks = []
    for i in range(6 if slug.startswith("oliy-talim-yonalishlari") else 5):
        if slug.startswith("oliy-talim-yonalishlari"):
            blocks.append(para({"uz": uz[i]["md"], "ru": ru[i]["md"], "en": en_lines[i]["md"]}))
        else:
            blocks.append(para({"uz": uz[i]["md"], "ru": ru[i]["md"], "en": en_lines[i]["md"]}))
    base = len(blocks)
    note = {"ru": ru[base]["md"], "en": en_lines[base]["md"]}
    assert "узбекском" in note["ru"] and "Uzbek" in note["en"], note
    if "узбекском" in note["ru"] and "Uzbek" in note["en"] and "](" not in note["en"]:
        note["en"] = note["en"].replace("Uzbek", "[Uzbek](%s)" % ru[base]["links"][0][0], 1)
    clause_1, clause_2 = uz[base + 1]["md"], uz[base + 2]["md"]
    blocks.append(para({"uz": uz[base]["md"], "ru": note["ru"], "en": note["en"]}))
    blocks.append(para({"uz": clause_1, "ru": clause_1, "en": clause_1}))  # the act is published in Uzbek only: ru/en show the Uzbek text under the note
    blocks.append(para({"uz": clause_2, "ru": clause_2, "en": clause_2}))
    for k in range(4):
        blocks.append(para({"uz": uz[base + 3 + k]["md"], "ru": ru[base + 1 + k]["md"], "en": en_lines[base + 1 + k]["md"]}))
    plan.append(entry(slug, raw, blocks, captions_of_cards(documents, [card_caption])))

# ---- SSV buyruqlari: four orders as links to their files --------------------------------------------------------------------------------------------------------
slug = "ozbeksiton-respublikasi-ssv-buyruqlari"
raw, documents, lines = get(slug)
assert all(len(lines[lang]) == 4 for lang in LANGS)
ORDERS = [
    ({"ru": "О приеме в клиническую ординатуру (ординатуру) в 2024/2025 учебном году",
      "en": "On admission to clinical residency (residency) for the 2024/2025 academic year"}),
    ({"ru": "Об обеспечении исполнения постановления Президента Республики Узбекистан от 30 декабря 2022 года № ПП-471 «О мерах по обеспечению исполнения Закона Республики Узбекистан «О Государственном бюджете Республики Узбекистан на 2023 год»».",
      "en": "On ensuring the implementation of the Resolution of the President of the Republic of Uzbekistan No. PQ-471 of 30 December 2022 “On measures to ensure the implementation of the Law of the Republic of Uzbekistan “On the State Budget of the Republic of Uzbekistan for 2023””."}),
    ({"ru": "О назначении председателей координирующих экспертных советов, действующих при медицинских высших образовательных учреждениях, республиканских специализированных научно-практических медицинских центрах и научно-исследовательских институтах, находящихся в ведении Министерства здравоохранения.",
      "en": "On the appointment of chairpersons of the coordinating Expert Councils operating at the medical higher education institutions, the republican specialized scientific and practical medical centres and the research institutes under the Ministry of Health."}),
    ({"ru": "О внедрении в практику научных, прикладных и фундаментальных разработок по приоритетным направлениям развития науки и технологий и их результатов.",
      "en": "On the introduction into practice of scientific, applied and fundamental developments in the priority areas of science and technology development and of their results."}),
]
paths = [media_of(lines["uz"][i]["links"][0][0]) for i in range(4)]
assert paths == [media_of(lines[lang][i]["links"][0][0]) for lang in ("ru", "en") for i in range(4)][:4] and paths == [media_of(lines["en"][i]["links"][0][0]) for i in range(4)]
blocks = []
for i, translations in enumerate(ORDERS):
    address = url(paths[i])
    blocks.append(para({"uz": link(lines["uz"][i]["text"], address), "ru": link(translations["ru"], address), "en": link(translations["en"], address)}))
plan.append(entry(slug, raw, blocks, captions_of_cards(documents, [{
    "uz": "Sogʻliqni saqlash vazirligining 236-son buyrugʻi: kredit-modul oʻqitish tizimini joriy etish",
    "ru": "Приказ Министерства здравоохранения № 236: внедрение кредитно-модульной системы обучения",
    "en": "Ministry of Health Order No. 236: introduction of the credit-module system of teaching"}])))

json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"], len(e["blocks"])) for e in plan])
