"""Builds plan.json of script 52 (the page "Thumbay Fergana College of Medical Sciences", Institut yangiliklari) from the live page.
The old page was one English text (an advertising copy of the college) in all three languages and a duplicated list. Now: the three pictures, headings, paragraphs and one list as typed
blocks; the English text is kept for English and translated into Uzbek and Russian here (listed in tarjima-kerak.md); the "Apply Now" links lost their advertising parameters.
    python deploy/content/yillik-hisobot-2026-52/make_plan.py"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _plan_tools import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
SLUG = "thumbay-fergana-college-of-medical-sciences"
raw, documents = page_blocks(SLUG)
htmls = {lang: raw["data"][lang]["html"] for lang in LANGS}
lines = {lang: lines_of(htmls[lang]) for lang in LANGS}
pictures = images_of(htmls["uz"])
assert [p.rsplit("/", 1)[-1] for p in pictures] == ["Thumbay-2026.png", "tfcoms-5.jpg", "Thumbay Fergana.jpg"]
assert all(images_of(htmls[lang]) == pictures for lang in LANGS)
en = [l["text"] for l in lines["en"]]
assert en[1] == "A Game Changer in Medical Education" and en[24] == "$1 million investment"  # the English text is the source of the three languages
APPLY = "https://tfcoms.uz/"
ALT = {"uz": "Thumbay Fergana College of Medical Sciences", "ru": "Thumbay Fergana College of Medical Sciences", "en": "Thumbay Fergana College of Medical Sciences"}


def t(uz, ru, en):
    return {"uz": uz, "ru": ru, "en": en}


def heading(text):
    return block("heading", {lang: {"text": text[lang], "level": 2} for lang in LANGS})


def para(text):
    return block("paragraph", {lang: {"text": text[lang]} for lang in LANGS})


apply_top = t("[Ariza topshirish](https://tfcoms.uz/programs/)", "[Подать заявку](https://tfcoms.uz/programs/)", "[Apply Now](https://tfcoms.uz/programs/)")
apply_now = t("[Ariza topshirish](%s)" % APPLY, "[Подать заявку](%s)" % APPLY, "[Apply Now](%s)" % APPLY)
items_en = en[14:23]
assert items_en[0] == "More than 90 years of educational background" and items_en[-1] == "Safe community"
items = {
    "uz": ["90 yildan ortiq taʼlim tajribasi", "Yuqori malakali professor-oʻqituvchilar", "Kampus ichida yotoqxona va oshxona", "Hamkor shifoxonalarning yaxshi tarmogʻi",
           "Kompetensiyaga asoslangan tibbiy oʻquv dasturi", "Oʻqitish tili — ingliz tili", "Hamyonbop tibbiy taʼlim", "Hindiston, GCC mamlakatlari va BAAdan toʻgʻridan-toʻgʻri parvozlar",
           "Xavfsiz muhit"],
    "ru": ["Более 90 лет образовательных традиций", "Высококвалифицированный преподавательский состав", "Проживание в кампусе со столовой", "Развитая сеть клинических баз",
           "Компетентностно-ориентированная медицинская программа", "Язык обучения — английский", "Доступное медицинское образование", "Прямые рейсы из Индии, стран GCC и ОАЭ",
           "Безопасная среда"],
    "en": items_en,
}
blocks = [
    image_block(pictures[0], ALT),
    para(apply_top),
    image_block(pictures[1], ALT),
    heading(t("Tibbiy taʼlimni oʻzgartiruvchi loyiha", "Новое слово в медицинском образовании", en[1])),
    para(t("Thumbay Group bilan hamkorlikda Thumbay Fergana College of Medical Sciences (TFCOMS) tashkil etildi; u BAAdagi Gulf Medical University bilan akademik hamkorlikda faoliyat yuritadi.",
           "Сотрудничество с Thumbay Group по созданию Thumbay Fergana College of Medical Sciences в академическом партнёрстве с Gulf Medical University (ОАЭ).", en[2])),
    para(t("BAAda sogʻliqni saqlash va taʼlim sohasining yetakchisi boʻlgan Thumbay Group Oʻzbekistondagi nufuzli Fargʻona jamoat salomatligi tibbiyot instituti (FJSTI) bilan hamkorlikda Thumbay Fergana College of Medical Sciences kollejini tashkil etdi. Bu strategik hamkorlik jahon tibbiy taʼlimida muhim bosqich boʻlib, ikki yetakchi muassasaning tajriba va resurslarini birlashtirib, kelajak sogʻliqni saqlash mutaxassislari uchun oʻzgartiruvchi taʼlim muhitini yaratadi.",
           "Thumbay Group — пионер в сфере здравоохранения и образования в ОАЭ — в партнёрстве с авторитетным Ферганским медицинским институтом общественного здоровья (ФМИОЗ) в Узбекистане создала Thumbay Fergana College of Medical Sciences. Это стратегическое сотрудничество стало важной вехой в мировом медицинском образовании: оно объединяет опыт и ресурсы двух ведущих учреждений и создаёт преобразующую образовательную среду для будущих специалистов здравоохранения.",
           en[3])),
    heading(t("Taʼlim sifati global imkoniyatlar bilan uchrashadi", "Качество образования и глобальные возможности", en[4])),
    para(t("90 yildan ortiq tarixga ega Fargʻona tibbiyot instituti akademik mukammalligi va malakali sogʻliqni saqlash yetakchilarini tayyorlashga sodiqligi bilan mashhur. 19 ta kafedra, 147 nafar tajribali professor-oʻqituvchi hamda Hindiston, Qirgʻiziston va Nigeriya kabi mamlakatlardan kelgan xilma-xil talabalar jamoasiga ega FJSTI global qarashlarni boyituvchi koʻpmadaniyatli va inklyuziv muhitni taqdim etadi. Thumbay Group esa Gulf Medical University (GMU) orqali BAAdagi akademik sogʻliqni saqlash tizimi sifatidagi obroʻsini olib keladi: 102 millatga mansub 4000 dan ortiq bitiruvchi va dunyoning 90 dan ortiq muassasasi bilan hamkorlik.",
           "Ферганский медицинский институт с более чем 90-летней историей известен академическим совершенством и стремлением готовить компетентных лидеров здравоохранения. Имея 19 кафедр, 147 опытных преподавателей и разнообразное студенческое сообщество из таких стран, как Индия, Кыргызстан и Нигерия, ФМИОЗ создаёт мультикультурную и инклюзивную среду, расширяющую глобальный кругозор. Thumbay Group через Gulf Medical University (GMU) привносит репутацию академической системы здравоохранения ОАЭ: более 4000 выпускников из 102 стран и партнёрство с более чем 90 учреждениями мира.",
           en[5])),
    image_block(pictures[2], ALT),
    heading(t("Graduate Entry tibbiyot dasturi", "Программа Graduate Entry по медицине", en[6])),
    para(t("(Sogʻliqni saqlash va biologiya fanlari boʻyicha har qanday bitiruvchilar uchun)", "(Для выпускников любых направлений здравоохранения и биологических наук)", en[7])),
    para(t("Hamkorlik doirasida xalqaro standartlarga mos, toʻliq akkreditatsiyalangan Graduate Entry Doctor of Medicine (MD) dasturi taklif etiladi.",
           "В рамках сотрудничества предлагается программа Graduate Entry Doctor of Medicine (MD) — полностью аккредитованная программа, соответствующая международным стандартам.", en[8])),
    para(t("Toʻrt yillik dastur zamonaviy tibbiy texnologiyalar, faol oʻqitish usullari va turli sogʻliqni saqlash muassasalarida amaliy klinik tayyorgarlikni birlashtiradi. Sifat nazorati GMU tomonidan olib boriladi, bu jahon darajasidagi taʼlimni kafolatlaydi. Dastur muammoli va jamoaviy oʻqitishga, klinik amaliyotga erta jalb qilishga hamda talabalarni sogʻliqni saqlashdagi real muammolarga tayyorlaydigan zamonaviy simulyatsion mashgʻulotlarga urgʻu beradi.",
           "Четырёхлетняя программа объединяет передовые медицинские технологии, активные методы обучения и практическую клиническую подготовку в различных медицинских учреждениях. Контроль качества осуществляет GMU, что гарантирует образование мирового уровня. В программе делается упор на проблемно-ориентированное и командное обучение, раннее клиническое погружение и современное симуляционное обучение, готовящее студентов к реальным задачам здравоохранения.",
           en[9])),
    para(apply_now),
    heading(t("Xalqaro tibbiyot darajasi dasturi (Twinning)", "Международная программа по медицине (Twinning)", en[11])),
    para(t("Maktab bitiruvchilari uchun", "Для выпускников школ", en[12])),
    para(t("BAA, Ajmandagi Gulf Medical University’da 3 yil va Oʻzbekiston, Fargʻonadagi TFCOMS’da 3 yil", "3 года в Gulf Medical University (Аджман, ОАЭ) и 3 года в TFCOMS (Фергана, Узбекистан)", en[13])),
    block("list", {lang: {"items": items[lang]} for lang in LANGS}),
    para(apply_now),
    para(t("[1 million dollar investitsiya](/detail/1-million-dollar-investitsiya?menu_id=71)", "[Инвестиции в 1 миллион долларов](/detail/1-million-dollar-investitsiya?menu_id=71)", "[$1 million investment](/detail/1-million-dollar-investitsiya?menu_id=71)")),
    para(t("[Xalqaro hamkorlik](/detail/xalqaro-hamkorlik-14?menu_id=71)", "[Международное сотрудничество](/detail/xalqaro-hamkorlik-14?menu_id=71)", "[International cooperation](/detail/xalqaro-hamkorlik-14?menu_id=71)")),
    para(t("[Fargʻona jamoat salomatligi tibbiyot instituti va Gulf Medical University oʻrtasidagi hamkorlik](/detail/xalqaro-tashrif-xalqaro-xamkorlik-3?menu_id=71)",
           "[Сотрудничество Ферганского медицинского института общественного здоровья и Gulf Medical University](/detail/xalqaro-tashrif-xalqaro-xamkorlik-3?menu_id=71)",
           "[The cooperation between the Fergana Medical Institute of Public Health and the Gulf Medical University](/detail/xalqaro-tashrif-xalqaro-xamkorlik-3?menu_id=71)")),
]
card = captions_of_cards(documents, [t("Thumbay Fergana College of Medical Sciences: broshyura (2025-yil fevral)", "Thumbay Fergana College of Medical Sciences: брошюра (февраль 2025)",
                                       "Thumbay Fergana College of Medical Sciences: brochure (February 2025)")])
plan = [entry(SLUG, raw, blocks, card)]
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"], len(e["blocks"])) for e in plan])
