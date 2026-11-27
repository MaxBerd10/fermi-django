"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-110/make_plan.py

Texts of page blocks that Russian / English (sometimes Uzbek) readers see in the wrong language, found by loading 405 pages of the live site in ru and en and reading what is on screen:
  * mutaxassisliklar-boyicha-testlar-toplami: the titles of the 45 test collections were the same Uzbek (or Russian) title in all three languages: each language gets its own title, the language of
    the file in brackets: (uzb) -> (узб.) / (Uzbek), (rus) -> (рус.) / (Russian) -- the form the one title already translated by the staff (#75) uses;
  * respublika-ilmiy-konferensiyalari: the eight conference titles and two "Программа конференции" captions; ilmiy-konferensiyalar #23-25: the captions of the three information letters
    (Russian / English / Uzbek) were the same line in all languages: built from the titles already there in each language;
  * avtoreferatlar: the 13 doctoral candidates (names: Russian gets Cyrillic, English keeps the Latin) and the titles of their theses (ru, en);
  * jcpm-2024 #10, #47 and jcpm-2025 #28, #29, #41: the English title was the Russian one;
  * institut-yol-xaritasi-2025, abituriyentlar-uchun-talim-yonalishlari-va-institut-tarixi, institut-gazetasi-2025: a card title;
  * news xalqaro-hamkorlik-5 #1: the Russian text was a copy of the English one (with "Uni versity"): now a translation of the Uzbek text; news "...Oliy Majlis va Oʻzbekiston xalqiga murojaatnomasi" #88:
    a Cyrillic "с" in the English word "creating".
Every op: {slug of the page, order, lang, field, old, new}. All translations are Claude's wording, to be read by the staff.
Left as they are on purpose: titles of articles in their own language (the journal archive), the poem of "zulfiyaxonim-izdoshlari", personal names in English, brand names."""
import json
import re
import subprocess
import time
import urllib.parse
from pathlib import Path

ops = []
cache = {}


def api(path):
    for _ in range(5):
        text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/" + path + ("&" if "?" in path else "?") + "v=110"], capture_output=True, text=True).stdout
        try:
            return json.loads(text)
        except ValueError:
            time.sleep(2)
    raise SystemExit("API did not answer: " + path)


def blocks_of(slug):
    if slug not in cache:
        cache[slug] = {b["order"]: b for b in api("pages/%s/" % slug)["blocks"]}
    return cache[slug]


def put(slug, order, lang, field, new, page_slug=None):
    block = blocks_of(slug)[order] if page_slug is None else page_slug[order]
    old = block["data"][lang][field]
    if old == new:
        return
    ops.append({"slug": slug if page_slug is None else page_slug["slug"], "order": order, "lang": lang, "field": field, "old": old, "new": new})


def caption_of(block):
    return "caption" if block["block_type"] == "document" else "text"


def set_all(slug, order, uz=None, ru=None, en=None):
    block = blocks_of(slug)[order]
    for lang, value in (("uz", uz), ("ru", ru), ("en", en)):
        if value is not None:
            put(slug, order, lang, caption_of(block), value)


# ---- mutaxassisliklar-boyicha-testlar-toplami ------------------------------------------------------------------------------------------------------
S = "mutaxassisliklar-boyicha-testlar-toplami"
TAG = {"uzb": (" (uzb)", " (узб.)", " (Uzbek)"), "rus": (" (rus)", " (рус.)", " (Russian)"), None: ("", "", "")}
# order: (tag, uz or None (keep), ru or None (keep), en)
TESTS = {
    3: ("uzb", None, "Гистология, цитология и эмбриология, тест", "Histology, cytology and embryology test"),
    4: ("uzb", None, "Медицинская биология, общая генетика", "Medical biology, general genetics"),
    5: ("rus", "Biologiya fanidan testlar", None, "Tests in Biology"),
    6: ("rus", "Botanika fanidan testlar", None, "Tests in Botany"),
    7: ("rus", "Biologiya, ekologiya asoslari fanidan testlar", None, "Tests in Biology and the Fundamentals of Ecology"),
    8: ("rus", "Tibbiy biologiya, umumiy genetika fanidan testlar", None, "Tests in Medical Biology and General Genetics"),
    9: ("uzb", None, "Медицинская биология", "Medical biology"),
    11: ("uzb", None, "Информационные технологии", "Information technologies"),
    12: ("uzb", None, "Сборник тестов по предмету «Схемотехника»", "Collection of tests in Circuit Engineering"),
    13: ("uzb", None, "Сборник тестов по предмету «Электротехника»", "Collection of tests in Electrical Engineering"),
    14: ("uzb", None, "Сборник тестов по предмету «Схемотехника»", "Collection of tests in Circuit Engineering"),
    15: ("uzb", None, "Сборник тестов по предмету «Общие и теоретические основы электротехники»", "Collection of tests in General and Theoretical Foundations of Electrical Engineering"),
    17: (None, None, "Карантинные болезни", "Quarantine diseases"),
    18: ("uzb", None, "Военная эпидемиология", "Military epidemiology"),
    19: ("rus", None, "Военная эпидемиология", "Military epidemiology"),
    20: ("uzb", None, "Медико-профилактическое дело", "Preventive medicine"),
    21: ("rus", "Epidemiologik vaziyatlar va immunoprofilaktika OMX", None, "Epidemiological situations and immunoprophylaxis, OMX"),
    22: ("rus", "Epidemiologik vaziyatlar va immunoprofilaktika TPI", None, "Epidemiological situations and immunoprophylaxis, TPI"),
    23: ("uzb", None, "Эпидемиологические ситуации и иммунопрофилактика, OMX", "Epidemiological situations and immunoprophylaxis, OMX"),
    24: ("uzb", None, "Эпидемиологические ситуации и иммунопрофилактика, TPI", "Epidemiological situations and immunoprophylaxis, TPI"),
    25: ("uzb", None, "Инфекционные болезни и детские инфекционные болезни, профессиональное образование", "Infectious diseases and childhood infectious diseases, professional education"),
    26: ("uzb", None, "Инфекционные болезни, медико-профилактическое дело", "Infectious diseases, preventive medicine"),
    28: ("uzb", None, "Гигиена. Медицинская экология", "Hygiene. Medical ecology"),
    29: ("rus", "Gigiyena. Tibbiy ekologiya", None, "Hygiene. Medical ecology"),
    30: ("uzb", None, "Гигиена. Медицинская экология, TPI, 2 курс", "Hygiene. Medical ecology, TPI, year 2"),
    31: ("uzb", None, "Гигиена. Медицинская экология", "Hygiene. Medical ecology"),
    32: ("rus", "Gigiyena. Tibbiy ekologiya, Davolash ishi", None, "Hygiene. Medical ecology, General Medicine"),
    33: ("rus", "Gigiyena. Tibbiy ekologiya", None, "Hygiene. Medical ecology"),
    35: ("uzb", None, "Пропедевтика внутренних болезней, направление «Лечебное дело»", "Propedeutics of internal diseases, General Medicine programme"),
    37: ("uzb", None, "OXTA. Лечебное дело, практика (помощник медсестры)", "OXTA. General Medicine, practice (nurse assistant)"),
    38: ("rus", None, "OXTA. Стоматология — клиническая анатомия", "OXTA. Dentistry — clinical anatomy"),
    39: ("uzb", None, "OXTA. Народная медицина, клиническая анатомия", "OXTA. Traditional medicine, clinical anatomy"),
    41: ("rus", None, "Микробиология", "Microbiology"),
    42: ("uzb", None, "Микробиология", "Microbiology"),
    43: ("uzb", None, "Микробиология, высшее сестринское дело", "Microbiology, higher nursing"),
    44: ("rus", "Immunologiya testi, Davolash ishi, Pediatriya, 3-kurs", None, "Immunology test, General Medicine, Pediatrics, year 3"),
    45: ("rus", "Mikrobiologiya, Oliy hamshiralik ishi", None, "Microbiology, higher nursing"),
    47: ("uzb", None, "Патологическая анатомия", "Pathological anatomy"),
    49: ("uzb", None, "Патологическая физиология", "Pathological physiology"),
    51: ("uzb", None, "Медицинская биология", "Medical biology"),
    52: ("uzb", None, "Медицинская биология", "Medical biology"),
    53: ("uzb", None, "Медицинская биология", "Medical biology"),
    55: ("uzb", None, "Биохимия", "Biochemistry"),
    56: ("uzb", None, "Неорганическая химия", "Inorganic chemistry"),
    57: ("uzb", None, "Медицинская химия", "Medical chemistry"),
    58: ("uzb", None, "Медицинская биология, общая генетика", "Medical biology, general genetics"),
    59: ("rus", "Kimyo fanidan testlar (KGMU)", None, "Chemistry tests (KGMU)"),
    61: ("uzb", None, "Медицинская психология", "Medical psychology"),
    62: ("uzb", None, "Фтизиатрия", "Phthisiology"),
    64: ("uzb", None, "Фармакология", "Pharmacology"),
    66: ("uzb", None, "Иностранный язык в медицине", "Foreign language in medicine"),
    67: ("uzb", None, "Акушерство", "Obstetrics"),
    68: ("uzb", None, "Физиология, тестовые вопросы", "Physiology test questions"),
    69: ("uzb", None, "Тестовые вопросы. Физиология", "Physiology test questions"),
    71: ("uzb", None, "Общая хирургия, для 4 курса TPI", "General surgery, for year 4 of TPI"),
    72: ("rus", None, "Общая хирургия, для 4 курса TPI", "General surgery, for year 4 of TPI"),
    73: ("rus", None, "Общая хирургия, для направления «Лечебное дело»", "General surgery, for the General Medicine programme"),
}
tests = blocks_of(S)
for order, (tag, uz, ru, en) in TESTS.items():
    block = tests[order]
    assert block["block_type"] == "document", order
    t_uz, t_ru, t_en = TAG[tag]
    set_all(S, order, uz=None if uz is None else uz + t_uz, ru=None if ru is None else ru + t_ru, en=en + t_en)

# ---- conferences --------------------------------------------------------------------------------------------------------------------------------------
S = "respublika-ilmiy-konferensiyalari"
CONF = {
    1: (None, "АКТУАЛЬНЫЕ ПРОБЛЕМЫ ПУЛЬМОНОЛОГИИ", "TOPICAL PROBLEMS OF PULMONOLOGY"),
    2: (None, "ПРОФИЛАКТИЧЕСКАЯ МЕДИЦИНА НА ОСНОВЕ ЭПИДЕМИОЛОГИИ-2024", "EPIDEMIOLOGY-BASED PREVENTIVE MEDICINE-2024"),
    3: ("XXI ASRDA PSIXIATRIYA VA PSIXOSOMATIKA", None, "PSYCHIATRY AND PSYCHOSOMATICS IN THE 21ST CENTURY"),
    4: (None, "МЕЖДИСЦИПЛИНАРНЫЕ ПОДХОДЫ В АНАТОМИИ И ХИРУРГИИ: ОТ ФУНДАМЕНТАЛЬНЫХ ИССЛЕДОВАНИЙ ДО КЛИНИЧЕСКОЙ ПРАКТИКИ", "INTERDISCIPLINARY APPROACHES IN ANATOMY AND SURGERY: FROM FUNDAMENTAL RESEARCH TO CLINICAL PRACTICE"),
    5: (None, "ЗНАЧЕНИЕ ВЫСОКОТЕХНОЛОГИЧНОЙ ХИРУРГИЧЕСКОЙ ПРАКТИКИ", "THE IMPORTANCE OF HIGH-TECH SURGICAL PRACTICE"),
    6: (None, "ЗНАЧЕНИЕ ОКРУЖАЮЩЕЙ СРЕДЫ И ЗДОРОВОГО ПИТАНИЯ В ОХРАНЕ ОБЩЕСТВЕННОГО ЗДОРОВЬЯ", "THE IMPORTANCE OF THE ENVIRONMENT AND HEALTHY NUTRITION IN PROTECTING PUBLIC HEALTH"),
    7: ("XXI ASR INSON SALOMATLIGI: DOLZARB MASALALAR, MUAMMOLAR VA INNOVATSIYALAR", None, "HUMAN HEALTH OF THE 21ST CENTURY: TOPICAL ISSUES, PROBLEMS AND INNOVATIONS"),
    8: ("NEVROLOGIYA VA PSIXIATRIYADA MULTIDISSIPLINAR YONDASHUV: FAN VA AMALIYOT", None, "A MULTIDISCIPLINARY APPROACH IN NEUROLOGY AND PSYCHIATRY: SCIENCE AND PRACTICE"),
    9: ("Konferensiya dasturi", None, "Conference programme"),
    10: ("Konferensiya dasturi", None, "Conference programme"),
}
for order, (uz, ru, en) in CONF.items():
    set_all(S, order, uz=uz, ru=ru, en=en)

S = "ilmiy-konferensiyalar"
b = blocks_of(S)
uz_title = b[25]["data"]["uz"]["caption"].split(" — ", 1)[1]
ru_title = b[23]["data"]["ru"]["caption"].split(" — ", 1)[1]
en_title = b[24]["data"]["en"]["caption"].split(" — ", 1)[1]
set_all(S, 23, uz="Ruscha — Axborot xati: " + uz_title.split(": ", 1)[1], en="Russian — Information letter: " + en_title.split(": ", 1)[1])
set_all(S, 24, uz="Inglizcha — Axborot xati: " + uz_title.split(": ", 1)[1], ru="Английский — Информационное письмо: " + ru_title.split(": ", 1)[1])
set_all(S, 25, ru="Узбекский — Информационное письмо: " + ru_title.split(": ", 1)[1], en="Uzbek — Information letter: " + en_title.split(": ", 1)[1])

# ---- avtoreferatlar ----------------------------------------------------------------------------------------------------------------------------------
S = "avtoreferatlar"
AVTO = {
    2: ("Шакиров Сардор Абдусаминович", None),
    3: ("Патологическая анатомия почек при COVID-19-инфекции", "Pathological anatomy of the kidney in COVID-19 infection"),
    6: ("Муйдинов Жавлонбек Иброхимович", None),
    7: ("Гистотопография врождённого дефекта мембранозной части межжелудочковой перегородки сердца", "Histotopography of a congenital defect of the membranous part of the interventricular septum of the heart"),
    10: ("Абдувалиева Ферузахон Тулкинжановна", None),
    11: ("Эколого-гигиенические аспекты оптимизации водоснабжения населения (на примере города Ферганы)", "Ecological and hygienic aspects of optimizing the water supply of the population (using the city of Fergana as an example)"),
    14: ("Арабоев Хуршидбек Хусниддинович", None),
    15: ("Технология подготовки студентов медицинского образования к массовому оздоровлению методами кроссфита (на примере преподавания физической культуры и спорта)", "Technology of preparing medical students for mass health improvement through CrossFit methods (using the teaching of physical education and sports as an example)"),
    18: ("Хамдамова Шахноза Юсупалиевна", None),
    19: ("Технология развития профессиональных компетенций студентов на основе интеграционного подхода (на примере сопоставления английского и латинского языков в медицинском образовании)", "Technology for developing students' professional competence on the basis of an integrative approach (using the comparison of English and Latin in medical education as an example)"),
    22: ("Юнусова Рано Гайбуллаевна", None),
    23: ("«Совершенствование методики преподавания биофизики на основе проектирования в медицинском образовании»", "“Improving the methodology of teaching biophysics on the basis of design in medical education”"),
    26: ("Кахорова Турсиной Улугбек кизи", None),
    27: ("Технологии совершенствования методики использования 3D-интерактивных дидактических материалов в процессе медицинского образования (на примере преподавания английского языка)", "Technologies for improving the methodology of using 3D interactive didactic materials in the medical education process (using English language teaching as an example)"),
    30: ("Юлдошев Собитали Зохиджон угли", None),
    31: ("Методика развития валеологической компетентности будущих врачей посредством адаптивных технологий физического воспитания (на примере преподавания физической культуры и спорта)", "Methodology for developing the valeological competence of future doctors through adaptive technologies of physical education (using the teaching of physical education and sports as an example)"),
    34: ("Турдиев Шавкат Маъмирович", None),
    35: ("Интенсивные технологии развития профилактической компетентности студентов в медицинском образовании (на примере преподавания гигиены)", "Intensive technologies for developing students' preventive competence in medical education (using the teaching of hygiene as an example)"),
    38: ("Шаланков Константин Константинович", None),
    39: ("Педагогические условия организации самостоятельной деятельности студентов-медиков на занятиях по музыкальной терапии", "Pedagogical conditions for organizing the independent activity of medical students in music therapy classes"),
    42: ("Улмасов Зикрилло Обидович", None),
    43: ("Оценка эффективности сочетания «дочим» и гирудотерапии в лечении и профилактике грыжи межпозвонкового диска", "Evaluating the effectiveness of combining dochim and hirudotherapy in the treatment and prevention of intervertebral disc herniation"),
    46: ("Ядгарова Шаходат Солиховна", None),
    47: ("Гигиеническая характеристика сточных вод, образующихся от населения и промышленных предприятий (на примере города Бухары)", "Hygienic characterization of wastewater generated by the population and industrial enterprises (using the city of Bukhara as an example)"),
    50: ("Матхошимов Нодиржон Соибжонович", None),
    51: ("Профилактика инвалидности населения трудоспособного возраста (на примере Ферганской области)", "Prevention of disability among the working-age population (using the Fergana region as an example)"),
}
for order, (ru, en) in AVTO.items():
    set_all(S, order, ru=ru, en=en)

# ---- journal: five English titles that were Russian --------------------------------------------------------------------------------------------------------
JCPM = {
    ("jcpm-2024", 10): "Obtaining polyvalent serum against intestinal yersiniosis from experimental animals and studying its properties",
    ("jcpm-2024", 47): "Studying the relationship between thyroid pathologies and diseases of the reproductive system in women of childbearing age",
    ("jcpm-2025", 28): "Study of the antioxidant properties of medicinal plants of southern Fergana",
    ("jcpm-2025", 29): "The state of perinatal deaths in the Fergana region during 2024 and their characteristics",
    ("jcpm-2025", 41): "Modern methods of preventing purulent complications in children after abdominal surgery",
}
for (slug, order), en in JCPM.items():
    set_all(slug, order, en=en)

# ---- card titles ---------------------------------------------------------------------------------------------------------------------------------------
set_all("institut-yol-xaritasi-2025", 1, ru="Дорожная карта института – 2026", en="Institute roadmap – 2026")
set_all("abituriyentlar-uchun-talim-yonalishlari-va-institut-tarixi", 3, ru="Направления обучения для абитуриентов и история института")
set_all("institut-gazetasi-2025", 2, en="Institute newspaper-2025")

# ---- two news --------------------------------------------------------------------------------------------------------------------------------------------
news = api("news/xalqaro-hamkorlik-5/")
news = news.get("data", news)
page = {"slug": news["page"]["slug"], **{b["order"]: b for b in news["page"]["blocks"]}}
RU_GULF = ("Представители Gulf Medical University (ОАЭ) посетили наш вуз. Как вам известно, совместно с Gulf Medical University была организована 4-летняя совместная магистерская образовательная "
           "программа по специальности «Doctor of medicine» (терапия). В соответствии с ней предусматривается широкое внедрение в учебный процесс передовых педагогических технологий, учебных программ "
           "и учебно-методических материалов, основанных на международных образовательных стандартах, проведение мастер-классов для профессорско-преподавательского состава и студентов, а также "
           "активное привлечение высококвалифицированных преподавателей и учёных университета к курсам повышения квалификации. Сегодня в Ферганский медицинский институт общественного здоровья прибыли "
           "представители Gulf Medical University профессор Hossam Hamdy и Vinod Abraham. Их встретил ректор нашего вуза профессор Акмал Сидиков.")
assert page[1]["data"]["ru"]["text"].startswith("Representatives of the Gulf Medical Uni versity")
put(None, 1, "ru", "text", RU_GULF, page_slug=page)

pres_slug = "oʻzbekiston-respublikasi-prezidenti-shavkat-mirziyoyevning-oliy-majlis-va-oʻzbekiston-xalqiga-murojaatnomasi"
pres = api("news/%s/" % urllib.parse.quote(pres_slug))
pres = pres.get("data", pres)
ppage = {"slug": pres["page"]["slug"], **{b["order"]: b for b in pres["page"]["blocks"]}}
old = ppage[88]["data"]["en"]["text"]
assert "сreating" in old
put(None, 88, "en", "text", old.replace("сreating", "creating"), page_slug=ppage)

Path("deploy/content/yillik-hisobot-2026-110/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ops), "texts")
