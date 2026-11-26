"""Builds plan.json of script 59 (Faoliyat > Korrupsiyaga qarshi kurashish faoliyati: six pages) from the live pages:
Korrupsiyaga qarshi kurashish tadbirlari (pictures and two news items), Tavsiyaviy qoʻllanma (four paragraphs), Davlat dasturlari (a quotation card, pictures and one PDF),
SSV korrupsiyaga qarshi kurashish siyosati (an order and its 19 annexes as links), and two pages that are one PDF card each (captions). What we wrote: tarjima-kerak.md.
    python deploy/content/yillik-hisobot-2026-59/make_plan.py"""
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


def para(text, quote=False):
    return block("paragraph", {lang: ({"text": text[lang], "quote": True} if quote else {"text": text[lang]}) for lang in LANGS})


def dates(text):
    """"2019 yil 27 maydagi" -> "2019-yil 27-maydagi"; "2019-2020 yillarda" -> "2019–2020-yillarda"."""
    text = re.sub(r"(\d{4}) yil (\d{1,2}) (\w+dagi)", r"\1-yil \2-\3", text)
    text = re.sub(r"(\d{4})-(\d{4}) yillarda", r"\1–\2-yillarda", text)
    return re.sub(r"(\d)- bandiga", r"\1-bandiga", text)


plan = []
IMG = "migrated/img/"

# ================= 1. Korrupsiyaga qarshi kurashish tadbirlari =================
slug = "korrupsiyaga-qarshi-kurashish-tadbirlari"
raw, documents = page_blocks(slug)
assert not documents
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert all(len(L[lang]) == 3 for lang in LANGS)
pics = images_of(raw["data"]["uz"]["html"])
assert len(pics) == 5 and all(images_of(raw["data"][lang]["html"]) == pics for lang in LANGS)
alts = [t("«Biz korrupsiyaga qarshimiz» targʻibot banneri", "Агитационный баннер «Мы против коррупции»", "“We are against corruption” campaign banner"),
        t("«Korrupsiya — taraqqiyot kushandasi» tadbiri", "Мероприятие «Коррупция — враг прогресса»", "The event “Corruption is the enemy of progress”"),
        t("Tadbirlardan fotolavhalar", "Фотографии с мероприятий", "Photographs from the events"),
        t("Talabalar yakuniy imtihonlarni topshirmoqda", "Студенты сдают итоговые экзамены", "Students are taking final examinations"),
        t("«Stop korrupsiya» chellenji", "Челлендж «Стоп коррупция»", "The “Stop corruption” challenge")]
blocks = [image_block(pics[i], alts[i]) for i in range(4)]
blocks += [
    heading(t(L["uz"][0]["text"].rstrip("."), L["ru"][0]["text"].rstrip("."), L["en"][0]["text"].rstrip("."))),
    para(t(L["uz"][1]["text"].replace("S.Isaqov", "S. Isaqov").replace("bosqichma bosqich", "bosqichma-bosqich"), L["ru"][1]["text"], L["en"][1]["text"])),
    image_block(pics[4], alts[4]),
    para(t("Fargʻona jamoat salomatligi tibbiyot institutida “Stop korrupsiya” chellenji davom etmoqda.", L["ru"][2]["text"], L["en"][2]["text"])),
]
entry_ = entry(slug, raw, blocks)
entry_["notes"] = ["the picture blocks are in the order of the old page (four pictures, the news about the final examinations, the fifth picture with its sentence); picture descriptions (alt texts) are ours; the uz title 'stop korrupsiya chellenji' got its quotation marks"]
plan.append(entry_)

