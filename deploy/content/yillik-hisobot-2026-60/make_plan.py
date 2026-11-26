"""Builds plan.json of script 60 (Faoliyat > Doktorantura: three pages) from the live pages: Monografiya (a cover and four PDFs), Malakaviy imtihonlar (twelve exam programmes as PDF links),
Doktorantura maʻlumotlari (admission information: numbers, programmes, requirements, documents, regulations). Uzbek is the base; the old English text of the third page was a broken
machine translation with other lists (rewritten here after the Uzbek and Russian text); Uzbek spelling fixed (h/x, mahkamasi, tibbiyot, funksional). Uzbek text uses only U+02BB.
What we wrote: tarjima-kerak.md.
    python deploy/content/yillik-hisobot-2026-60/make_plan.py"""
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


def card(media, caption):
    return block("document", {lang: {"media": media, "caption": caption[lang]} for lang in LANGS})


def tutuq(text):
    """Uzbek: one apostrophe U+02BB (after a vowel too: "taʻlim")."""
    return text.replace("ʼ", "ʻ")


def strip(text):
    return text.strip().rstrip(";.").strip()


plan = []

# ================= 1. Malakaviy imtihonlar (and the same programmes on Doktorantura maʻlumotlari) =================
slug = "malakaviy-imtihonlar"
raw, documents = page_blocks(slug)
assert not documents
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert all(len(L[lang]) == 12 for lang in LANGS)
CODE = re.compile(r"^\s*(\d{2}\.\d{2}\.\d{2})[\s.\-–]*(.+?)\s*$")
FIX_UZ = {"Profilaktik tibbyot": "Profilaktik tibbiyot", "funktsional": "funksional", "Taʻlim va tarbiya nazariyasi va metodikasi sohalar boʻyicha": "Taʻlim va tarbiya nazariyasi va metodikasi (sohalar boʻyicha)"}
FIX_RU = {"Образование и теория и методология образования по областям": "Теория и методика обучения и воспитания (по областям)"}
FIX_EN = {"Education and theory and methodology of education by region": "Theory and methodology of education and upbringing (by field)"}
programs = []
for i in range(12):
    parts = {}
    for lang, fix in (("uz", FIX_UZ), ("ru", FIX_RU), ("en", FIX_EN)):
        m = CODE.match(L[lang][i]["text"])
        assert m, L[lang][i]["text"]
        name = m.group(2)
        for a, b in fix.items():
            name = name.replace(a, b)
        parts[lang] = (m.group(1), name)
    assert len({parts[lang][0] for lang in LANGS}) == 1
    href = L["uz"][i]["links"][0][0]
    assert L["en"][i]["links"][0][0] == href and (L["ru"][i]["links"][0][0] == href or i == 10)  # the Russian link of 14.00.43 was a broken address
    programs.append(("%s — %s" % (parts["uz"][0], parts["uz"][1]), "%s — %s" % (parts["ru"][0], parts["ru"][1]), "%s — %s" % (parts["en"][0], parts["en"][1]), media_of(href)))
program_cards = lambda: [card(m, t(tutuq(u), r, e)) for u, r, e, m in programs]
entry_ = entry(slug, raw, program_cards())
entry_["notes"] = ["the twelve links are document cards ('code — name' in three languages); uz typos: 'Profilaktik tibbyot', 'funktsional'; the 13.00.02 name is written again in all three languages (ru was 'Образование и теория и методология образования по областям'); the Russian link of 14.00.43 was a broken address (the Uzbek file is used)"]
plan.append(entry_)

