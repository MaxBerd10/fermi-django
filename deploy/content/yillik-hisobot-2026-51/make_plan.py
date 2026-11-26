"""Builds plan.json of script 51 (FJSTI Ilmiy jurnali, six pages) from the live pages.
  * klinik-va-profilaktik-tibbiyot-jurnali, jurnal-xaqida: the cover picture and the cards (captions in three languages);
  * tahrir-hayati-kengashi: the board as a heading and "role: name" paragraphs between the two pictures;
  * jcpm-2023, jcpm-2024, jcpm-2025: every article (a link to its PDF) becomes a `document` card whose caption is the title of the article (the titles are in the
    language of the article, the same in the three languages); a title without a file stays a paragraph. The old CAPITALS of the titles are turned into normal writing.
    The Uzbek page is the base; an article that only the ru/en page listed is added after its neighbour; the stray HTML text of one old line is dropped.
    python deploy/content/yillik-hisobot-2026-51/make_plan.py"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _plan_tools import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
MENU = menu_labels(1864)
plan = []
notes_all = []


def get(slug):
    raw, documents = page_blocks(slug)
    return raw, documents, {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}


def para(texts):
    return block("paragraph", {lang: {"text": texts[lang]} for lang in LANGS})


# ---- sentence case of the old CAPITAL titles --------------------------------------------------------------------------------------------------------------------
KEEP_UPPER = {"ВИЧ", "ДНК", "РНК", "ВОЗ", "ЭКГ", "ХОБЛ", "ИБС", "ОРВИ", "ЖКТ", "ЦНС", "ПЦР", "МРТ", "УЗИ", "ЛПНП", "ХБП", "ХСН", "ИМТ", "ЖДА", "ИФА", "СОЭ", "СРБ", "ТТГ", "ВПЧ", "ГЭРБ", "ЭХО", "ЭКО",
              "HIV", "DNA", "RNA", "PCR", "MRI", "WHO", "COVID", "SARS", "BMI", "ECG", "COPD", "ICU", "CT", "AIDS", "HPV", "IVF", "TB", "ABCD", "CDK4/6", "COVID-19", "II", "III", "IV", "SSPE", "РПИ", "MAR", "MED", "ART", "GROUP"}
PROPER = ("ФЕРГАН", "УЗБЕКИСТАН", "БУХАР", "ТАШКЕНТ", "САМАРКАНД", "НАМАНГАН", "АНДИЖАН", "ХОРЕЗМ", "КАШКАДАРЬ", "СУРХАНДАРЬ", "ЮЖНОЙ ФЕРГАН", "FERGANA", "UZBEKISTAN", "TASHKENT", "FARGʻONA", "FARG'ONA",
          "BUXORO", "SAMARQAND", "ANDIJON", "NAMANGAN", "OʻZBEKISTON", "O'ZBEKISTON", "AFRIKA", "ЕВРОП", "АЗИ", "МОСКВ", "ЯПОН", "КИТАЙ", "КЫРГЫЗ", "КАЗАХСТАН", "РОСС", "ТАДЖИК", "ТУРКМЕН")
unknown_upper = set()


def sentence_case(title):
    title = re.sub(r"\\[þÿ]\\[þÿ] ", "", title)  # a damaged word of the old title ("работни\\þ\\ÿ ков")
    words = title.split(" ")
    out = []
    first = True
    for word in words:
        core = re.sub(r"^[^\w]+|[^\w]+$", "", word)
        if not core:
            out.append(word)
            continue
        letters = re.sub(r"[^A-Za-zА-Яа-яЁёʻ’']", "", core)
        if core.upper() in KEEP_UPPER or (any(ch.isdigit() for ch in core) and core.upper() == core):
            piece = word
        elif letters and letters.upper() == letters and (len(letters) > 1 or re.search("[А-Яа-я]", letters)):
            lowered = word.lower()
            if any(core.upper().startswith(p) for p in PROPER):
                lowered = re.sub(r"[^\W\d_]", lambda m: m.group(0).upper(), lowered, count=1)
            piece = lowered
            if len(letters) <= 4:
                unknown_upper.add(core)
        else:
            piece = word
        if first:
            piece = re.sub(r"[^\W\d_]", lambda m: m.group(0).upper(), piece, count=1)
            first = False
        out.append(piece)
    text = " ".join(out)
    for latin in ("Helicobacter pylori", "Escherichia coli", "Staphylococcus aureus", "Candida albicans", "Klebsiella pneumoniae", "Streptococcus pneumoniae"):
        text = re.sub(latin, latin, text, flags=re.I)  # the Latin names of species keep their own capitals
    return text


# ---- klinik-va-profilaktik-tibbiyot-jurnali -----------------------------------------------------------------------------------------------------------------------
slug = "klinik-va-profilaktik-tibbiyot-jurnali"
raw, documents, lines = get(slug)
htmls = {lang: raw["data"][lang]["html"] for lang in LANGS}
pictures = {lang: images_of(htmls[lang]) for lang in LANGS}
pdfs = {lang: [media_of(h) for h, _ in links_of(htmls[lang])] for lang in LANGS}
assert len(pictures["uz"]) == 1 and pictures["uz"] == pictures["ru"] == pictures["en"] and len(pdfs["uz"]) == 1 and pdfs["uz"] == pdfs["ru"] == pdfs["en"]
OAK = {"uz": "OAK xati: jurnal dissertatsiya natijalarini chop etish uchun tavsiya etilgan milliy ilmiy nashrlar roʻyxatida",
       "ru": "Письмо ВАК: журнал включён в перечень национальных научных изданий, рекомендованных для публикации результатов диссертаций",
       "en": "Letter of the Supreme Attestation Commission: the journal is on the list of national scientific publications recommended for publishing dissertation results"}
plan.append(entry(slug, raw, [image_block(pictures["uz"][0], {lang: MENU[slug][lang] for lang in LANGS}),
                              document_block(pdfs["uz"][0], {"uz": "Klinik va profilaktik tibbiyot jurnali, 1-son", "ru": "Журнал клинической и профилактической медицины, № 1",
                                                             "en": "Journal of Clinical and Preventive Medicine, No. 1"})],
                  captions_of_cards(documents, [OAK])))

# ---- tahrir-hayati-kengashi ---------------------------------------------------------------------------------------------------------------------------------------
slug = "tahrir-hayati-kengashi"
raw, documents, lines = get(slug)
htmls = {lang: raw["data"][lang]["html"] for lang in LANGS}
pictures = {lang: images_of(htmls[lang]) for lang in LANGS}
assert pictures["uz"] == pictures["ru"] == pictures["en"] and len(pictures["uz"]) == 2
assert all(len(lines[lang]) == 4 for lang in LANGS)


def name_case(text):
    return " ".join(w[:1].upper() + w[1:].lower() for w in text.split(" "))


def role_line(line, sep):
    role, rest = line.split(": ", 1) if ": " in line else line.split(":", 1)
    return role.strip(), rest.strip()


texts = {}
texts["uz"] = ["Ilmiy jurnal tahrir hayʻati", "Bosh muharrir: Sidikov Akmal Abdukaxxarovich — t.f.d., professor.", "Bosh muharrir yordamchisi: Kadirova Munira Rasulovna — p.f.d., professor.",
               "Masʻul kotib: Valitov Elyor Akimovich."]
texts["ru"] = ["Научный журнал. Редакционная коллегия", "Главный редактор: Сидиков Акмал Абдукахарович — д.м.н., профессор.",
               "Заместитель главного редактора: Кадырова Мунира Расуловна — д.п.н., профессор.", "Ответственный секретарь: Валитов Эльёр Акимович."]
texts["en"] = ["Scientific journal. Editorial board", "Editor-in-Chief: Sidikov Akmal Abdukakharovich — Doctor of Medical Sciences, Professor.",
               "Deputy Editor-in-Chief: Kadirova Munira Rasulovna — Doctor of Pedagogical Sciences, Professor.", "Executive Secretary: Valitov Elyor Akimovich."]
for lang, expected in (("uz", "SIDIKOV"), ("ru", "СИДИКОВ"), ("en", "SIDIKOV")):
    assert expected in lines[lang][1]["text"].upper(), lang
cover = {lang: MENU[slug][lang] for lang in LANGS}
plan.append(entry(slug, raw, [block("heading", {lang: {"text": texts[lang][0], "level": 2} for lang in LANGS}),
                              image_block(pictures["uz"][0], cover),
                              para({lang: texts[lang][1] for lang in LANGS}), para({lang: texts[lang][2] for lang in LANGS}), para({lang: texts[lang][3] for lang in LANGS}),
                              block("heading", {"uz": {"text": "Tahrir hayʻati aʻzolari", "level": 2}, "ru": {"text": "Члены редакционной коллегии", "level": 2},
                                                "en": {"text": "Members of the editorial board", "level": 2}}),
                              image_block(pictures["uz"][1], {"uz": "Tahrir hayʻati aʻzolari", "ru": "Члены редакционной коллегии", "en": "Members of the editorial board"})],
                  captions_of_cards(documents, [{lang: MENU[slug][lang] for lang in LANGS}])))

# ---- jurnal-xaqida -----------------------------------------------------------------------------------------------------------------------------------------------------
slug = "jurnal-xaqida"
raw, documents, lines = get(slug)
pictures = {lang: images_of(raw["data"][lang]["html"]) for lang in LANGS}
assert len(pictures["uz"]) == 1 and pictures["uz"] == pictures["ru"] == pictures["en"]
first_card = [d for d in documents if "caption" not in d["data"]["uz"]]
assert len(first_card) == 1
plan.append(entry(slug, raw, [image_block(pictures["uz"][0], {lang: MENU[slug][lang] for lang in LANGS})], captions_of_cards(first_card, [OAK])))


# ---- the archives -------------------------------------------------------------------------------------------------------------------------------------------------
def archive_items(lines_):
    items = []
    for line in lines_:
        if line["text"].startswith("<div") or line["text"].startswith("<span"):
            continue  # the HTML of an old paste, shown as text
        href = line["links"][0][0] if line["links"] else None
        items.append({"href": href, "text": line["text"]})
    return items


def merged(uz_items, other_items):
    key = lambda item: item["href"] or "text:" + item["text"]  # noqa: E731
    out = list(uz_items)
    have = {key(i) for i in out}
    previous = None
    for item in other_items:
        if key(item) not in have:
            position = 0 if previous is None else next(i for i, x in enumerate(out) if key(x) == key(previous)) + 1
            out.insert(position, item)
            have.add(key(item))
        previous = item
    return out


CARDS = {"jcpm-2024": [{"uz": "Varikoselektomiyaning ikkilamchi bepusht erkaklarda samaradorligini baholash",
                        "ru": "Оценка эффективности варикоцелэктомии у мужчин с первичным и вторичным бесплодием",
                        "en": "Evaluation of varicocelectomy efficacy in primarily and secondarily infertile men"}]}
for slug in ("jcpm-2023", "jcpm-2024", "jcpm-2025"):
    raw, documents, lines = get(slug)
    uz_items = archive_items(lines["uz"])
    items = merged(merged(uz_items, archive_items(lines["ru"])), archive_items(lines["en"]))
    blocks = []
    for item in items:
        title = sentence_case(item["text"])
        if item["href"]:
            blocks.append(document_block(media_of(item["href"]), same(title)))
        else:
            blocks.append(para(same(title)))
    notes = []
    extra = [i["text"][:50] for i in items if i not in uz_items]
    if extra:
        notes.append("added from the ru/en text (not in the Uzbek text): %s" % extra)
    plan_entry = entry(slug, raw, blocks, captions_of_cards(documents, CARDS.get(slug, [])))
    plan_entry["notes"] = notes
    plan.append(plan_entry)

json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"], len(e["blocks"])) for e in plan])
print("short capital words turned into lower case (check them):", sorted(unknown_upper))
for e in plan:
    for n in e.get("notes", []):
        print("  ", e["slug"], n)
