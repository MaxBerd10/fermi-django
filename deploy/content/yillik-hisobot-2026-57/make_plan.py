"""Builds plan.json of script 57 (Faoliyat > Madaniy-marifiy faoliyat, Oquv-uslubiy faoliyat) from the live pages:
Kam taminlangan talabalar uchun yaratilgan imkoniyatlar (one long page: an introduction and seven pairs "question - answer"), Malaka tavsifnoma and Malaka talablari (lists of PDF links),
Reyting nizomi (one PDF). The Uzbek text of the first page had its first paragraph twice, the old spelling (x for h: "xolda", "maxalla", "isloxot"), "retkor" for "rektor" and one run-on
sentence: it is written again in clean Uzbek (listed in tarjima-kerak.md); Russian follows its own text, English had two lines glued together (split here).
    python deploy/content/yillik-hisobot-2026-57/make_plan.py"""
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


plan = []

# ================= 1. Kam taminlangan talabalar =================
slug = "kam-taminlangan-talabalar-uchun-yaratilgan-imkoniyatlar"
raw, documents = page_blocks(slug)
assert not documents
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert len(L["uz"]) == 15 and len(L["ru"]) == 15 and len(L["en"]) == 13
assert L["uz"][0]["text"].count("Fargʻona jamoat salomatligi tibbiyot institutida") == 2  # the first paragraph is written twice
en6 = L["en"][6]["text"]
cut1, cut2 = en6.index(" Training and awareness"), en6.index(" According to the action plan")
en_parts = {6: en6[:cut1].strip(), 7: en6[cut1:cut2].strip(), 8: en6[cut2:].strip()}
EN = {i: L["en"][i]["text"] for i in range(6)}
EN.update(en_parts)
EN.update({i + 2: L["en"][i]["text"] for i in range(7, 13)})
assert len(EN) == 15
RU = {i: L["ru"][i]["text"] for i in range(15)}
UZ = {
    0: "Fargʻona jamoat salomatligi tibbiyot institutida kam taʼminlangan va nogironligi boʻlgan talabalar soni 60 nafardan ortiq boʻlib, 2022–2023-oʻquv yilida ulardan 39 nafariga bir qancha imkoniyatlar yaratilgan. “Temir” va “Ayollar” daftarida turuvchi hamda nogironligi bor 3 nafar talabaga turar joydan bepul yotoqxona berilgan va kerakli sharoitlar yaratib berilgan. Qolgan 36 nafar talabaga talabalar turar joyining yillik toʻlovidan 50 foiz chegirma qilish orqali toʻlovlarda yordam berilmoqda.",
    1: "Kam taʼminlangan va qiynalgan talabalarning oʻqishni muvaffaqiyatli tamomlashlari uchun",
    2: "Oʻzbekiston Respublikasi Prezidentining 2021-yil 9-avgustdagi «Yetim bolalar va ota-ona qaramogʻidan mahrum boʻlgan bolalarni davlat tomonidan qoʻllab-quvvatlashning yangi tizimini joriy etish chora-tadbirlari toʻgʻrisida»gi PQ-5216-sonli qarorining 10-bandiga muvofiq, yetim bolalar va ota-ona qaramogʻidan mahrum boʻlgan bolalarning taʼlim olishini qoʻllab-quvvatlash maqsadida institutda taʼlim olayotgan davrida ushbu talabalarga bir martalik oʻquv, ilmiy va badiiy adabiyotlar xarid qilish xarajatlari uchun Davlat byudjeti mablagʻlari hisobidan bazaviy hisoblash miqdorining 5 baravari miqdorida subsidiyalar ajratilib kelinmoqda.",
    3: "Kam taʼminlangan oilalardagi talabalarga institutni tamomlashlari uchun moddiy va maʼnaviy yordam berish",
    4: "Shu qarorning 10-bandiga muvofiq institutda taʼlim olayotgan ota-ona qaramogʻidan mahrum boʻlgan 8 nafar talabaga Talabalarni ragʻbatlantirish jamgʻarmasi mablagʻlari hisobidan 50 foizga oshirilgan miqdorda stipendiya toʻlanib kelmoqda. Ushbu qaror ijrosini taʼminlash maqsadida ota-ona qaramogʻidan mahrum boʻlgan har bir talabaga shaxsiy gigiyena buyumlari, oziq-ovqat mahsulotlari, kiyim-bosh, poyabzal va boshqa buyumlar sotib olish hamda transportda yurish uchun kartochkalar olish uchun qarorda koʻrsatilganidek, qonun doirasida maʼlum miqdorda summalar ajratilib kelinmoqda.",
    5: "Kam taʼminlangan talabalarga oʻqishni muvaffaqiyatli yakunlashda yordam beradigan dasturlar yoki tashabbuslar",
    6: "Yuqoridagi qarorga muvofiq institutda taʼlim olayotgan ota-ona qaramogʻidan mahrum boʻlgan 8 nafar talaba Talabalarni ragʻbatlantirish jamgʻarmasi mablagʻlari hisobidan 50 foizga oshirilgan miqdorda stipendiya olmoqda; bu ularning oʻqishni muvaffaqiyatli tamomlashiga yordam beradi.",
    7: "Barcha uchun asosiy xizmatlardan foydalanish imkoniyatini yaxshilash uchun treninglar yoki dasturlar",
    8: "Yoshlar bilan ishlash, maʼnaviyat va maʼrifat boʻlimi tomonidan ishlab chiqilgan tadbirlar rejasiga muvofiq, boʻlim va rektorning xotin-qizlar masalalari boʻyicha maslahatchisi hamkorligida talaba yoshlarga sogʻlom turmush tarzini toʻgʻri talqin qilish boʻyicha tadbirlar va seminarlar tashkil etilgan. Shuningdek, institutga biriktirilgan Fargʻona tumani mahallalarida ham aholi oʻrtasida sogʻlom turmush tarzini yaxshilash boʻyicha targʻibot ishlari olib borilmoqda. Institut professor-oʻqituvchilari tomonidan mahalla aholisi uchun bepul tibbiy koʻriklar tashkil etilmoqda.",
    9: "Mahalliy, mintaqaviy, milliy yoki global miqyosda kambagʻallikni qisqartirish boʻyicha dasturlar va siyosatlarni amalga oshirish uchun siyosiy hujjat ishlab chiqishda organ sifatida ishtiroki",
    10: "Institutda talabalarga Oʻzbekistonda hozirgi kunda yaratilayotgan imkoniyatlar va islohotlar tushuntirilmoqda: kam taʼminlangan va iqtisodiy nochor oilalarga, oilasida mehnatga layoqatsiz nogironlar va surunkali kasallikka chalingan aʼzolari bor oilalarga, yakka-yolgʻiz keksalar, bevalar va oʻzgalar qaramogʻiga muhtoj kam taʼminlanganlardan iborat oilalarga hamda besh va undan koʻp farzandi bor oilalarga koʻrsatilayotgan imkoniyatlar haqida tushuntirish ishlari olib borilmoqda.",
    11: "Institut yuridik shaxs sifatida mahalliy jamiyatda salomatlik va farovonlikni yaxshilash yoki targʻib qilish, jumladan gigiena, ovqatlanish, oilani rejalashtirish, sport, jismoniy mashqlar, qarish va boshqa salomatlik va farovonlik boʻyicha targʻibot dasturlari va loyihalarini taqdim etadi",
    12: "Institut kafedralari professor-oʻqituvchilari Fargʻona tumani mahallalari bilan hamkorlikda sport tadbirlari, tanlov va musobaqalar oʻtkazib kelmoqda. Institutda talabalardan tashkil etilgan volontyorlik guruhlari mavjud boʻlib, ushbu volontyorlar tomonidan mahalla yoshlari bilan doʻstona tadbirlar, musobaqalar oʻtkazib kelinmoqda va salomatlik va farovonlik boʻyicha targʻibot ishlari olib borilmoqda.",
    13: "Institut tashkilot sifatida sport inshootlarini mahalliy hamjamiyat bilan, masalan, mahalliy maktablar yoki keng jamoatchilik bilan baham koʻradi",
    14: "Fargʻona shahar Ozodlik koʻchasida joylashgan institutga qarashli sport zali va sport maydonchalaridan “Tinchlik” va “Boʻston” MFYga qarashli maktab oʻquvchilari volleybol va taekvondo bilan shugʻullanmoqda. Institutda faoliyat olib borayotgan psixolog Yu. Hamedova tomonidan talabalar uchun psixologik suhbatlar, soʻrovnomalar, anonim soʻrovnomalar vaqti-vaqti bilan oʻtkazilmoqda. Shuningdek, talabalar turar joyida yashayotgan talabalar bilan har kuni individual suhbatlar oʻtkazib kelinmoqda. Institutning 2022-yil 30-avgust kuni boʻlib oʻtgan kengashida institut “Odob-axloq qoidalari” va “Ichki tartib qoidalari” tasdiqlandi va tyutorlar tomonidan talabalarga tushuntirish ishlari olib borilmoqda. Ushbu qoidalarda keltirilgan qoida va moddalarga har bir professor-oʻqituvchi, xodim va talaba, chet mamlakatdan kelib taʼlim olayotgan talabalar ham amal qilishlari shart. Institutda ushbu qoidalarda keltirilgan qoida va moddalarga tayangan holda va qonundan chetga chiqmagan holda har bir professor-oʻqituvchi, xodim va talaba himoya qilinadi.",
}
blocks = []
for i in range(15):
    if i % 2 == 1:
        blocks.append(heading(t(UZ[i], RU[i].rstrip(":"), EN[i].rstrip(":"))))
    else:
        blocks.append(para(t(UZ[i], RU[i], EN[i])))
