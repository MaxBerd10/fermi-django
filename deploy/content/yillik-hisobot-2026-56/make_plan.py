"""Builds plan.json of script 56 (Faoliyat > Moliyaviy faoliyat: eight pages) from the live pages.
Four pages are old HTML (links to PDFs and one sentence): the links become document cards, the sentence a paragraph; the other four are one PDF each (the card gets a caption in three
languages; the old caption of the currency page was a Russian file name in all three languages). What we wrote or corrected is listed in tarjima-kerak.md.
    python deploy/content/yillik-hisobot-2026-56/make_plan.py"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _plan_tools import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))


def t(uz, ru, en):
    return {"uz": uz, "ru": ru, "en": en}


def para(text):
    return block("paragraph", {lang: {"text": text[lang]} for lang in LANGS})


def href_of(lines, lang, i, n=0):
    return lines[lang][i]["links"][n][0]


plan = []
NOTES = {}


def caption_only(slug, caption, recaption=False):
    page = fetch("https://fermi.uz/api/v1/pages/%s/" % slug)["blocks"]
    documents = [b for b in page if b["block_type"] == "document"]
    assert len(documents) == 1 and len(page) == 1, slug
    result = {"slug": slug, "existing_documents": captions_of_cards(documents, [caption]), "notes": []}
    if recaption:
        result["recaption"] = True
    plan.append(result)
    return result


# ---------- 1. Byudjet smetasi ----------
slug = "byudjet-smetasi"
raw, documents = page_blocks(slug)
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert len(L["uz"]) == 4 and len(L["ru"]) == 3 and len(L["en"]) == 3
hrefs = [href_of(L, "uz", i) for i in range(4)]
assert hrefs[0].endswith(".xlsx") and hrefs[3] == hrefs[2].replace("qo%E2%80%98shma", "Byudjet") and hrefs[3].endswith("Smeta%20Byudjet.pdf")  # the 4th link is the PDF the page already has as a card
assert href_of(L, "ru", 0) == hrefs[3] and href_of(L, "ru", 1) == hrefs[1] and href_of(L, "ru", 2) == hrefs[2]
blocks = [
    document_block(media_of(hrefs[0]), t("Byudjet smetasi (Excel)", "Смета бюджета (Excel)", "Budget estimate (Excel)")),
    document_block(media_of(hrefs[1]), t("Kontrakt smetasi", "Смета контракта", "Contract estimate")),
    document_block(media_of(hrefs[2]), t("Qoʻshma smeta", "Совместная смета", "Joint estimate")),
]
entry_ = entry(slug, raw, blocks, captions_of_cards(documents, [t("Byudjet smetasi, 2-chorak", "Смета бюджета, 2-й квартал", "Budget estimate, 2nd quarter")]))
entry_["notes"] = ["the lines 'Yuklab olish uchun bosing>>>>>>' are gone (a card has its own download button); the Excel file exists only in the Uzbek text: its ru/en captions are ours; the 4th link (Byudjet smetasi, 2 chorak) is the PDF card the page already had: it stays last"]
plan.append(entry_)

# ---------- 2. Mansabdor shaxslarning xizmat safarlari ----------
slug = "mansabdor-shaxslarning-xizmat-safarlari-va-xorijdan-tashrif-buyurgan-mehmonlarni-kutib-olish-xarajatlari-togrisidagi-malumotlar"
raw, documents = page_blocks(slug)
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert len(L["uz"]) == 0 and [x["text"] for x in L["ru"]] == ["Командировочные расходы"] and [x["text"] for x in L["en"]] == ["Business travel expenses"]
entry_ = entry(slug, raw, [], captions_of_cards(documents, [t("Xizmat safarlari xarajatlari", "Командировочные расходы", "Business travel expenses")]))
entry_["notes"] = ["the old text was only the name of the PDF (nothing in Uzbek, a link in Russian): it becomes the caption of the card and the HTML block is removed"]
plan.append(entry_)

# ---------- 3. Xarid qilinishi rejalashtirilgan tovarlar ----------
slug = "xarid-qilinishi-rejalashtirilgan-tovarlar-ishlar-xizmatlar-togrisida-malumotlar"
raw, documents = page_blocks(slug)
assert not documents
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert all(len(L[lang]) == 1 and len(L[lang][0]["links"]) == 1 for lang in LANGS) and L["uz"][0]["links"][0][0] == L["ru"][0]["links"][0][0] == L["en"][0]["links"][0][0]
title = t("Xarid qilinishi rejalashtirilgan tovarlar (ishlar, xizmatlar) toʻgʻrisida maʻlumotlar", "Информация о товарах (работах, услугах), которые планируется приобрести",
          "Information on the goods (works, services) planned to be purchased")
entry_ = entry(slug, raw, [document_block(media_of(L["uz"][0]["links"][0][0]), title)])
entry_["notes"] = ["the link is now a document card; typos corrected in the title: uz 'toʻgrisida', ru 'услкгах' and 'коротые'"]
plan.append(entry_)

# ---------- 4. Davlat xaridlari va investitsiya loyihalari ----------
slug = "davlat-xaridlari-va-investitsiya-loyihalari-doirasida-tashkil-etiladigan-xarid-komissiyalarining-tarkibi-togrisidagi-malumotlar"
raw, documents = page_blocks(slug)
assert not documents
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert all(len(L[lang]) == 1 for lang in LANGS) and "apreI" in L["uz"][0]["text"]
text = t("Oʻzbekiston Respublikasining 2021-yil 22-apreldagi 684-son Qonuni ijrosini taʻminlash va Fargʻona jamoat salomatligi tibbiyot instituti rektorining 2022-yil 20-yanvardagi «Xarid komissiyasi tarkibini tuzish toʻgʻrisida»gi 38-sonli buyrugʻiga muvofiq Xarid komissiyasi tarkibiga oʻzgartirish kiritish maqsadida",
         "В целях обеспечения исполнения Закона Республики Узбекистан от 22 апреля 2021 года № 684 и приказа ректора Ферганского медицинского института общественного здоровья от 20 января 2022 года № 38 «О составе Закупочной комиссии» — с целью внесения изменений в состав закупочной комиссии",
         "In order to ensure the implementation of Law No. 684 of the Republic of Uzbekistan dated April 22, 2021 and Order No. 38 of the Rector of the Fergana Medical Institute of Public Health dated January 20, 2022 “On the composition of the Procurement Commission”, and to amend the composition of the procurement commission")
entry_ = entry(slug, raw, [para(text)])
entry_["notes"] = ["the old page is ONE unfinished sentence ('... maqsadida'): nothing follows it (no names, no file): kept as it is, typos corrected (22-apreI -> 22-aprel, Ns -> №, toʻgʻirisida, 'o’ zgartirish'); the staff must add the composition of the commission"]
plan.append(entry_)

# ---------- 5. One PDF each: captions ----------
caption_only("kontrakt-xisob-raqam-smetasi", t("Kontrakt hisob raqami smetasi", "Смета контрактного счёта", "Contract account estimate"))
caption_only("valyuta-xisob-raqam-smetasi", t("Valyuta hisob raqami smetasi", "Смета валютного счёта", "Foreign currency account estimate"), recaption=True)
caption_only("kvartal-boyicha-tushumlar-va-xarajatlar", t("Kvartal boʻyicha tushumlar va xarajatlar", "Доходы и расходы за квартал", "Revenues and expenses for the quarter"))
caption_only("davlat-organlari-va-tashkilotlari-tasarrufidagi-xizmat-avtomototransport-vositalari-xizmat-uylari-va-boshqa-kochmas-mulklar-togrisidagi-malumotlar",
             t("Davlat organlari va tashkilotlari tasarrufidagi xizmat avtomototransport vositalari, xizmat uylari va boshqa koʻchmas mulklar toʻgʻrisidagi maʻlumotlar",
               "Сведения о служебных автомобилях, служебных домах и другом недвижимом имуществе государственных органов и организаций",
               "Information on service vehicles, service houses and other real estate of government agencies and organizations"))
for item in plan[-4:]:
    item["notes"] = ["only the caption of the PDF card is set (the old one had none)" if not item.get("recaption") else "the old caption was a Russian file name ('иностранной валюты') in all three languages: replaced"]

for item in plan:
    for text_ in [b["data"]["uz"].get("text", "") for b in item.get("blocks", [])] + [item["existing_documents"][0]["caption"]["uz"] if item.get("existing_documents") else ""]:
        assert not re.search(r"['‘’`´]", text_), text_
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"][:30], len(e.get("blocks", [])) if "blocks" in e else "captions") for e in plan])