# ================= 2. Tavsiyaviy qollanma =================
slug = "tavsiyaviy-qollanma"
raw, documents = page_blocks(slug)
assert not documents
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert all(len(L[lang]) == 4 for lang in LANGS)
RU = [
    "Настоящее рекомендательное пособие разработано на основе Закона Республики Узбекистан «О противодействии коррупции» от 3 января 2017 года и Государственной программы по противодействию коррупции на 2019–2020 годы, утверждённой Указом Президента Республики Узбекистан от 27 мая 2019 года № УП-5729, и направлено на закрепление ответственными работниками государственных органов и организаций — после приёма на работу, а также по истечении определённого времени — знаний и навыков по соблюдению правил профессиональной этики, устранению конфликта интересов и другим направлениям противодействия коррупции.",
    "Указом Президента Республики Узбекистан от 3 октября 2019 года № УП-5843 «О мерах по коренному совершенствованию кадровой политики и системы государственной гражданской службы в Республике Узбекистан» образовано Агентство по развитию государственной службы при Президенте Республики Узбекистан.",
    L["ru"][2]["text"],
    "Вместе с тем, согласно пункту 7 «Плана мер по повышению правового сознания и правовой культуры населения в целях противодействия коррупции, формированию в обществе нетерпимого отношения к коррупции», утверждённого председателем Республиканской межведомственной комиссии по противодействию коррупции 31 июля 2019 года, предусмотрена разработка рекомендательного пособия по вопросам разъяснительной работы в сфере противодействия коррупции.",
]
EN = [
    "This recommendation manual is based on the Law of the Republic of Uzbekistan “On Combating Corruption” of January 3, 2017 and the State Anti-Corruption Program for 2019–2020 approved by Decree of the President of the Republic of Uzbekistan No. PD-5729 of May 27, 2019. It is intended to strengthen the knowledge and skills of responsible employees of state bodies and organizations — after they are hired and after a certain period of time — in compliance with the rules of professional ethics, elimination of conflicts of interest and other areas of combating corruption.",
    "By Decree of the President of the Republic of Uzbekistan No. PD-5843 of October 3, 2019 “On measures to radically improve the personnel policy and the system of state civil service in the Republic of Uzbekistan”, the Agency for the Development of Public Service under the President of the Republic of Uzbekistan was established.",
    L["en"][2]["text"],
    "In addition, according to paragraph 7 of the “Plan of measures to increase the legal awareness and legal culture of the population in order to combat corruption and to form an intolerant attitude towards corruption in society”, approved by the chairman of the Republican Interdepartmental Commission on Combating Corruption on July 31, 2019, the development of a recommendation manual on explanatory work in the field of combating corruption is envisaged.",
]
blocks = [para(t(dates(L["uz"][i]["text"]), RU[i], EN[i])) for i in range(4)]
entry_ = entry(slug, raw, blocks)
entry_["notes"] = ["ru and en: the first and the last paragraph were broken machine translations (a sentence without a main verb, a sentence that ended with 'the Republic of Uzbekistan'): written again after the Uzbek text; 'PF-5729-son' became '№ УП-5729' / 'No. PD-5729'; uz dates written as 2019-yil 27-maydagi"]
plan.append(entry_)

# ================= 3. Davlat dasturlari =================
slug = "korrupsiyaga-qarshi-kurashish-davlat-dasturlari"
raw, documents = page_blocks(slug)
assert not documents
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
pics = images_of(raw["data"]["uz"]["html"])
assert len(pics) == 3 and len(L["uz"]) == 4 and len(L["ru"]) == 2 and len(L["en"]) == 2
href = L["uz"][2]["links"][0][0]
assert href == L["uz"][3]["links"][0][0] and href.endswith("Topshiriqlar.pdf")
blocks = [
    para(t(L["uz"][0]["text"].rstrip(".") + ". — Sh. Mirziyoyev", L["ru"][0]["text"].replace(" - ", " — ").rstrip(".") + ". — Ш. Мирзиёев", L["en"][0]["text"].rstrip(".") + ". — Sh. Mirziyoyev"), quote=True),
    image_block(pics[0], t("Shavkat Mirziyoyev: «Korrupsiyaga qarshi kurash — umummilliy vazifa»", "Шавкат Мирзиёев: «Борьба с коррупцией — общенациональная задача»", "Shavkat Mirziyoyev: “The fight against corruption is a nationwide task”")),
    image_block(pics[1], t("«Stop korrupsiya»: korrupsiyaga qarshi kurashish «Komplayens-nazorat» tizimini boshqarish", "«Стоп коррупция»: управление системой «Комплаенс-контроль» по борьбе с коррупцией", "“Stop corruption”: management of the “Compliance Control” anti-corruption system")),
    document_block(media_of(href), t("Oʻzbekiston Respublikasi Prezidenti Sh. M. Mirziyoyev tomonidan Korrupsiyaga qarshi kurashish boʻyicha milliy kengash yigʻilishida Oliy taʼlim, fan va innovatsiyalar vazirligiga belgilab berilgan topshiriqlar",
                                     "Поручения, данные Президентом Республики Узбекистан Ш. М. Мирзиёевым Министерству высшего образования, науки и инноваций на заседании Национального совета по противодействию коррупции",
                                     "Tasks assigned to the Ministry of Higher Education, Science and Innovation by President Sh. M. Mirziyoyev at the meeting of the National Council on Combating Corruption")),
    image_block(pics[2], t("Korrupsiyaga qarshi kurashish davlat dasturi: infografika", "Государственная программа по противодействию коррупции: инфографика", "State anti-corruption program: infographic")),
]
entry_ = entry(slug, raw, blocks)
entry_["notes"] = ["the quotation and the line 'Sh.Mirziyoyev.' became one quotation paragraph; the PDF 'Topshiriqlar' (two links in uz, none in ru/en) is one document card (the same PDF in all languages, captions ours); picture descriptions are ours"]
plan.append(entry_)