entry_ = entry(slug, raw, blocks)
entry_["notes"] = ["uz text written again in clean Uzbek: the first paragraph was there twice, old spelling (xolda, maxalla, isloxot, suxbat, xamkorlik...), 'retkor' = rektor, 'Etim' = Yetim, one run-on sentence (block 10) made readable; en: one line held three blocks (resolution, heading, paragraph): split"]
plan.append(entry_)

# ================= 2/3. Malaka tavsifnoma, Malaka talablari =================
DIRECTIONS = {
    "davolash": ("Davolash ishi", "лечебное дело", "Medicine"),
    "pediatriya": ("Pediatriya ishi", "педиатрия", "Pediatrics"),
    "biotibbiyot": ("Biotibbiyot muhandisligi", "биомедицинская инженерия", "Biomedical Engineering"),
    "biologik": ("Tibbiy biologik ish", "медико-биологическое дело", "Medical Biology"),
    "profilaktika": ("Tibbiy profilaktika ishi", "медико-профилактическое дело", "Preventive Medicine"),
    "tabobat": ("Xalq tabobati", "народная медицина", "Traditional Medicine"),
    "kasbiy": ("Kasbiy taʼlim", "профессиональное образование", "Vocational Education"),
    "hamshira": ("Oliy hamshiralik ishi", "высшее сестринское дело", "Higher Nursing"),
    "farmatsiya": ("Farmatsiya", "фармация", "Pharmacy"),
    "stomatologiya": ("Stomatologiya", "стоматология", "Dentistry"),
}

