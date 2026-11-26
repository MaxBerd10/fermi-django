"""Builds plan.json of script 54 (Faoliyat > Xalqaro faoliyat: the pages "Xalqaro xamkor tashkilotlar" and "Iqlim boyicha xarakatlar strategiyasi") from the live pages.
Both pages were English text in all three languages (styled by hand in the editor: centred headings in blue, bold labels, the policies as a column of links). Now: typed blocks,
English stays for English, Uzbek and Russian are our translation (listed in tarjima-kerak.md); the 16 policy links become document cards (one per PDF, the 17th is the card the
page already had); the page "Xalqaro taʻlim" is only one document card and stays as it is. The third page of the section (Thumbay) is script 52.
    python deploy/content/yillik-hisobot-2026-54/make_plan.py"""
import json
import os
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


# ---------- page 1: Xalqaro xamkor tashkilotlar ----------
SLUG1 = "xalqaro-xamkor-tashkilotlar"
raw1, documents1 = page_blocks(SLUG1)
lines1 = {lang: lines_of(raw1["data"][lang]["html"]) for lang in LANGS}
en1 = [l["text"] for l in lines1["en"]]
assert en1[0].startswith("Head office for International students:") and en1[1] == "India Head Office:" and en1[-1] == "Phone:+91 1143036884", en1
picture1 = images_of(raw1["data"]["uz"]["html"])
assert len(picture1) == 1 and picture1[0].endswith("India.jpg") and all(images_of(raw1["data"][lang]["html"]) == picture1 for lang in LANGS)
blocks1 = [
    para(t("Xalqaro talabalar uchun bosh ofis: Fargʻona jamoat salomatligi tibbiyot instituti, Fargʻona, Oʻzbekiston.",
           "Головной офис для иностранных студентов: Ферганский медицинский институт общественного здоровья, Фергана, Узбекистан.",
           "Head office for International students: Fergana Medical Institute of Public Health, Fergana, Uzbekistan.")),
    heading(t("Hindistondagi bosh ofis", "Головной офис в Индии", "India Head Office"), 3),
    para(t("Manzil: 10-C, 10-qavat, Gopala Tower, Govind Lal Sikka Marg, Prasad Nagar, Nyu-Deli, Deli 110008.",
           "Адрес: 10-C, 10-й этаж, Gopala Tower, Govind Lal Sikka Marg, Prasad Nagar, Нью-Дели, Дели 110008.",
           "Address: 10-C, 10th Floor, Gopala Tower, Govind Lal Sikka Marg, Prasad Nagar, New Delhi, Delhi 110008.")),
    para(t("Telefon: +91 1143036884", "Телефон: +91 1143036884", "Phone: +91 1143036884")),
    image_block(picture1[0], t("Hindistondagi bosh ofis", "Головной офис в Индии", "India Head Office")),
]
card1 = captions_of_cards(documents1, [t("Institut haqida umumiy maʻlumot (inglizcha)", "Общая информация об институте (на английском)", "General information about the institute")])

# ---------- page 2: Iqlim boyicha xarakatlar strategiyasi ----------
SLUG2 = "iqlim-boyicha-xarakatlar-strategiyasi"
raw2, documents2 = page_blocks(SLUG2)
lines2 = {lang: lines_of(raw2["data"][lang]["html"]) for lang in LANGS}
assert all(len(lines2[lang]) == 32 for lang in LANGS)
en2 = [l["text"] for l in lines2["en"]]
assert en2[0].startswith("Five-Year Sustainability") and en2[2] == "MISSION" and en2[8] == "The plan has four areas of focus:" and en2[14] == "FERGHANA MEDICAL INSTITUTE OF PUBLIC HEALTH"
picture2 = images_of(raw2["data"]["uz"]["html"])
assert len(picture2) == 1 and picture2[0].endswith("osen.jpg") and all(images_of(raw2["data"][lang]["html"]) == picture2 for lang in LANGS)
TITLE = {"uz": "Fargʻona jamoat salomatligi tibbiyot instituti: besh yillik barqarorlik va iqlim boʻyicha harakatlar rejasi",
         "ru": "Пятилетний план действий по устойчивому развитию и климату Ферганского медицинского института общественного здоровья"}