# ================= 4. SSV korrupsiyaga qarshi kurashish siyosati =================
slug = "ssv-korrupsiyaga-qarshi-kurashish-siyosati"
raw, documents = page_blocks(slug)
assert not documents
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert all(len(L[lang]) == 20 for lang in LANGS)
pics = images_of(raw["data"]["uz"]["html"])
assert len(pics) == 1 and pics[0].endswith("Sh.Mirziyoyev.jpg")
order_href = L["uz"][0]["links"][0][0]
annexes = []
for i in range(1, 20):
    links = [h for h, _ in L["uz"][i]["links"]]
    own = links[0] if len(links) == 1 else links[-2]  # "[11.](11.1)[2](11.2)[-ilova](1-ilova)": the number is in the link before the last
    number = re.search(r"/([\d.]+)-%D0%B8", own).group(1)
    annexes.append((number, own))
assert [n for n, _ in annexes] == ["1", "2", "3", "4", "5", "6", "7", "8", "8.1", "9", "10", "11", "11.1", "11.2", "11.3", "11.4", "12", "13", "14"], [n for n, _ in annexes]
blocks = [
    document_block(media_of(order_href), t(L["uz"][0]["text"], L["ru"][0]["text"], L["en"][0]["text"])),
    image_block(pics[0], t("Shavkat Mirziyoyev: «Korrupsiyaga qarshi kurash — umummilliy vazifa»", "Шавкат Мирзиёев: «Борьба с коррупцией — общенациональная задача»", "Shavkat Mirziyoyev: “The fight against corruption is a nationwide task”")),
    heading(t("Ilovalar", "Приложения", "Annexes")),
]
blocks += [document_block(media_of(href_), t("%s-ilova" % n, "Приложение %s" % n, "Annex %s" % n)) for n, href_ in annexes]
entry_ = entry(slug, raw, blocks)
entry_["notes"] = ["the order and its 19 annexes (1, 2, ... 8.1, ... 11.4, ... 14) are 20 document cards; the number of each annex is read from the file it opens (the old links were cut into pieces); captions 'N-ilova' / 'Приложение N' / 'Annex N' are ours (the titles of the annexes are not on the page)"]
plan.append(entry_)

# ================= 5. Two pages with one PDF =================
def caption_only(slug, caption):
    page = fetch("https://fermi.uz/api/v1/pages/%s/" % slug)["blocks"]
    documents = [b for b in page if b["block_type"] == "document"]
    assert len(documents) == 1 and len(page) == 1, slug
    plan.append({"slug": slug, "existing_documents": captions_of_cards(documents, [caption]), "recaption": True,
                 "notes": ["only the caption of the PDF card is set (the old caption was the file name, with wrong apostrophes in ru and en)"]})


caption_only("uslubiy-qollanma-va-tavsiyalar", t("Uslubiy qoʻllanmalar va tavsiyalar", "Методические пособия и рекомендации", "Methodological manuals and recommendations"))
caption_only("korrupsiyaga-qarshi-ichki-nazorat-komplayens-tizimini-joriy-etish-boyicha-qollanma",
             t("Korrupsiyaga qarshi ichki nazorat (Komplayens) tizimini joriy etish boʻyicha qoʻllanma", "Руководство по внедрению системы антикоррупционного внутреннего контроля (комплаенс)", "Guide to implementing the anti-corruption internal control (compliance) system"))

for item in plan:
    texts = [b["data"]["uz"].get("text", "") + b["data"]["uz"].get("caption", "") + b["data"]["uz"].get("alt", "") for b in item.get("blocks", [])] + [c["caption"]["uz"] for c in item.get("existing_documents", [])]
    for text in texts:
        assert not re.search(r"['‘’`´]", text), text
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"][:25], len(e.get("blocks", [])) if "blocks" in e else "captions") for e in plan])