# ================= 2. Monografiya =================
slug = "monografiya"
raw, documents = page_blocks(slug)
assert not documents
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
cover = images_of(raw["data"]["uz"]["html"])
assert len(cover) == 1 and all(len(L[lang]) == 4 for lang in LANGS) and all(images_of(raw["data"][lang]["html"]) == cover for lang in LANGS)
hrefs = [L["uz"][i]["links"][0][0] for i in range(4)]
blocks = [
    image_block(cover[0], t("«Tibbiyot oliy taʻlim muassasalarida fundamental fanlarni integral tizimida oʻqitishning asosiy motivlari» monografiyasining muqovasi (M. T. Rasulov, 2025)",
                            "Обложка монографии «Основные мотивы преподавания фундаментальных дисциплин в интегральной системе в медицинских вузах» (М. Т. Расулов, 2025)",
                            "Cover of the monograph “The main motives for teaching fundamental sciences in an integral system at medical higher education institutions” (M. T. Rasulov, 2025)")),
    card(media_of(hrefs[0]), t("Tibbiyot oliy taʻlim muassasalarida fundamental fanlarni integral tizimida oʻqitishning asosiy motivlari (M. T. Rasulov, 2025)",
                                "Основные мотивы преподавания фундаментальных дисциплин в интегральной системе в медицинских вузах (М. Т. Расулов, 2025)",
                                "The main motives for teaching fundamental sciences in an integral system at medical higher education institutions (M. T. Rasulov, 2025)")),
    card(media_of(hrefs[1]), t("Hazm tizimi fiziologiyasi (rus tilida)", "Физиология пищеварительной системы", "Physiology of the digestive system (in Russian)")),
    card(media_of(hrefs[2]), t("Ayirish va endokrin tizimlar fiziologiyasi (rus tilida)", "Физиология выделительной и эндокринной системы", "Physiology of the excretory and endocrine systems (in Russian)")),
    card(media_of(hrefs[3]), t("Normal fiziologiya (rus tilida)", "Нормальная физиология", "Normal physiology (in Russian)")),
]
entry_ = entry(slug, raw, [b for b in blocks])
entry_["notes"] = ["the cover is an image block; the four PDF links are cards; the three monographs on physiology are in Russian (their Russian titles were the link texts in all three languages): the captions in uz and en say '(in Russian)', the ru/en captions of the 2025 monograph were the Uzbek title with wrong apostrophes: translated by us"]
plan.append(entry_)

