"""Builds plan.json from the database AFTER scripts 39-77 (read-only):
    python manage.py shell < deploy/content/yillik-hisobot-2026-78/make_plan.py
Every correction is "in this block, in this language, this exact wording becomes that wording". The corrections come from two independent reviewers who read
the Russian and English texts against the Uzbek (findings checked one by one before they were taken over), plus the obvious typos of the Uzbek source."""
import json
from pathlib import Path

from apps.content.models import Page

OUT = Path("deploy/content/yillik-hisobot-2026-78/plan.json")
TECH = "tibbiyot-texnikumi-biturvchilarini-qabul-qilish-nizomi"
YOSH = "yoshlar-bilan-ishlash-manaviyat-va-marifat-bolimi"
REG = "registrator-ofisi"
BUX = "buxgalteriya-bolimi"
QN = "qabul-nizomi"
YOR = "bakalavriat-uchun-yoriqnoma"
# (slug, block order, lang, old wording, new wording, why)
FIXES = [
    (TECH, 18, "en", "a document on graduation from the technical college and a copy of its appendix.", "a copy of the document on graduation from the technical college and of its appendix.", "the Uzbek (and the Russian) ask for a copy of both"),
    (TECH, 49, "en", "institution one day after the interview process", "institution within one day after the interview process", "'bir kun muddatda' is a deadline"),
    (TECH, 47, "ru", "в подчинённое министерство или ведомство", "в министерство или ведомство, которому подчинено высшее образовательное учреждение", "the ministry the institution is subordinate to"),
    (TECH, 23, "en", "a highly qualified teacher of the technical college", "a qualified teacher of the technical college", "'malakali' = qualified"),
    (TECH, 50, "uz", "tomonlarning hududlari va majburiyatlari", "tomonlarning huquqlari va majburiyatlari", "typo of the Uzbek source (hududlari = territories); ru and en already say rights"),
    (YOR, 2, "ru", "Порядок приёма на программы бакалавриата", "Приём на программы бакалавриата", "a procedure is not 'carried out'"),
    (YOSH, 2, "en", "Preparing young specialists at the student level for participation in domestic and foreign policy;", "Training young specialists of the required standard for the country’s domestic and foreign policy;", "'talab darajasidagi' = of the required level"),
    (YOSH, 2, "ru", "Совершенствование систематической духовно-нравственной работы.", "Совершенствование адресной духовно-нравственной работы.", "'manzillashgan' = targeted"),
    (YOSH, 2, "en", "Improving systematic moral and spiritual work.", "Improving targeted moral and spiritual work.", "'manzillashgan' = targeted"),
    (YOSH, 2, "en", "injustice, showmanship, corruption, nepotism, and localism;", "injustice, window-dressing, bribery, nepotism, and localism;", "koʻzboʻyamachilik = window-dressing, poraxoʻrlik = bribery"),
    (YOSH, 2, "ru", "несправедливость, показушничество, коррупция, кумовство, локализм;", "несправедливость, очковтирательство, взяточничество, кумовство, местничество;", "'локализм' is not a Russian term; exact equivalents"),
    (YOSH, 2, "ru", "Воспитание у студентов отношения к национальным, семейным, соседским, общинным и общественно-гражданским обязанностям;", "Воспитание у студентов осознания своего долга перед нацией, семьёй, родителями, соседями, махаллёй и народом;", "the duty to parents (ota-ona) was missing"),
    (YOSH, 2, "en", "D-eveloping the student’s personal and individual qualities;", "Developing and improving the student’s personal and individual qualities;", "typo; 'takomillashtirish' was dropped"),
    (YOSH, 3, "ru", "Задачи- отдела по работе с молодежью, духовного и просветительского воспитания:", "Задачи отдела по работе с молодёжью, духовности и просвещения:", "stray hyphen; the department name"),
    (REG, 7, "en", "creating clearance (obkhodnoy) sheets for graduating students;", "creating clearance sheets for graduating students;", "a Russian transliteration was left in the English"),
    (REG, 11, "ru", "регистрация иностранных студентов и прикрепление к учебным дисциплинам;", "регистрация в электронной системе иностранных студентов, зачисленных на обучение, и прикрепление их к учебным дисциплинам;", "'elektron tizimda' and 'qabul qilingan' were missing"),
    (REG, 2, "en", "decisions and orders of the Ministry of Higher Education, Science and Innovation and the Ministry of Health", "decisions of the Boards and orders of the Ministry of Higher Education, Science and Innovation and the Ministry of Health", "the Boards (Hayʻat) were missing; the Russian keeps them"),
    # the link to HEMIS: the text had a typo (fsjti) and the address pointed to the HEMIS of another university (samdu); the Institute's is hemis.fjsti.uz
    (REG, 2, "uz", "[https://hemis.fsjti.uz/](https://hemis.samdu.uz/)", "[https://hemis.fjsti.uz/](https://hemis.fjsti.uz/)", "the link led to another university's HEMIS; the text had a typo"),
    (REG, 2, "uz", "unversitetning", "universitetning", "typo of the Uzbek source"),
    (REG, 2, "ru", "https://hemis.fsjti.uz/", "https://hemis.fjsti.uz/", "typo: this address does not exist"),
    (REG, 2, "en", "https://hemis.fsjti.uz/", "https://hemis.fjsti.uz/", "typo: this address does not exist"),
    (BUX, 1, "ru", "бухгалтерия Института также может вести бухгалтерский учёт в журнально-ордерной форме.", "бухгалтерия Института ведёт бухгалтерский учёт в журнально-ордерной форме.", "the Uzbek states a fact; 'может' had been added"),
    (BUX, 1, "en", "accounting may also be conducted in the journal-order form.", "the Institute’s accounting department keeps its accounts in the journal-order form.", "the Uzbek states a fact; 'may' had been added"),
    (BUX, 5, "ru", "Контроль правильного использования фонда оплаты труда в соответствии с утверждённым штатным расписанием;", "Обеспечение правильного использования фонда оплаты труда на основании утверждённых штатных расписаний и штатных формуляров;", "'shtat formulyarlari' was missing"),
    (BUX, 5, "en", "Ensuring proper use of the payroll fund in accordance with approved staffing schedules;", "Ensuring proper use of the payroll fund on the basis of the approved staffing schedules and staffing forms;", "'shtat formulyarlari' was missing"),
    (QN, 53, "ru", "и документ о военной службе предъявляются", "и документ об отношении к воинской обязанности предъявляются", "the document on the relation to military service (military registration)"),
    (QN, 53, "en", "and the document on military service in person", "and the military registration document in person", "the document on the relation to military service"),
    (QN, 21, "en", "foreign languages other than English, German or French were taught without English, German or French,", "other foreign languages were taught instead of English, German or French,", "a garbled duplication"),
    (QN, 86, "ru", "не добравших до утверждённой границы квот приёма по платно-контрактной основе до одного балла", "которым до утверждённой границы квот приёма на платно-контрактной основе не хватает до одного балла", "grammar ('на … основе') and wording"),
    (QN, 29, "uz", "3-ilovadabelgilangan", "3-ilovada belgilangan", "a missing space in the Uzbek source"),
    (QN, 91, "uz", "Manbaa:", "Manba:", "typo of the Uzbek source"),
]


def items(data):
    return list(data["items"]) if "items" in data else [data.get("text", "")]


entries = []
for slug, order, lang, old, new, why in FIXES:
    block = Page.objects.get(slug=slug).blocks.get(order=order)
    found = sum(item.count(old) for item in items(block.data[lang]))
    assert found == 1, (slug, order, lang, old[:50], found)
    assert block.block_type in ("heading", "paragraph", "list"), (slug, order, block.block_type)
    anchor = items(block.data["uz"])[0][:30]
    entries.append({"slug": slug, "order": order, "lang": lang, "anchor": anchor, "old": old, "new": new, "why": why})
OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections in", len({(e["slug"], e["order"]) for e in entries}), "blocks ->", OUT)
