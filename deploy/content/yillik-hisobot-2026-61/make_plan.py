"""Builds plan.json of script 61: the pages of Tuzilma, Abiturient, Talabalar, Xorijiy-talabalar, Kongress, Interaktiv xizmatlar and Yashil Universitet whose old HTML says the same thing in
the three languages block by block (the generic converter deploy/content/_auto_plan.py reads headings, paragraphs, lists, tables, pictures, links to files and frames; a line that is one link
to a file becomes a document card; consecutive "1. ..." / "-" lines become a list; lines in CAPITALS become headings in normal case; Uzbek apostrophes become U+02BB). Pages whose three
languages differ in structure are NOT here (they are written by hand in the next scripts). What we corrected by hand after the converter: OVERRIDES below. Review notes: tarjima-kerak.md.
    .venv/bin/python deploy/content/yillik-hisobot-2026-61/make_plan.py"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _auto_pages import build  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SLUGS = [
 "17-goals-of-un-policies",
 "abiturientlar-uchun-eslatma-2025",
 "abituriyentlar-uchun-talim-yonalishlari-va-institut-tarixi",
 "axborot-resurs-markazi",
 "buvayda-abu-ali-ibn-sino-nomidagi-jamoat-salomatligi-texnikumi",
 "dak-savollari",
 "devonxona-bolimi",
 "doktorantura-mandat-2025",
 "ekofaol-yoshlar-loyihasi",
 "ekofaol-yoshlar-loyihasi-navbatdagi-bosqich",
 "horijiy-fuqarolar-uchun-hujjatlarni-topshirish-tartibi",
 "horijiy-talabalar-ishtirokidagi-tadbirlar",
 "ilmiy-tadqiqotlar-innovatsiyalar-va-ilmiy-pedagog-kadrlar-tayyorlash-bolimi",
 "imtihon-fanlar-royxati",
 "internatura-mandat-2025",
 "internatura-qabul-komissiyasi-2025",
 "internaturaga-hujjat-topshirish-2025",
 "iqtidorli-talabalar",
 "iqtidorli-talabalarning-ilmiy-tadqiqot-faoliyatini-tashkil-etish-bolimi",
 "jismoniy-va-yuridik-shaxslarning-murojaatlari-bilan-ishlash-nazorat-va-monitoring-bolimi",
 "klinik-fikrlashga-doir-video-darslar",
 "kontrakt-miqdori-2025",
 "kop-berilayotgan-savollar",
 "magistrantlar-uchun-yoriqnoma",
 "magistratura-baholash-mezonlari",
 "magistratura-bolimi",
 "magistratura-online-royxatdan-otish-2025",
 "magistratura-qabul-komissiyasi-joylashgan-orni",
 "magistratura-qabul-kvotasi-2025",
 "markaz-xaqida",
 "marketing-va-talabalar-amaliyoti-bolimi",
 "matbuot-kotibi",
 "olimpiada-sertifikatlari",
 "oqishni-kochirish-natijalari-2024",
 "oqishni-kochirish-qayta-tiklash",
 "oquv-uslubiy-boshqarma",
 "ordinatura-imtihonga-kirish-ruxsatnomasi-2025",
 "ordinatura-test-sinovi-manzillari-2025",
 "qabul-komissiyasi-qoshma-talim-2025",
 "qabul-nizomi-2",
 "quva-abu-ali-ibn-sino-nomidagi-jamoat-salomatligi-texnikumi",
 "quyosh-panellari",
 "reja-moliya-bolimi",
 "respublika-miqiyosidagi-yutuqlar",
 "rishton-abu-ali-ibn-sino-nomidagi-jamoat-salomatligi-texnikumi",
 "shartnomalar-namunasi-2",
 "talabalar-turar-joyi-uchun-ariza-yuborish",
 "talim-sifatini-nazorat-qilish-bolimi",
 "test-markazi-semestr-grafigi",
 "turdosh-mutaxassisliklar-royxati",
 "vakant-lavozimlar-2025",
 "xalqaro-fan-olimpiadalari",
 "xalqaro-hamkorlik-bolimi",
 "xalqaro-talabalar-anjumani",
 "xodimlar-bolimi",
 "xorijiy-abiturientlar-uchun-mandat-2025",
 "xorijiy-bolim",
 "xorijiy-fuqarolar-uchun-magistratura-va-klinik-ordinatura",
 "xotin-qizlar-qomitasi",
 "yoshlar-ittifoqi-bt"
]

# words of the old English texts that are Cyrillic by mistake
REPLACE_EN = {"территории": "territory", "инициативные": "proactive", "Мевшсфд": "Medical"}
CAPTIONS = {  # slug -> {block index: {lang: caption}}: translations of captions that were the same Uzbek (or English) text in the three languages
    "dak-savollari": {0: {"uz": "Yakuniy davlat attestatsiya testlari", "ru": "Тесты итоговой государственной аттестации", "en": "Final state attestation tests"},
                      1: {"uz": "Yakuniy davlat attestatsiya OSKI vazifalari", "ru": "Задания ОСКЭ итоговой государственной аттестации", "en": "OSCE tasks of the final state attestation"}},
}
POLICIES = [  # (words of the English title, uz, ru): the 17 policies of the Green University (the same titles as in script 54)
    ("accessible and clean energy", "Arzon va toza energiya siyosati", "Политика в области доступной и чистой энергии"),
    ("reducing inequalities", "Tengsizlikni kamaytirish siyosati", "Политика сокращения неравенства"),
    ("industry innovation", "Sanoat, innovatsiyalar va infratuzilma strategiyasi", "Стратегия индустриализации, инноваций и инфраструктуры"),
    ("clean water", "Toza suv va sanitariya siyosati", "Политика в области чистой воды и санитарии"),
    ("climate change", "Iqlim oʻzgarishi siyosati", "Политика в области изменения климата"),
    ("decent work", "Munosib mehnat va iqtisodiy oʻsish siyosati", "Политика достойного труда и экономического роста"),
    ("gender equality", "Gender tengligi siyosati", "Политика гендерного равенства"),
    ("healthy and quality life", "Sogʻlom va sifatli hayot siyosati", "Политика здоровой и качественной жизни"),
    ("seas and aquatic", "Dengizlar va suv muhitini muhofaza qilish siyosati", "Политика защиты морей и водных пространств"),
    ("terminate poverty", "Qashshoqlikka barham berish siyosati", "Политика ликвидации бедности"),
    ("quality education", "Sifatli taʻlim siyosati", "Политика качественного образования"),
    ("sustainable development goals", "Birlashgan Millatlar Tashkilotining barqaror rivojlanish maqsadlari", "Цели ООН в области устойчивого развития"),
    ("sustainable cities", "Barqaror shaharlar va jamiyatlar siyosati", "Политика устойчивых городов и сообществ"),
    ("production and consumption", "Barqaror ishlab chiqarish va isteʻmol siyosati", "Политика устойчивого производства и потребления"),
    ("hunger", "Ocharchilikka barham berish siyosati", "Политика ликвидации голода"),
    ("terrestrial life", "Quruqlikdagi hayotni saqlash siyosati", "Политика сохранения экосистем суши"),
]
SEMESTER_RU = ["2024–2025 учебный год. Педиатрический факультет: график итогового контроля",
               "2024–2025 учебный год. Педиатрический факультет, направление «Стоматология», 1–2 курсы: график итогового контроля",
               "2024–2025 учебный год. Педиатрический факультет, направление «Педиатрия», 1–2 курсы: график итогового контроля",
               "2024–2025 учебный год. Педиатрический факультет, направление «Фармация», 1–2 курсы: график итогового контроля",
               "2024–2025 учебный год. Международный факультет: график итогового контроля"]
plan, report = build(SLUGS)
by = {e["slug"]: e for e in plan}
missing = [s for s in SLUGS if s not in by]
assert not missing, missing


def walk_text(block, function):
    for lang, data in block["data"].items():
        for key in ("text", "caption", "alt"):
            if isinstance(data.get(key), str):
                data[key] = function(lang, data[key])
        if "items" in data:
            data["items"] = [function(lang, x) for x in data["items"]]
        if "rows" in data:
            data["rows"] = [[function(lang, c) for c in row] for row in data["rows"]]
            data["headers"] = [function(lang, c) for c in data["headers"]]


for item in plan:
    for block in item["blocks"]:
        walk_text(block, lambda lang, text: __import__("functools").reduce(lambda t, kv: t.replace(*kv), REPLACE_EN.items(), text) if lang == "en" else text)
    if item["slug"] == "17-goals-of-un-policies":
        for block in item["blocks"]:
            if block["block_type"] == "document":
                en = block["data"]["en"]["caption"].lower()
                found = [p for p in POLICIES if p[0] in en]
                assert len(found) == 1, en
                block["data"]["uz"]["caption"], block["data"]["ru"]["caption"] = found[0][1], found[0][2]
                block["data"]["en"]["caption"] = re.sub(r"^Fergana Medical Institute of Public Health['’ʻ]?s?,? ?", "", block["data"]["en"]["caption"]).rstrip(".")
                block["data"]["en"]["caption"] = block["data"]["en"]["caption"][:1].upper() + block["data"]["en"]["caption"][1:]
    if item["slug"] == "iqtidorli-talabalar":
        for block in item["blocks"]:
            name = re.sub(r"\s*erishilgan yutuqlari$", "", re.sub(r"^[>»\s]+", "", block["data"]["uz"]["caption"])).strip()
            block["data"]["uz"]["caption"] = "%s erishgan yutuqlari" % name
            block["data"]["ru"]["caption"] = "Достижения: %s" % name
            block["data"]["en"]["caption"] = "Achievements: %s" % name
    if item["slug"] == "test-markazi-semestr-grafigi":
        for block, ru in zip(item["blocks"], SEMESTER_RU):
            block["data"]["ru"]["caption"] = ru
    for index, captions in CAPTIONS.get(item["slug"], {}).items():
        for lang, text in captions.items():
            item["blocks"][index]["data"][lang]["caption"] = text
    for block in item["blocks"]:
        data = block["data"]["uz"]
        uz = " ".join([data.get(k, "") for k in ("text", "caption", "alt")] + data.get("items", []) + [c for row in data.get("rows", []) for c in row] + data.get("headers", []))
        assert not re.search(r"['‘’`´ʼ]", re.sub(r"\]\([^)]*\)", "]", re.sub(r"\b[a-z]+'s\b", "", uz))), (item["slug"], uz[:100])
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", len(plan), "pages,", sum(len(e["blocks"]) for e in plan), "blocks")
for slug, lines in report.items():
    if slug in by:
        print("review", slug[:50], "|", "; ".join(lines[:3])[:110])