# ================= 3. Doktorantura maʻlumotlari =================
slug = "doktorantura-malumotlari"
raw, documents = page_blocks(slug)
assert len(documents) == 1
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert [len(L[lang]) for lang in LANGS] == [45, 53, 51], [len(L[lang]) for lang in LANGS]
U = lambda i: tutuq(L["uz"][i]["text"].replace("Maxkamasining", "Mahkamasining").replace("mutaxasislik", "mutaxassislik").replace(" - ", " — ").replace(",yoki", ", yoki"))
R = lambda i: L["ru"][i]["text"]
E = lambda i: L["en"][i]["text"]
blocks = [
    para(t(U(0), R(0).replace("самостоятельного поиска - 24", "самостоятельного соискательства — 24"), "The institute has 40 basic doctoral students and 255 independent researchers. The number of specialties of basic doctoral studies (PhD), doctoral studies (DSc) and independent research is 24.")),
    heading(t(U(1).rstrip(":"), R(1).rstrip(":").replace("по приему в институт базовой докторантуры Ферганского медицинского института общественного здоровья на 2025 год", "для приёма в базовую докторантуру Ферганского медицинского института общественного здоровья на 2025 год"),
              "Examination programmes for admission to basic doctoral studies at the Fergana Medical Institute of Public Health for 2025")),
]
blocks += program_cards()
blocks += [
    heading(t(U(14), R(14), E(14))),
    para(t(U(15), R(15), E(15))),
    para(t(U(16), "Отбор поступающих в базовую докторантуру осуществляется по результатам вступительных экзаменов, а в докторантуру — по результатам собеседования.", E(16))),
    para(t(U(17), R(19), "Registration for independent research is based on the results of an interview.")),
    heading(t("Falsafa doktori (PhD) uchun talablar", R(20), "Requirements for applicants to basic doctoral studies or independent researchers for the PhD degree"), 3),
    para(t(U(18), R(21), E(18))),
    items(t([strip(U(19)), strip(U(20))],
            [strip(R(22)), "иметь определённые научные результаты, которые могут составить основу диссертационного исследования на соискание степени PhD, в том числе не менее одной научной статьи, опубликованной в научных журналах и изданиях, и не менее двух тезисов, опубликованных в сборниках научных работ по соответствующим научным направлениям, а также представленных на научно-практических конференциях и семинарах"],
            ["hold a master’s degree or a clinical residency diploma (for medical sciences), or a diploma of higher education (for specialist programmes)",
             "have certain scientific results that may form the basis of dissertation research for the PhD degree, including at least one scientific article published in scientific journals and publications and at least two theses in scientific-practical conferences, seminars and collections of scientific papers in the relevant fields"])),
    para(t(U(21), R(26).rstrip(".") + ".", E(21))),
    heading(t("Tayanch doktoranturaga kirish uchun hujjatlar", R(27), "Documents for admission to basic doctoral studies"), 3),
    para(t(U(22), R(28), E(22))),
    items(t([strip(U(i)) for i in range(23, 28)], [strip(R(i)) for i in range(29, 34)],
            ["brief biographical information (CV)",
             "a copy of the master’s diploma of a higher education institution or of a diploma of higher education (for specialist programmes) (not required if integrated in the system)",
             "copies of published scientific works, with links (at least 1 scientific article and 2 theses)",
             "a copy of the document on the State Scholarship of the President of the Republic of Uzbekistan (if any)",
             "certificates of recognised foreign-language proficiency at the required level"])),
    heading(t("Doktoranturaga kirish uchun hujjatlar", R(34), "Documents for admission to doctoral studies"), 3),
    para(t(U(28).rstrip(":") + ":", R(35), E(33))),
    items(t([strip(U(i)) for i in range(29, 34)], [strip(R(i)) for i in range(36, 41)],
            ["brief biographical information (CV)", "certificates of recognised foreign-language proficiency at the required level",
             "a copy of a diploma of higher education, or a diploma of Candidate of Sciences / Doctor of Philosophy (PhD), or an equivalent academic degree obtained abroad",
             "a scientific report on the research topic and a detailed draft plan of the doctoral dissertation prepared for the degree of Doctor of Science (DSc)",
             "a list of published scientific works, with their copies and links (at least 3 scientific articles and 2 theses)"])),
    heading(t("Mustaqil izlanuvchilikka rasmiylashtirish uchun hujjatlar", R(41), "Documents for registration as an independent researcher"), 3),
    para(t(U(34), R(42), E(40))),
    items(t([strip(U(i)) for i in range(35, 40)], [strip(R(i)) for i in range(43, 48)],
            ["brief biographical information", "for registration for the PhD degree: a copy of the master’s diploma or the clinical residency diploma (for medical sciences) or of the diploma of higher education (for specialist programmes)",
             "a list of scientific works and their copies",
             "for registration for the DSc degree: a copy of the diploma of Candidate of Sciences or Doctor of Philosophy (PhD), or of another equivalent academic degree obtained abroad",
             "a reference from the place of work"])),
    heading(t(U(40), R(48), "Doctoral regulations")),
]
ru_hrefs = [L["ru"][i]["links"][0][0] for i in range(49, 53)]
uz_hrefs = [L["uz"][i]["links"][0][0] for i in range(41, 45)]
assert uz_hrefs[1:] == ru_hrefs[1:] and "304" in ru_hrefs[0]
cap_regs = [t("Oʻzbekiston Respublikasi Vazirlar Mahkamasining 304-son qarori", "Постановление Кабинета Министров Республики Узбекистан № 304", "Resolution of the Cabinet of Ministers of the Republic of Uzbekistan No. 304"),
            t("Oʻzbekiston Respublikasi Vazirlar Mahkamasining 937-son qarori", "Постановление Кабинета Министров Республики Узбекистан № 937", "Resolution of the Cabinet of Ministers of the Republic of Uzbekistan No. 937"),
            t("Oʻzbekiston Respublikasi Vazirlar Mahkamasining 606-son qarori", "Постановление Кабинета Министров Республики Узбекистан № 606", "Resolution of the Cabinet of Ministers of the Republic of Uzbekistan No. 606")]
for k in range(3):
    blocks.append(card(media_of(ru_hrefs[k]), cap_regs[k]))
doktorantlar = t("Doktorantlar maktabi. Nizom. 572 (26.06.2019)", "Докторантская школа. Положение. 572 (26.06.2019)", "School of Doctoral Students. Regulation. 572 (26.06.2019)")
entry_ = entry(slug, raw, blocks, captions_of_cards(documents, [doktorantlar]))
entry_["notes"] = ["uz was the base; the old English text had other lists (application, employment history...) and a block about DSc requirements that is neither in uz nor in ru: the English lists are written again after the Uzbek and Russian lists (listed in tarjima-kerak.md), the extra DSc paragraph is dropped",
                   "the twelve exam programmes are the same twelve PDFs as on 'Malakaviy imtihonlar' (copied again as cards); the four regulations are cards: the Cabinet resolution 304 pointed at tsuull.uz in uz and at the site's own file in ru: the site's file is used in all languages; the card the page already had (Doktorantlar maktabi, 572) stays last"]
plan.append(entry_)

for item in plan:
    for b in item["blocks"]:
        d = b["data"]["uz"]
        text = " ".join([d.get("text", ""), d.get("caption", ""), d.get("alt", "")] + d.get("items", []))
        assert not re.search(r"['‘’`´ʼ]", text), text
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"][:25], len(e["blocks"])) for e in plan])