TITLE["en"] = en2[0]  # the English heading as it is
POLICIES = [  # (line, English title without the name of the institute, uz, ru) - the links of lines 15..31
    (15, "Accessible and clean energy policy", "Arzon va toza energiya siyosati", "Политика в области доступной и чистой энергии"),
    (16, "Policy on Reducing Inequalities", "Tengsizlikni kamaytirish siyosati", "Политика сокращения неравенства"),
    (17, "Industry Innovation and Infrastructure Strategy", "Sanoat, innovatsiyalar va infratuzilma strategiyasi", "Стратегия индустриализации, инноваций и инфраструктуры"),
    (18, "Clean Water and Sanitation Policy", "Toza suv va sanitariya siyosati", "Политика в области чистой воды и санитарии"),
    (19, "Climate Change Policy", "Iqlim oʻzgarishi siyosati", "Политика в области изменения климата"),
    (20, "Decent Work and Economic Growth Policy", "Munosib mehnat va iqtisodiy oʻsish siyosati", "Политика достойного труда и экономического роста"),
    (21, "Gender Equality Policy", "Gender tengligi siyosati", "Политика гендерного равенства"),
    (22, "Healthy and Quality Life Policy", "Sogʻlom va sifatli hayot siyosati", "Политика здоровой и качественной жизни"),
    (23, "Policy for the Protection of the Seas and Aquatic Spaces", "Dengizlar va suv muhitini muhofaza qilish siyosati", "Политика защиты морей и водных пространств"),
    (24, "Policy to Terminate Poverty", "Qashshoqlikka barham berish siyosati", "Политика ликвидации бедности"),
    (25, "Quality Education Policy", "Sifatli taʻlim siyosati", "Политика качественного образования"),
    (26, "Sustainable Development Goals of the United Nations", "Birlashgan Millatlar Tashkilotining barqaror rivojlanish maqsadlari", "Цели ООН в области устойчивого развития"),
    (27, "Sustainable Cities and Societies Policy", "Barqaror shaharlar va jamiyatlar siyosati", "Политика устойчивых городов и сообществ"),
    (28, "Sustainable Development Goals of the United Nations", "Birlashgan Millatlar Tashkilotining barqaror rivojlanish maqsadlari", "Цели ООН в области устойчивого развития"),
    (29, "Sustainable Production and Consumption Policy", "Barqaror ishlab chiqarish va isteʻmol siyosati", "Политика устойчивого производства и потребления"),
    (30, "Terminating Hunger Policy", "Ocharchilikka barham berish siyosati", "Политика ликвидации голода"),
    (31, "Terrestrial Life Policy", "Quruqlikdagi hayotni saqlash siyosati", "Политика сохранения экосистем суши"),
]
for line, title, _, _ in POLICIES:
    assert title.lower().replace(".", "") in lines2["en"][line]["text"].lower().replace(".", "").replace("’s", "").replace(",", ""), (line, title, lines2["en"][line]["text"])
    assert len(lines2["en"][line]["links"]) == 1 and all(lines2[lang][line]["links"] == lines2["en"][line]["links"] for lang in LANGS)
