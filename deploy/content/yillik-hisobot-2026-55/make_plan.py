"""Builds plan.json of script 55 (Faoliyat > Ilmiy faoliyat: five pages still written as one old HTML block) from the live pages.
Pages: Ilmiy faoliyat boyicha normativ-huquqiy hujjatlar, FJSTI Grant siyosati, Innovatsion goyalar, Ilmiy tadqiqot yonalishlari, Oliy oquv yurtidan keyingi taolim.
Uzbek is the base. Russian and English follow it block by block (the old pages had different line counts, a missing English half, one wrong date and stray labels); what we had to
translate or correct is listed in tarjima-kerak.md.
    python deploy/content/yillik-hisobot-2026-55/make_plan.py"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _plan_tools import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))


def t(uz, ru, en):
    return {"uz": uz, "ru": ru, "en": en}


def heading(text, level=2):
    return block("heading", {lang: {"text": text[lang], "level": level} for lang in LANGS})


def para(text):
    return block("paragraph", {lang: {"text": text[lang]} for lang in LANGS})


def items(text):
    return block("list", {lang: {"items": text[lang]} for lang in LANGS})


def spaced(text):
    """A link written as [label](address) must be followed by a space before a letter: "[qarori](..)tahririda" -> "[qarori](..) tahririda"."""
    return re.sub(r"(\]\([^)\s]+\))(?=\w)", r"\1 ", text)


def unnumber(text):
    return re.sub(r"^\s*(?:\d+\.\s*|•\s*(?:\.\s*)?)", "", text).strip()


def load(slug):
    raw, documents = page_blocks(slug)
    lines = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
    return raw, documents, lines


def md(lines, lang, i):
    return spaced(lines[lang][i]["md"])


def uz_ok(text):
    assert not re.search(r"['‘’`´]", text), text  # Uzbek uses only ʻ (U+02BB) and ʼ (U+02BC)
    return text


plan = []
NOTES = {}

# ================= 1. FJSTI Grant siyosati =================
slug = "fjsti-grant-siyosati"
raw, documents, L = load(slug)
assert len(L["uz"]) == 13 and len(L["ru"]) == 14 and len(L["en"]) == 12
assert L["ru"][6]["text"] == "Ответственный за рассмотрение гранта:"  # a label with nothing after it (only in Russian)
URL = "https://gov.uz/oz/innovation"
uz_intro = L["uz"][0]["text"].replace("hakida", "haqida")
ru_intro = L["ru"][0]["text"].rstrip(".") + ": " + URL
en_intro = L["en"][0]["text"]
assert uz_intro.endswith(URL) and en_intro.endswith(URL)
links = {k: re.search(r"\[[^\]]+\]\(([^)]+)\)", md(L, "uz", 6 + k)).group(1) for k in range(6)}
assert links[5].startswith("https://www.uni-stuttgart.de") and links[0] == "https://eyuf.uz/"


def link_item(lang, index, text):
    label = {0: "eyuf.uz", 1: "itpu.uz", 2: "yoshlarportali.uz", 3: "edu.uz", 4: "www.maltalingua.com/scholarship", 5: "uni-stuttgart.de/en/study/application/dates"}[index]
    return "[%s](%s) – %s" % (label, links[index], text)


def tail(lang, index):
    """The text after the dash of a useful-link line."""
    line = unnumber(L[lang][{"uz": 6, "ru": 8, "en": 6}[lang] + index]["text"])
    return line.split(" – ", 1)[1].strip()


ru_tail = [tail("ru", i) for i in range(5)] + ["стипендии для бакалавриата и магистратуры в Штутгартском университете (Германия)"]
en_tail = [tail("en", i) for i in range(5)] + ["scholarships for bachelor’s and master’s studies at the University of Stuttgart, Germany"]
uz_tail = [tail("uz", i) for i in range(6)]
useful = t([link_item("uz", i, uz_tail[i]) for i in range(6)], [link_item("ru", i, ru_tail[i]) for i in range(6)], [link_item("en", i, en_tail[i]) for i in range(6)])
blocks = [
    heading(t("Grant haqida", "О грантах", "About grants")),
    para(t(uz_ok(uz_intro), ru_intro, en_intro)),
    para(t(L["uz"][1]["text"], L["ru"][2]["text"], L["en"][1]["text"])),
    items(t([uz_ok("Tanlovning asosiy maqsadi bilan tanishish"), uz_ok("Arizani toʻldirish va vazirlik veb-saytida elektron roʻyxatdan oʻtkazish: " + URL), uz_ok("Loyihalarni tanlovga qogʻoz shaklida yuborish")],
            ["Ознакомиться с основной целью конкурса", "Заполнить заявку и пройти электронную регистрацию на сайте Министерства: " + URL, "Подать проекты на конкурс в бумажной форме"],
            [unnumber(L["en"][2]["text"]), unnumber(L["en"][3]["text"]).replace(", https", ": https"), unnumber(L["en"][4]["text"])])),
    heading(t(L["uz"][5]["text"].rstrip(":"), L["ru"][7]["text"].rstrip(":"), L["en"][5]["text"].rstrip(":"))),
    items(useful),
]
title = t("Iqtidorli mutaxassislarning xorijda taʼlim olishini qoʻllab-quvvatlash, ularda kasbiy koʻnikmalarini rivojlantirish va ragʻbatlantirishga oid qoʻshimcha chora-tadbirlar toʻgʻrisida",
          "О дополнительных мерах по поддержке обучения за рубежом одарённых специалистов, развитию их профессиональных навыков и их стимулированию",
          "On additional measures to support the training abroad of gifted specialists, to develop their professional skills and to stimulate them")
plan.append(entry(slug, raw, blocks, captions_of_cards(documents, [title])))
NOTES[slug] = ["the heading 'Grant haqida' is new (the old page started without one); the numbers 1. 2. 3. of the steps are gone (a list); ru: the empty label 'Ответственный за рассмотрение гранта:' is dropped",
               "the all-capitals line at the end was the title of the PDF card: it is now the caption of the card (normal case, the Russian and English lines were cut short: completed)"]

# ================= 2. Innovatsion goyalar =================
slug = "innovatsion-goyalar"
raw, documents, L = load(slug)
assert all(len(L[lang]) == 10 for lang in LANGS)
picture = images_of(raw["data"]["uz"]["html"])
assert len(picture) == 1 and all(images_of(raw["data"][lang]["html"]) == picture for lang in LANGS)
blocks = [
    heading(t(L["uz"][0]["text"], L["ru"][0]["text"], L["en"][0]["text"])),
    image_block(picture[0], t(L["uz"][0]["text"], L["ru"][0]["text"], L["en"][0]["text"])),
    para(t(*[L[lang][1]["text"] for lang in LANGS])),
    para(t(*[L[lang][2]["text"] for lang in LANGS])),
    para(t(*[L[lang][3]["text"] for lang in LANGS])),
    heading(t(L["uz"][4]["text"].rstrip(":"), L["ru"][4]["text"].rstrip(":"), L["en"][4]["text"].rstrip(":")), 3),
    items(t([unnumber(L["uz"][i]["text"]).rstrip(";.") for i in (5, 6, 7)], [unnumber(L["ru"][i]["text"]).rstrip(";.") for i in (5, 6, 7)], [unnumber(L["en"][i]["text"]).rstrip(";.") for i in (5, 6, 7)])),
    items(t([re.sub(r"kim\?-\s*", "kim? — ", unnumber(L["uz"][i]["text"])) for i in (8, 9)],
            [unnumber(L["ru"][i]["text"]).replace("потребителем? -", "потребителем? —") for i in (8, 9)],
            [unnumber(L["en"][i]["text"]).replace("consumer?-", "consumer? —") for i in (8, 9)])),
]
for b in blocks:
    for lang in ("uz",):
        d = b["data"][lang]
        uz_ok(" ".join([d.get("text", "")] + (d.get("items", []))))
plan.append(entry(slug, raw, blocks, captions_of_cards(documents, [t("Loyiha tavsifi (PDF, inglizcha)", "Описание проекта (PDF, на английском)", "Project description (PDF)")])))
NOTES[slug] = ["the picture, which was the first line, now stands after the title; the numbered results and the two bullet lines became two lists"]

# ================= 3. Ilmiy tadqiqot yonalishlari =================
slug = "ilmiy-tadqiqot-yonalishlari"
raw, documents, L = load(slug)
assert all(len(L[lang]) == 2 for lang in LANGS)
assert L["uz"][1]["text"] == "https://lex.uz/ru/"  # the homepage of lex.uz written as a link: not a document
blocks = [
    para(t("Oʻzbekiston Respublikasi Vazirlar Mahkamasining 2022-yil 7-martdagi 101-sonli Farmoyishi",
           "Распоряжение Кабинета Министров Республики Узбекистан № 101 от 7 марта 2022 года",
           "Order of the Cabinet of Ministers of the Republic of Uzbekistan No. 101 dated March 7, 2022")),
]
plan.append(entry(slug, raw, blocks, captions_of_cards(documents, [t("Ilmiy tadqiqot yoʻnalishlari va ilmiy kadrlar tayyorlash", "Направления научных исследований и подготовка научных кадров", "Research directions and training of scientific staff")])))
NOTES[slug] = ["the old text was a link to a PDF on the old site fjsti.uz (404 now, also at fermi.uz) and the address https://lex.uz/ru/ (a homepage, not a document): both links are dropped, the title of the order stays as text",
               "uz title was half Cyrillic ('Вазирлар Mahkamasining 2022 йил'), ru 'Постановления ... Минимтров', en 'Dacree': one clean title per language (the old uz says Farmoyish, ru Постановление, en Decree: we use Farmoyish / Распоряжение / Order)"]

# ================= 4. Oliy oquv yurtidan keyingi talim =================
slug = "oliy-oquv-yurtidan-keyingi-talim"
raw, documents, L = load(slug)
assert len(L["uz"]) == 23 and len(L["ru"]) == 25 and len(L["en"]) == 25
picture = images_of(raw["data"]["uz"]["html"])
assert len(picture) == 1 and all(images_of(raw["data"][lang]["html"]) == picture for lang in LANGS)
UZ = lambda i: L["uz"][i]["text"]
RU = lambda i: L["ru"][i]["text"]
EN = lambda i: L["en"][i]["text"]
legal = t("Oliy taʼlimdan keyingi taʼlimni tashkil etish va amalga oshirish faoliyati quyidagilarga asoslanadi:", RU(6), EN(6))
legal_items = t(["Oʻzbekiston Respublikasi Prezidentining 2017-yil 16-fevraldagi PF-4958-son «Oliy oʻquv yurtidan keyingi taʼlim tizimini yanada takomillashtirish toʻgʻrisida»gi Farmoni",
                 "Oʻzbekiston Respublikasi Vazirlar Mahkamasining 2017-yil 22-maydagi 304-son «Oliy taʼlimdan keyingi taʼlim tizimini yanada takomillashtirish chora-tadbirlari toʻgʻrisida»gi Qarori"],
                [RU(7).rstrip(";"), RU(8).rstrip(".")], [EN(7).rstrip(";"), EN(8).rstrip(".")])
for text in legal_items["uz"] + [legal["uz"]]:
    uz_ok(text)
link_texts = [md(L, "uz", i) for i in range(16, 23)]
hrefs = [re.search(r"\]\(([^)]+)\)", x).group(1) for x in link_texts]
assert hrefs[1].endswith("Ilmiy%20daraja%20berish%20tartibi.pdf")  # the page already has this PDF as a card (the 2nd of the seven)
cap = {
    0: t("Ilmiy darajalar beruvchi ilmiy kengash toʻgʻrisidagi Nizom", "Положение о научном совете по присуждению учёных степеней", "Regulation on the scientific council awarding academic degrees"),
    1: t("Ilmiy daraja berish tartibi toʻgʻrisidagi Nizom", "Положение о порядке присуждения учёных степеней", "Regulation on the procedure for awarding academic degrees"),
    2: t("Ilmiy unvonlar berish tartibi toʻgʻrisidagi Nizom", "Положение о порядке присвоения учёных званий", "Regulation on the procedure for awarding academic titles"),
    3: t("Malakaviy imtihonlarni oʻtkazish tartibi toʻgʻrisidagi Nizom", "Положение о порядке проведения квалификационных экзаменов", "Regulation on the procedure for qualification examinations"),
    4: t("Ekspert kengashi toʻgʻrisidagi Nizom", "Положение об Экспертном совете", "Regulation on the Expert Council"),
    5: t("Dissertatsiya va dissertatsiya avtoreferatini rasmiylashtirish qoidalari", "Правила оформления диссертации и автореферата диссертации", "Rules for preparing a dissertation and its abstract"),
    6: t("Dissertatsiyalar ilmiy natijalarining amaliyotga joriy qilinishini baholash boʻyicha uslubiy koʻrsatmalar", "Методические указания по оценке внедрения в практику научных результатов диссертаций", "Methodological guidelines for assessing the introduction of the scientific results of dissertations into practice"),
}
blocks = [
    para(t(UZ(0), RU(0), EN(0))),
    image_block(picture[0], t("Ilmiy kadrlar tayyorlash", "Подготовка научных кадров", "Training of scientific staff")),
    para(t(UZ(1), RU(1).rstrip(":") + ":", EN(1))),
    items(t(["Tayanch doktorantura (PhD darajasi uchun)", "Doktorantura (DSc darajasi uchun)", "Mustaqil izlanuvchilik (PhD yoki DSc darajasiga daʼvogarlar uchun)"],
            [RU(2).rstrip(";"), RU(3).rstrip(";"), RU(4).rstrip(".")], [EN(2).rstrip(";"), EN(3).rstrip(";"), EN(4).rstrip(".")])),
    heading(t(UZ(5), RU(5), EN(5))),
    para(legal),
    items(legal_items),
    heading(t(UZ(7), RU(9), EN(9))), para(t(UZ(8), RU(10), EN(10))),
    heading(t(UZ(9), RU(11), EN(11))), para(t(UZ(10), RU(12), EN(12))),
    heading(t(UZ(11), RU(13), EN(13))), para(t(UZ(12), RU(14), EN(14))),
    heading(t(UZ(13), RU(15), EN(15))), para(t(UZ(14), RU(16), EN(16))),
    heading(t(UZ(15), RU(17), EN(17))),
]
for i in (0, 2, 3, 4, 5, 6):  # card 1 (the 2nd link) is the PDF the page already has
    blocks.append(document_block(media_of(hrefs[i]), cap[i]))
plan.append(entry(slug, raw, blocks, captions_of_cards(documents, [cap[1]])))
NOTES[slug] = ["uz 'Huquqiy asoslar': one sentence with PQ-4958 and '30-maydagi 304-son' became an introduction and two items like in ru/en (the decree is PF-4958, the resolution 304 is of 22 May 2017)",
               "the 7 regulations are document cards (six new, the seventh 'Ilmiy daraja berish tartibi' is the card the page already had: it stays last); ru/en captions lost the stray 'согласно' / 'according to'"]

# ================= 5. Normativ-huquqiy hujjatlar =================
slug = "ilmiy-faoliyat-boyicha-normativ-huquqiy-hujjatlar"
raw, documents, L = load(slug)
assert len(L["uz"]) == 35 and len(L["ru"]) == 36 and len(L["en"]) == 17
U = lambda i: md(L, "uz", i)
R = lambda i: md(L, "ru", i)
E = lambda i: md(L, "en", i)
ru1 = R(1)
cut = ru1.index("Также Законом предусмотрены")
ru1a, ru1b = ru1[:cut].strip(), ru1[cut:].strip()
law_href = re.search(r"\]\(([^)]+)\)", U(5)).group(1)
decree_uz_intro = "Oʻzbekiston Respublikasi Prezidentining «Oʻzbekiston Respublikasi oliy taʼlim tizimini 2030 yilgacha rivojlantirish kontseptsiyasini tasdiqlash toʻgʻrisida»gi Farmoni. Farmonga koʻra Oʻzbekiston Respublikasi oliy taʼlim tizimini 2030 yilgacha rivojlantirish kontseptsiyasi tasdiqlandi, unda quyidagilar nazarda tutilgan:"
decree_uz = ["davlat-xususiy sheriklikni rivojlantirish, hududlarda davlat va nodavlat oliy taʼlim muassasalari faoliyatini tashkil etish, sohada sogʻlom raqobat muhitini yaratish orqali oliy taʼlim bilan qamrov darajasini 50 foizdan oshirish",
             "Oʻzbekiston Milliy universiteti va Samarqand davlat universitetini mamlakat oliy taʼlim muassasalarining flagmanlari sifatida shakllantirish",
             "respublikadagi kamida 10 ta oliy taʼlim muassasasini xalqaro eʼtirof etilgan tashkilotlar (Quacquarelli Symonds World University Rankings, Times Higher Education yoki Academic Ranking of World Universities) reytingining birinchi 1 000 ta oʻrindagi oliy taʼlim muassasalari roʻyxatiga kiritish, oliy taʼlim muassasalarida oʻquv jarayonini bosqichma-bosqich kredit-modul tizimiga oʻtkazish",
             "oliy taʼlimning ilgʻor standartlarini joriy etish, jumladan, xalqaro tajribaga tayanib, oʻquv dasturlari nazariy bilimlarni berishga qaratilgan taʼlimdan amaliy koʻnikmalarni shakllantirishga yoʻnaltirilgan taʼlim tizimiga bosqichma-bosqich oʻtish",
             "oliy taʼlim muassasalarining akademik mustaqilligini taʼminlash",
             "oliy taʼlim muassasalarida taʼlim, fan, innovatsiyalar va ilmiy tadqiqotlar natijalarini tijoratlashtirish faoliyatining oʻzaro bogʻliqligini koʻzda tutuvchi «Universitet 3.0» konsepsiyasini bosqichma-bosqich joriy etish",
             "xorijiy investitsiyalarni keng jalb etish, pullik xizmatlar koʻlamini kengaytirish va boshqa byudjetdan tashqari mablagʻlar hisobiga oliy taʼlim muassasalarida texnoparklar, foresight-markazlar, transfer texnologiyalar markazlari, startaplar va akseleratorlar yaratish, ularni tegishli tarmoqlar, sohalar va hududlarning ijtimoiy-iqtisodiy rivojlanishini bashorat qilish va tadqiq etish boʻyicha ilmiy-amaliy muassasalar darajasiga chiqarish",
             "ijtimoiy himoyaga muhtoj aholi qatlamlari, jumladan, imkoniyati cheklangan shaxslarning oliy taʼlim bilan qamrovini ular uchun infratuzilma sharoitlarini yaxshilagan holda oshirish"]
for text in decree_uz + [decree_uz_intro]:
    uz_ok(text)
decree = t(decree_uz, [re.sub(r";$|\.$", "", R(i)) for i in range(7, 15)], [re.sub(r";$|\.$", "", E(i)) for i in range(8, 16)])
en_notes = {
    "title": "The title of the act was amended by [Resolution](https://lex.uz/docs/5085289) of the Cabinet of Ministers of the Republic of Uzbekistan No. 696 of November 6, 2020. See the text in [Uzbek](https://lex.uz/docs/3213410#5096301).",
    1: "Paragraph 1 was amended by [Resolution](https://lex.uz/docs/5085289) of the Cabinet of Ministers of the Republic of Uzbekistan No. 696 of November 6, 2020. See the text in [Uzbek](https://lex.uz/docs/3213410#5096335).",
    4: "Paragraph 4 was amended by [Resolution](https://lex.uz/docs/5085289) of the Cabinet of Ministers of the Republic of Uzbekistan No. 696 of November 6, 2020. See the text in [Uzbek](https://lex.uz/docs/3213410#5096386).",
    5: "Paragraph 5 was amended by [Resolution](https://lex.uz/docs/5085289) of the Cabinet of Ministers of the Republic of Uzbekistan No. 696 of November 6, 2020. See the text in [Uzbek](https://lex.uz/docs/3213410#5096399).",
}


def uz_note(what, note_line, previous_line):
    """The lex.uz note of a change: the words of uz line `note_line` and the link "Oldingi tahrirga qarang" of uz line `previous_line` (they were two lines)."""
    assert "Oldingi" in U(previous_line)
    return uz_ok("(%s Oʻzbekiston Respublikasi Vazirlar Mahkamasining 2020-yil 6-noyabrdagi 696-sonli [qarori](%s) tahririda — Qonun hujjatlari maʼlumotlari milliy bazasi, 07.11.2020-y., 09/20/696/1481-son) [Oldingi tahrirga qarang](%s)." % (
        what, re.search(r"\]\(([^)]+)\)", U(note_line)).group(1), re.search(r"\]\(([^)]+)\)", U(previous_line)).group(1)))


blocks = [
    heading(t(U(0), R(0), E(0))),
    para(t(uz_ok("“" + U(1)), ru1a, E(1))),
    para(t(U(2), ru1b, E(2))),
    para(t(U(3), R(2), E(3))),
    para(t(U(4), R(3), E(4))),
    document_block(media_of(law_href), t(re.search(r"\[([^\]]+)\]", U(5)).group(1), re.search(r"\[([^\]]+)\]", R(4)).group(1), re.search(r"\[([^\]]+)\]", E(5)).group(1))),
    heading(t(uz_ok(U(6).replace("2019 yil 8 oktyabrdagi", "2019-yil 8-oktyabrdagi")), R(5), E(6))),
    para(t(decree_uz_intro, R(6), E(7))),
    items(decree),
    heading(t(U(9), R(16), "On measures to further improve the postgraduate education system")),
    para(t(uz_ok("(Qaror nomi Oʻzbekiston Respublikasi Vazirlar Mahkamasining 2020-yil 6-noyabrdagi 696-sonli [qarori](%s) tahririda — Qonun hujjatlari maʼlumotlari milliy bazasi, 07.11.2020-y., 09/20/696/1481-son)." % re.search(r"\]\(([^)]+)\)", U(10)).group(1)),
           R(17), en_notes["title"])),
    para(t(U(11).rstrip(":") + ":", R(18), "In pursuance of the [Decree](https://lex.uz/docs/3119697) of the President of the Republic of Uzbekistan No. UP-4958 of February 16, 2017 “On further improving the postgraduate education system”, the Cabinet of Ministers resolves:")),
    para(t(U(12), R(19), "1. To approve:")),
    items(t([U(14).rstrip(";"), U(17).rstrip(";"), uz_ok(U(20).rstrip(".").replace("tasdiqlansin", "tasdiqlansin"))],
            [R(20).rstrip(";"), R(21).rstrip(";"), R(22).rstrip(".")],
            ["State requirements for postgraduate education according to Appendix No. 1", "Regulations on postgraduate education according to Appendix No. 2",
             "State samples of documents on postgraduate education: diplomas of Doctor of Philosophy (PhD) and Doctor of Science (DSc), and certificates of associate professor, senior researcher and professor according to Appendices No. 3–7"])),
    para(t(uz_note("1-bandning ikkinchi, uchinchi va toʻrtinchi xatboshilari", 15, 13), R(23), en_notes[1])),
    para(t(U(22), R(24), "2. The Higher Attestation Commission under the Cabinet of Ministers of the Republic of Uzbekistan, together with the interested ministries and departments, shall ensure, starting from July 1, 2017, the acceptance and consideration of attestation files and the award to applicants of the academic degrees of Doctor of Philosophy (PhD) and Doctor of Science (DSc) in accordance with the requirements approved by this resolution.")),
    para(t(U(23), R(25), "3. The Agency for Science and Technology and the Higher Attestation Commission under the Cabinet of Ministers of the Republic of Uzbekistan, together with the interested ministries and departments, shall within one month bring the regulatory legal acts adopted by them into conformity with this resolution.")),
    para(t(U(25), R(26), "4. To amend the [resolution](https://lex.uz/docs/2111826) of the Cabinet of Ministers of December 28, 2012 No. 365 “On measures to further improve the postgraduate education system and the attestation of highly qualified scientific and scientific-pedagogical personnel” (Collection of Legislation of the Republic of Uzbekistan, 2012, No. 12, Art. 90) in accordance with Appendix No. 8.")),
    para(t(uz_note("4-band", 26, 24), R(27), en_notes[4])),
    para(t(U(28), R(28), "5. Control over the implementation of this resolution shall be assigned to the Information and Analytical Department for Education and Science of the Cabinet of Ministers of the Republic of Uzbekistan.")),
    para(t(uz_note("5-band", 29, 27), R(30), en_notes[5])),
    para(t(U(30), R(31), "Prime Minister of the Republic of Uzbekistan A. ARIPOV")),
    para(t("Toshkent sh., 2017-yil 22-may, 304-son", "г. Ташкент, 22 мая 2017 г., № 304", "Tashkent, May 22, 2017, No. 304")),
    para(t(U(34), R(35), "[More details](https://lex.uz/docs/-3213410?otherlang=1)")),
]
card = captions_of_cards(documents, [t("Oʻzbekiston Respublikasi Prezidentining 2019-yil 8-oktyabrdagi PF-5847-son Farmoni", "Указ Президента Республики Узбекистан от 8 октября 2019 года № УП-5847",
                                       "Decree of the President of the Republic of Uzbekistan dated October 8, 2019 No. DP-5847")])
plan.append(entry(slug, raw, blocks, card))
NOTES[slug] = ["en had no text at all for the Cabinet resolution No. 304 of 22 May 2017 (half of the page): translated from the Russian text; uz decree paragraph was a short summary: replaced by a full translation of the ru/en list (8 items)",
               "lex.uz editor notes: the five 'Oldingi tahrirga qarang' lines of uz were joined with the notes of the changes (one note per point as in ru); ru-only label 'Комментарий LexUz' dropped",
               "the Decree PF-5847 PDF is the card the page already had (it stays last, with a caption); the Law PDF is a new card after the law text"]

for e in plan:
    e["notes"] = NOTES[e["slug"]]
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"], len(e["blocks"])) for e in plan])