slug = "malaka-tavsifnoma"
raw, documents = page_blocks(slug)
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert all(len(L[lang]) == 6 for lang in LANGS) and len(documents) == 1 and documents[0]["data"]["uz"]["document"]["file_size"] == 15548211
order = ["davolash", "pediatriya", "biotibbiyot", "biologik", "profilaktika", "tabobat"]
cap = lambda key: t("%s malaka tavsifnomasi" % DIRECTIONS[key][0], "Квалификационная характеристика: %s" % DIRECTIONS[key][1], "Qualification profile: %s" % DIRECTIONS[key][2])
hrefs = [L["uz"][i]["links"][0][0] for i in range(6)]
assert all(L[lang][i]["links"][0][0] == hrefs[i] for lang in LANGS for i in range(6))
blocks = [document_block(media_of(hrefs[i]), cap(order[i])) for i in range(1, 6)]  # the first PDF (Davolash ishi, 15 MB) is the card the page already has
entry_ = entry(slug, raw, blocks, captions_of_cards(documents, [cap("davolash")]))
entry_["notes"] = ["the six links are document cards (five new, the first 'Davolash ishi' is the card the page already had: it stays last); the ru captions were broken Russian ('Описания должности обязанностей по направления Надорного дедицина'): written again, en 'Biomedical enjineering' fixed"]
plan.append(entry_)

slug = "malaka-talablari"
raw, documents = page_blocks(slug)
L = {lang: lines_of(raw["data"][lang]["html"]) for lang in LANGS}
assert all(len(L[lang]) == 10 for lang in LANGS) and len(documents) == 1
order = ["kasbiy", "hamshira", "profilaktika", "pediatriya", "davolash", "farmatsiya", "stomatologiya", "tabobat", "biologik", "biotibbiyot"]
cap = lambda key: t("Malaka talablari: %s yoʻnalishi" % DIRECTIONS[key][0],
                    "Квалификационные требования: %s" % DIRECTIONS[key][1], "Qualification requirements: %s" % DIRECTIONS[key][2])
hrefs = [L["uz"][i]["links"][0][0] for i in range(10)]
assert all(L[lang][i]["links"][0][0] == hrefs[i] for lang in LANGS for i in range(10))
blocks = [document_block(media_of(hrefs[i]), cap(order[i])) for i in range(10)]
card = captions_of_cards(documents, [t("Davolash ishi (60910200) bakalavriat taʼlim yoʻnalishining malaka talablari, 2023", "Квалификационные требования к направлению бакалавриата «Лечебное дело» (60910200), 2023",
                                       "Qualification requirements for the Bachelor’s programme in Medicine (60910200), 2023")])
entry_ = entry(slug, raw, blocks, card)
entry_["notes"] = ["ten links are document cards with captions in three languages (the old ru/en captions were the Uzbek text with wrong apostrophes); the card the page already had is the NEW (2023) requirements for Davolash ishi, it stays last"]
plan.append(entry_)

# ================= 4. Reyting nizomi =================
page = fetch("https://fermi.uz/api/v1/pages/reyting-nizomi/")["blocks"]
doc = [b for b in page if b["block_type"] == "document"]
assert len(page) == 1 and len(doc) == 1
plan.append({"slug": "reyting-nizomi", "existing_documents": captions_of_cards(doc, [t("Reyting nizomi", "Положение о рейтинге", "Rating regulation")]),
             "notes": ["only the caption of the PDF card is set (written by us from the menu label)"]})

for item in plan:
    texts = [b["data"]["uz"].get("text", "") or b["data"]["uz"].get("caption", "") for b in item.get("blocks", [])] + [c["caption"]["uz"] for c in item.get("existing_documents", [])]
    for text in texts:
        assert not re.search(r"['‘’`´]", text) and "  " not in text, text
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"][:25], len(e.get("blocks", [])) if "blocks" in e else "captions") for e in plan])