p13 = en2[13].replace("o public health", "of public health")  # one typo of the source ("institute o public health")
blocks2 = [
    image_block(picture2[0], t(TITLE["uz"], TITLE["ru"], TITLE["en"])),
    heading(TITLE),
    para(t("Fargʻona jamoat salomatligi tibbiyot institutining 2022–2027-yillarga moʻljallangan barqarorlik va iqlim boʻyicha harakatlar rejasi yakunlandi va amalga oshirishga tayyor: unda maqsadlarga erishish uchun jasoratli koʻrsatkichlar va batafsil choralar belgilangan. Besh yillik reja institutning xoʻjalik va infratuzilma boʻlimi jamoasi olib borgan va kampusning koʻplab manfaatdor tomonlarini qamrab olgan uzoq jamoatchilik jarayoni natijasidir. 2021-yilda barqarorlik va iqlim oʻzgarishi borasidagi jamoatchilik tushunchasi va xavotirlarini aniqlash uchun soʻrovnoma oʻtkazildi. Bir necha ochiq uchrashuvdan soʻng kampusdagi turli boʻlimlar va talabalardan iborat 40 dan ortiq kishilik guruh tuzildi va ular taxminan bir yil davomida besh yillik rejani ishlab chiqdi.",
           "План действий Ферганского медицинского института общественного здоровья по устойчивому развитию и климату на 2022–2027 годы завершён и готов к реализации: в нём определены амбициозные цели и подробные меры для их достижения. Пятилетний план — результат длительного общественного процесса, проведённого командой службы эксплуатации и инфраструктуры института с участием широкого круга участников кампуса. В 2021 году был проведён опрос, чтобы определить исходный уровень понимания и озабоченности сообщества вопросами устойчивого развития и изменения климата. После нескольких открытых встреч была сформирована группа из более чем 40 человек из разных подразделений кампуса и студентов, которая около года разрабатывала пятилетний план.",
           en2[1])),
    heading(t("Missiya", "Миссия", "Mission")),
    para(t("Taʻlim, tadqiqot, tibbiy xizmat koʻrsatish va jamoatchilik xizmatida yetakchilik qilib va yangilik yaratib, biz Fargʻonadagi va butun dunyodagi turli hamjamiyatlarning salomatligi va farovonligini yaxshilaymiz.",
           "Возглавляя и внедряя инновации в образовании, науке, оказании медицинской помощи и общественном служении, мы улучшаем здоровье и благополучие разных сообществ в Фергане и во всём мире.",
           en2[3])),
    heading(t("Barqarorlikning taʻrifi", "Определение устойчивого развития", "Definition of sustainability")),
    para(t("Fargʻona jamoat salomatligi tibbiyot instituti barqarorlikni keng va yaxlit maʻnoda taʻriflaydi. Oliy taʻlimda barqarorlikni rivojlantirish assotsiatsiyasi (AASHE) barqarorlikni «inson va ekologik salomatlik, ijtimoiy adolat, barqaror turmush vositalari va barcha avlodlar uchun yaxshiroq sayyora» deb taʻriflaydi. Institutning ekologik, ijtimoiy va iqtisodiy muammolarga taʻsirini hisobga oladigan barqaror amaliyotlar ushbu majburiyatga kiradi.",
           "Ферганский медицинский институт общественного здоровья понимает устойчивость широко и целостно. Ассоциация по развитию устойчивости в высшем образовании (AASHE) определяет её как «здоровье человека и экосистем, социальную справедливость, стабильные средства к существованию и лучшую планету для всех поколений». В это обязательство входят устойчивые практики, учитывающие влияние института на экологические, социальные и экономические проблемы.",
           en2[5])),
    heading(t("Barqarorlik va iqlim boʻyicha harakatlar qarashi", "Видение устойчивого развития и климатических действий", "Vision for sustainability and climate action")),
    para(t("Oʻz faoliyati, taʻlimi va tadqiqotlari orqali Fargʻona jamoat salomatligi tibbiyot instituti barqarorlikni oshiradigan, iqlim oʻzgarishini yumshatadigan va kelajak avlodlar uchun resurslarni tejaydigan tibbiy taʻlim va tadqiqotlarni taqdim etib, mamlakat va butun dunyo aholisining farovonligiga hissa qoʻshadi.",
           "Через свою деятельность, образование и исследования Ферганский медицинский институт общественного здоровья способствует благополучию всех людей в стране и мире, предоставляя медицинское образование и научные исследования, которые повышают устойчивость, смягчают изменение климата и сберегают ресурсы для будущих поколений.",
           en2[7])),
    para(t("Rejada toʻrtta asosiy yoʻnalish bor:", "В плане четыре приоритетных направления:", en2[8])),
    block("list", {"uz": {"items": ["Transport", "Binolar va energiya", "Hudud va suvni boshqarish", "Materiallar va resurslarni boshqarish"]},
                   "ru": {"items": ["Транспорт", "Здания и энергетика", "Территория и управление водными ресурсами", "Материалы и управление ресурсами"]},
                   "en": {"items": en2[9:13]}}),
    para(t("Har bir yoʻnalish uchun besh yillik maqsadlarga erishishga yordam beradigan aniq tadbirlar roʻyxati mavjud. Masalan, transport boʻyicha institut kampusda foydalaniladigan transport vositalaridan chiqadigan emissiyani ikki baravar kamaytirishni rejalashtirmoqda. Bundan tashqari, kampusga qatnovdan chiqadigan emissiyani kamaytirish ham qiyinchilik tugʻdirmoqda. Bu klinik komponentga ega, ilmiy-tadqiqotlarga yoʻnaltirilgan kampus boʻlgani uchun rejada alohida binolarda energiya sarfini oʻlchash va tekshirish dasturini yaratishni davom ettirish hamda barcha obyektlarda energiyani tejash va qayta tiklashni kuchaytirish koʻzda tutilgan. Materiallar va resurslarni boshqarish boʻyicha kampus hosil qiladigan qattiq chiqindi miqdorini 20 foizga kamaytiradi. Institut rejalashtirish jarayonini boshqarishda yordam berish uchun oliy taʻlim va sogʻliqni saqlash tashkilotlariga iqlim oʻzgarishi taʻsirini yumshatishda koʻmaklashadigan maslahat guruhi — oʻz hamkorlari bilan ishlaydi. Hamkorlarimiz energiyani tejash va issiqxona gazlarini kamaytirish boʻyicha iqlim harakatlari strategiyalarini ishlab chiqish va amalga oshirishda bizga yordam beradi.",
           "Для каждого направления составлен перечень конкретных мер, помогающих достичь пятилетних целей. Например, в области транспорта институт планирует вдвое сократить выбросы от транспортных средств, используемых на территории кампуса. Кроме того, сложностью остаётся сокращение выбросов от поездок в кампус. Поскольку это кампус с интенсивной научной работой и клиническим компонентом, план предусматривает продолжение создания программы измерения и проверки энергопотребления для отдельных зданий, а также усиление энергосбережения и рекуперации во всех объектах. В области материалов и управления ресурсами кампус сократит объём образуемых твёрдых отходов на 20 %. Институт взаимодействует со своими партнёрами — консалтинговой группой, цель которой — помогать организациям высшего образования и здравоохранения смягчать последствия изменения климата, — чтобы возглавить процесс планирования. Наши партнёры помогают нам разрабатывать и реализовывать климатические стратегии по энергосбережению и сокращению выбросов парниковых газов.",
           p13)),
    heading(t("Fargʻona jamoat salomatligi tibbiyot instituti siyosatlari: BMTning barqaror rivojlanish maqsadlari",
              "Политики Ферганского медицинского института общественного здоровья: цели ООН в области устойчивого развития",
              "Ferghana Medical Institute of Public Health policies: the UN Sustainable Development Goals")),
]
for line, title, uz, ru in POLICIES[1:]:  # the first policy is the card the page already has (it stays last)
    blocks2.append(document_block(media_of(lines2["uz"][line]["links"][0][0]), t(uz, ru, title)))
first = POLICIES[0]
card2 = captions_of_cards(documents2, [t(first[2], first[3], first[1])])

plan = [entry(SLUG1, raw1, blocks1, card1), entry(SLUG2, raw2, blocks2, card2)]
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"], len(e["blocks"])) for e in plan])
