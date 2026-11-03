# Publishes the announcement about the national contest of the "Besh million sunʼiy intellekt yetakchilari" project
# ("Eng faol ishtirokchi" for students, "Eng faol oliy taʼlim tashkiloti" for universities) in the "E'lonlar" category:
# a short summary in uz/ru/en, the two infographics (student / university) shown in the text and as PDF downloads, and the
# joint decision of the ministries as a PDF. It goes through the SAME serializer the admin panel's news form uses.
#
# The ministry's covering letter with the rector's internal resolution is NOT published (names and a deadline for staff).
# The PDFs here were cleaned of the recipient's faint "UZJ..." tracking watermark (it is an overlay on the page).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/news-2026-11-03-besh-million-ai/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/news-2026-11-03-besh-million-ai/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/news-2026-11-03-besh-million-ai/apply.py   (deletes what apply made)
#
# dry (default) only shows; apply stops if the post already exists, so a second run changes nothing.
import os
import shutil

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from rest_framework.parsers import JSONParser
from rest_framework.request import Request
from rest_framework.test import APIRequestFactory

from apps.admin_api.common import resolve_or_create_image
from apps.admin_api.news_views import AdminPostSerializer
from apps.content.models import ContentBlock
from apps.media_lib.models import Document, Image
from apps.news.models import NewsCategory, NewsPost

MODE = os.environ.get("MODE", "dry")
SLUG = "besh-million-suniy-intellekt-yetakchilari-milliy-tanlov-2026"
CATEGORY_SLUG = "elonlar"
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "news-2026-11-03-besh-million-ai")
SUBDIR = "uploads/2026/11"
DEST_DIR = os.path.join(settings.MEDIA_ROOT, SUBDIR)

STUDENT_JPG = "ai-yetakchilari-talabalar-uchun-poster.jpg"
OTM_JPG = "ai-yetakchilari-otm-uchun-poster.jpg"
STUDENT_PDF = "ai-yetakchilari-talabalar-uchun-poster.pdf"
OTM_PDF = "ai-yetakchilari-otm-uchun-poster.pdf"
DECISION_PDF = "ai-yetakchilari-qoshma-qaror-2026-01-16.pdf"
FILES = [STUDENT_JPG, OTM_JPG, STUDENT_PDF, OTM_PDF, DECISION_PDF]

IMAGE_ALT = {
    STUDENT_JPG: {
        "uz": "“Talabalar uchun” infografika: faol boʻling — noutbuk yutib oling",
        "ru": "Инфографика «Для студентов»: будьте активны — выиграйте ноутбук",
        "en": "Infographic “For students”: be active — win a laptop",
    },
    OTM_JPG: {
        "uz": "“OTM uchun” infografika: Eng faol oliy taʼlim tashkiloti — jami mukofot 435 BHM",
        "ru": "Инфографика «Для вузов»: самая активная образовательная организация — общий призовой фонд 435 БРВ",
        "en": "Infographic “For universities”: most active higher education institution — total prizes of 435 BCV",
    },
}
# captions of the three downloads, per language (a document block carries one caption per language)
DOC_CAPTIONS = {
    STUDENT_PDF: {
        "uz": "“Talabalar uchun” infografika (PDF)",
        "ru": "Инфографика «Для студентов» (PDF)",
        "en": "Infographic “For students” (PDF)",
    },
    OTM_PDF: {
        "uz": "“OTM uchun” infografika (PDF)",
        "ru": "Инфографика «Для вузов» (PDF)",
        "en": "Infographic “For universities” (PDF)",
    },
    DECISION_PDF: {
        "uz": "Qoʻshma qaror: tanlovlarni tashkil etish va faol ishtirokchilarni ragʻbatlantirish tizimi (2026-yil 16-yanvar, PDF)",
        "ru": "Совместное решение: организация конкурсов и система поощрения активных участников (16 января 2026 года, PDF)",
        "en": "Joint decision: organising the contests and rewarding active participants (16 January 2026, PDF)",
    },
}

TITLE = {
    "uz": "“Besh million sunʼiy intellekt yetakchilari” loyihasi: faol talabalar va oliy taʼlim tashkilotlari uchun milliy tanlov",
    "ru": "Проект «Пять миллионов лидеров искусственного интеллекта»: национальный конкурс для активных студентов и вузов",
    "en": "“Five Million AI Leaders” project: national contest for active students and universities",
}
EXCERPT = {
    "uz": "Eng faol 250 nafar talaba noutbuk, planshet, aqlli soat kabi sovgʻalar bilan, eng faol 3 ta oliy taʼlim tashkiloti esa jami 435 BHM pul mukofoti bilan taqdirlanadi. Shartlar va hujjatlar — ichida.",
    "ru": "250 самых активных студентов получат ноутбуки, планшеты, умные часы и другие подарки, а три самых активных вуза — денежные премии на 435 БРВ. Условия и документы — внутри.",
    "en": "The 250 most active students win laptops, tablets, smartwatches and other gifts; the 3 most active universities share cash prizes worth 435 BCV. Rules and documents inside.",
}

# One block structure for all three languages (the admin pairs the languages block by block), so every list below
# has the same number of items in uz, ru and en.
TEXT = {
    "uz": {
        "intro": "“Besh million sunʼiy intellekt yetakchilari” loyihasi doirasida har yili milliy tanlov oʻtkaziladi: “Eng faol ishtirokchi” nominatsiyasida faol talabalar qimmatbaho sovgʻalar bilan, “Eng faol oliy taʼlim tashkiloti” nominatsiyasida esa eng yuqori natijaga erishgan 3 ta oliy taʼlim tashkiloti pul mukofoti bilan taqdirlanadi. Tanlov shartlari Taʼlim va ilm-fan vazirligi hamda Raqamli texnologiyalar vazirligi tayyorlagan ikkita infografikada bayon etilgan (vazirlikning 2026-yil 23-oktabrdagi 04-241-son xati). Quyida ularning qisqacha mazmuni va yuklab olish uchun hujjatlar keltirilgan.",
        "h_students": "Talabalar uchun: faol boʻling — noutbuk yutib oling",
        "students_prizes": "Har yili eng faol 250 nafar talaba sovgʻalar bilan taqdirlanadi: 100 ta noutbuk (qiymati 20 BHMgacha), 30 ta planshet (10 BHMgacha), 30 ta aqlli soat (3 BHMgacha), 60 ta platforma litsenziyasi (2 BHMgacha) va 30 ta kitob vaucheri (1 BHMgacha). BHM — bazaviy hisoblash miqdori. Eng yuqori ball toʻplaganlarga avval noutbuk, keyingilarga planshet, aqlli soat, litsenziya va vaucher beriladi. “Eng faol ishtirokchi” nominatsiyasi gʻoliblari soni har bir hududdan 72 nafardan oshmaydi.",
        "how": "Qanday qatnashiladi:",
        "steps": [
            "aileaders.uz platformasida shaxsan roʻyxatdan oʻting;",
            "platformadagi Courseraning 5 ta bepul onlayn kursini tugating;",
            "sertifikat, ish va olimpiadalar orqali 100 ballgacha toʻplang.",
        ],
        "points": "Ballar qanday beriladi:",
        "point_items": [
            "Xorijiy til sertifikati — 30 ballgacha: B2 daraja — 15, C1 va yuqori — 30 (tan olingan roʻyxatdagi, amal qilish muddati oʻtmagan sertifikatlar hisobga olinadi);",
            "AT (axborot texnologiyalari) sohasida ishga joylashish — 30 ballgacha: AT sohasida — 15, AT xizmatlarini eksport qiluvchi kompaniyada — 30;",
            "Xalqaro olimpiada va tanlovlar — 40 ballgacha: ICPC mintaqaviy bosqich — 20, ICPC final — 30, gʻolib (ICPC finalida yuqori oʻrin yoki President Tech Award, AI Xakaton, AI Award, Zulfiya mukofoti gʻolibi) — 40.",
        ],
        "example": "Misol: C1 darajadagi xorijiy til sertifikati (30) + AT sohasida ishga joylashish (15) + ICPC mintaqaviy bosqichiga chiqish (20) = 65 ball. Agar AT xizmatlarini eksport qiluvchi kompaniyada ishlasa — 30 ball, jami 80 ball.",
        "deadline": "<strong>Muddat:</strong> natijalar har kalendar yil boʻyicha hisoblanadi, gʻoliblar keyingi yilning I choragida eʼlon qilinadi. Eʼlondan soʻng 3 kalendar kuni ichida qayta koʻrib chiqish uchun ariza berish mumkin; arizalar 5 ish kunida koʻrib chiqiladi.",
        "warning": "<strong>Diqqat!</strong> Ishtirokchi nomidan ruxsatsiz roʻyxatdan oʻtish, uning nomiga sertifikat rasmiylashtirish va hujjatlarni soxtalashtirish natijalar bekor qilinishiga sabab boʻladi.",
        "h_otm": "Oliy taʼlim tashkilotlari rahbariyati uchun: “Eng faol oliy taʼlim tashkiloti” — jami mukofot 435 BHM",
        "otm_prizes": "Har yili eng yuqori ball toʻplagan 3 ta oliy taʼlim tashkiloti pul mukofoti bilan taqdirlanadi: 1-oʻrin — 250 BHM, 2-oʻrin — 125 BHM, 3-oʻrin — 60 BHM. Natijalar 5 ta koʻrsatkich boʻyicha 100 ballik tizimda baholanadi (O1 + O2 + O3 + O4 + O5).",
        "otm_items": [
            "O1 — platformada bepul kurslarni tamomlagan talabalar ulushi (OTMdagi barcha talabalarga nisbatan) — 30 ball;",
            "O2 — xorijiy til sertifikatiga ega (B2 va undan yuqori, muddati oʻtmagan) AT talabalari ulushi — 20 ball;",
            "O3 — xorijiy til sertifikatiga ega AT pedagoglari ulushi — 15 ball;",
            "O4 — AT yoʻnalishi boʻyicha ishga joylashgan bitiruvchilar ulushi (RTV tizimi va IT Park rezidentlarida) — 20 ball;",
            "O5 — ICPC, President Tech Award, AI Xakaton, AI Award yutuqlari va Zulfiya mukofoti gʻoliblari — 15 ball.",
        ],
        "otm_share": "Ulush oshgani sari ball ham oshadi. Masalan, O1 boʻyicha kurslarni tugatganlar ulushi 5–25% boʻlsa — 5 ball, 26–55% boʻlsa — 10, 56–75% boʻlsa — 20, 76% va undan yuqori boʻlsa — 30 ball. Ulush 5% dan kam boʻlsa — 0 ball.",
        "otm_warning": "<strong>Diqqat!</strong> O1 — eng katta koʻrsatkich: 30 ball uchun OTMdagi barcha talabalarning kamida 76 foizi kurslarni tugatishi kerak.",
        "h_docs": "Hujjatlar va infografikalar",
    },
    "ru": {
        "intro": "В рамках проекта «Пять миллионов лидеров искусственного интеллекта» ежегодно проводится национальный конкурс: в номинации «Самый активный участник» активные студенты награждаются ценными подарками, а в номинации «Самая активная образовательная организация высшего образования» три вуза с наивысшими результатами получают денежные премии. Условия конкурса изложены в двух инфографиках, подготовленных Министерством образования и науки совместно с Министерством цифровых технологий (письмо министерства от 23 октября 2026 года № 04-241). Ниже — краткое содержание и документы для скачивания.",
        "h_students": "Для студентов: будьте активны — выиграйте ноутбук",
        "students_prizes": "Ежегодно 250 самых активных студентов награждаются подарками: 100 ноутбуков (стоимостью до 20 БРВ), 30 планшетов (до 10 БРВ), 30 умных часов (до 3 БРВ), 60 лицензий на платформу (до 2 БРВ) и 30 книжных ваучеров (до 1 БРВ). БРВ — базовая расчётная величина. Участникам с наивысшими баллами сначала достаются ноутбуки, затем планшеты, умные часы, лицензии и ваучеры. Число победителей номинации «Самый активный участник» от каждого региона не превышает 72.",
        "how": "Как участвовать:",
        "steps": [
            "лично зарегистрируйтесь на платформе aileaders.uz;",
            "пройдите 5 бесплатных онлайн-курсов Coursera на платформе;",
            "наберите до 100 баллов за сертификаты, работу и олимпиады.",
        ],
        "points": "Как начисляются баллы:",
        "point_items": [
            "Сертификат по иностранному языку — до 30 баллов: уровень B2 — 15, C1 и выше — 30 (учитываются сертификаты из списка признанных, срок действия которых не истёк);",
            "Трудоустройство в сфере ИТ (информационных технологий) — до 30 баллов: в сфере ИТ — 15, в компании, экспортирующей ИТ-услуги, — 30;",
            "Международные олимпиады и конкурсы — до 40 баллов: региональный этап ICPC — 20, финал ICPC — 30, победитель (высокое место в финале ICPC или победа в President Tech Award, AI Хакатон, AI Award, премии «Зулфия») — 40.",
        ],
        "example": "Пример: сертификат по иностранному языку уровня C1 (30) + трудоустройство в сфере ИТ (15) + выход в региональный этап ICPC (20) = 65 баллов. Если работа в компании, экспортирующей ИТ-услуги, — 30 баллов, итого 80.",
        "deadline": "<strong>Сроки:</strong> результаты подводятся за каждый календарный год, победители объявляются в I квартале следующего года. В течение 3 календарных дней после объявления можно подать заявление на пересмотр; заявления рассматриваются в течение 5 рабочих дней.",
        "warning": "<strong>Внимание!</strong> Регистрация от имени участника без его разрешения, оформление на его имя сертификатов и подделка документов приведут к аннулированию результатов.",
        "h_otm": "Для руководства вузов: «Самая активная образовательная организация высшего образования» — общий призовой фонд 435 БРВ",
        "otm_prizes": "Ежегодно три вуза, набравшие наибольшее количество баллов, награждаются денежными премиями: 1 место — 250 БРВ, 2 место — 125 БРВ, 3 место — 60 БРВ. Результаты оцениваются по 5 показателям по 100-балльной системе (О1 + О2 + О3 + О4 + О5).",
        "otm_items": [
            "О1 — доля студентов, прошедших бесплатные курсы на платформе (от всех студентов вуза) — 30 баллов;",
            "О2 — доля студентов ИТ-направлений с сертификатом по иностранному языку (B2 и выше, срок не истёк) — 20 баллов;",
            "О3 — доля преподавателей ИТ-направлений с сертификатом по иностранному языку — 15 баллов;",
            "О4 — доля выпускников, трудоустроенных по ИТ-направлению (в системе RTV и у резидентов IT Park) — 20 баллов;",
            "О5 — призёры ICPC, President Tech Award, AI Хакатон, AI Award и лауреаты премии «Зулфия» — 15 баллов.",
        ],
        "otm_share": "Чем выше доля, тем больше баллов. Например, по О1: доля прошедших курсы 5–25% — 5 баллов, 26–55% — 10, 56–75% — 20, 76% и выше — 30 баллов. Если доля менее 5% — 0 баллов.",
        "otm_warning": "<strong>Внимание!</strong> О1 — самый крупный показатель: чтобы получить 30 баллов, курсы должны пройти не менее 76% всех студентов вуза.",
        "h_docs": "Документы и инфографики",
    },
    "en": {
        "intro": "A national contest is held every year within the “Five Million AI Leaders” project: in the “Most active participant” nomination active students win valuable gifts, and in the “Most active higher education institution” nomination the 3 universities with the best results receive cash prizes. The rules are set out in two infographics prepared by the Ministry of Education and Science together with the Ministry of Digital Technologies (the ministry’s letter no. 04-241 of 23 October 2026). Below are a short summary and the documents to download.",
        "h_students": "For students: be active — win a laptop",
        "students_prizes": "Every year the 250 most active students receive gifts: 100 laptops (worth up to 20 BCV), 30 tablets (up to 10 BCV), 30 smartwatches (up to 3 BCV), 60 platform licences (up to 2 BCV) and 30 book vouchers (up to 1 BCV). BCV is the base calculation value. The top scorers get the laptops first, then tablets, smartwatches, licences and vouchers. The number of winners in the “Most active participant” nomination does not exceed 72 per region.",
        "how": "How to take part:",
        "steps": [
            "register in person on the aileaders.uz platform;",
            "complete 5 free online Coursera courses on the platform;",
            "earn up to 100 points through certificates, employment and olympiads.",
        ],
        "points": "How points are awarded:",
        "point_items": [
            "Foreign language certificate — up to 30 points: level B2 — 15, C1 and above — 30 (certificates from the recognised list that have not expired count);",
            "IT (information technology) employment — up to 30 points: in IT — 15, at a company that exports IT services — 30;",
            "International olympiads and contests — up to 40 points: ICPC regional round — 20, ICPC final — 30, winner (a top place in the ICPC final, or a winner of President Tech Award, AI Hackathon, AI Award or the Zulfiya prize) — 40.",
        ],
        "example": "Example: a C1 foreign language certificate (30) + IT employment (15) + reaching the ICPC regional round (20) = 65 points. If the employer is a company exporting IT services — 30 points, 80 in total.",
        "deadline": "<strong>Deadlines:</strong> results are counted for each calendar year and the winners are announced in the first quarter of the next year. Within 3 calendar days after the announcement you can apply for a review; applications are reviewed within 5 working days.",
        "warning": "<strong>Attention!</strong> Registering on a participant’s behalf without permission, obtaining certificates in their name and forging documents lead to the results being cancelled.",
        "h_otm": "For university management: “Most active higher education institution” — total prizes of 435 BCV",
        "otm_prizes": "Every year the 3 universities with the highest scores receive cash prizes: 1st place — 250 BCV, 2nd place — 125 BCV, 3rd place — 60 BCV. Results are scored on a 100-point scale across 5 indicators (O1 + O2 + O3 + O4 + O5).",
        "otm_items": [
            "O1 — share of students who completed the free courses on the platform (out of all students of the university) — 30 points;",
            "O2 — share of IT students with a foreign language certificate (B2 or higher, not expired) — 20 points;",
            "O3 — share of IT teaching staff with a foreign language certificate — 15 points;",
            "O4 — share of graduates employed in IT (in the RTV system and at IT Park residents) — 20 points;",
            "O5 — winners of ICPC, President Tech Award, AI Hackathon, AI Award and Zulfiya prize laureates — 15 points.",
        ],
        "otm_share": "The higher the share, the more points. For example, for O1: 5–25% of students completed the courses — 5 points, 26–55% — 10, 56–75% — 20, 76% and above — 30 points. A share below 5% scores 0 points.",
        "otm_warning": "<strong>Attention!</strong> O1 is the largest indicator: to get 30 points, at least 76% of all the university’s students must complete the courses.",
        "h_docs": "Documents and infographics",
    },
}


def html_of(lang):
    t = TEXT[lang]
    img = lambda name: '<p><img src="/media/%s/%s" alt="%s" /></p>' % (SUBDIR, name, IMAGE_ALT[name][lang])
    li = lambda items: "".join("<li>%s</li>" % item for item in items)
    parts = [
        "<p>%s</p>" % t["intro"],
        "<h3>%s</h3>" % t["h_students"],
        "<p>%s</p>" % t["students_prizes"],
        "<p><strong>%s</strong></p>" % t["how"],
        "<ol>%s</ol>" % li(t["steps"]),
        "<p><strong>%s</strong></p>" % t["points"],
        "<ul>%s</ul>" % li(t["point_items"]),
        "<p>%s</p>" % t["example"],
        "<p>%s</p>" % t["deadline"],
        "<p>%s</p>" % t["warning"],
        # (the student infographic is the post's cover, shown at the top of the page, so it is not repeated here)
        "<h3>%s</h3>" % t["h_otm"],
        "<p>%s</p>" % t["otm_prizes"],
        "<ul>%s</ul>" % li(t["otm_items"]),
        "<p>%s</p>" % t["otm_share"],
        "<p>%s</p>" % t["otm_warning"],
        img(OTM_JPG),
        "<h3>%s</h3>" % t["h_docs"],
    ]
    if lang == "uz":
        # new-document markers: the admin turns each into a "document" block (a download card) at this spot;
        # only the Uzbek text carries them, the card is shared by all three languages
        for name in (STUDENT_PDF, OTM_PDF, DECISION_PDF):
            parts.append(
                '<div data-new-document="/media/%s/%s" data-title="%s">%s</div>' % (SUBDIR, name, DOC_CAPTIONS[name]["uz"], DOC_CAPTIONS[name]["uz"])
            )
    return "".join(parts)


def hand_to_www_data(paths):
    if os.geteuid() != 0:  # the site runs as www-data; never leave root-owned media behind
        return
    import grp
    import pwd

    uid, gid = pwd.getpwnam("www-data").pw_uid, grp.getgrnam("www-data").gr_gid
    for path in paths:
        os.chown(path, uid, gid)


print("MODE:", MODE)
existing = NewsPost.objects.filter(slug=SLUG).first()
stored = {name: "%s/%s" % (SUBDIR, name) for name in FILES}

if MODE == "remove":
    if existing is None:
        raise SystemExit("Nothing to remove: the post is not there.")
    page = existing.page
    images = list(Image.objects.filter(file__in=[stored[STUDENT_JPG], stored[OTM_JPG]]))
    documents = list(Document.objects.filter(file__in=[stored[n] for n in (STUDENT_PDF, OTM_PDF, DECISION_PDF)]))
    with transaction.atomic():
        existing.delete()
        page.delete()  # its blocks (images, document cards) go with it
        for row in images + documents:
            row.delete()
    for name in FILES:
        path = os.path.join(settings.MEDIA_ROOT, stored[name])
        if os.path.isfile(path):
            os.remove(path)
    print("REMOVED the post, its page, the 2 pictures and the 3 PDFs (the category '%s' is left in place)." % CATEGORY_SLUG)
else:
    category = NewsCategory.objects.filter(slug=CATEGORY_SLUG).first()
    missing = [name for name in FILES if not os.path.isfile(os.path.join(SRC_DIR, name))]
    if missing:
        raise SystemExit("STOP: files missing (git pull first?): %s. Nothing was modified." % ", ".join(missing))
    if category is None:
        raise SystemExit("STOP: category '%s' not found. Nothing was modified." % CATEGORY_SLUG)
    if existing is not None:
        raise SystemExit("The post already exists (id %s): %s. Nothing was modified." % (existing.pk, SLUG))
    print("category:", category.name_uz)
    for lang in ("uz", "ru", "en"):
        print("title %s: %s" % (lang, TITLE[lang]))
    print("uz html:", len(html_of("uz")), "chars | ru:", len(html_of("ru")), "| en:", len(html_of("en")))
    if MODE != "apply":
        print("DRY RUN: nothing was created. Run again with MODE=apply to publish.")
    else:
        os.makedirs(DEST_DIR, exist_ok=True)
        copied = [DEST_DIR]
        for name in FILES:
            dest = os.path.join(DEST_DIR, name)
            shutil.copyfile(os.path.join(SRC_DIR, name), dest)
            copied.append(dest)
        hand_to_www_data(copied)
        with transaction.atomic():
            # the pictures need Image rows before the text can point at them
            for name in (STUDENT_JPG, OTM_JPG):
                image = resolve_or_create_image(stored[name])
                image.alt_text = IMAGE_ALT[name]["uz"]
                image.save(update_fields=["alt_text"])
            payload = {
                "title_uz": TITLE["uz"], "title_ru": TITLE["ru"], "title_en": TITLE["en"],
                "content_uz": html_of("uz"), "content_ru": html_of("ru"), "content_en": html_of("en"),
                "slug": SLUG, "category_id": category.pk, "status": 1,
                "date": timezone.now().isoformat(),
                "img": stored[STUDENT_JPG],
            }
            request = Request(APIRequestFactory().post("/api/v1/admin/news", payload, format="json"), parsers=[JSONParser()])
            serializer = AdminPostSerializer(data=payload, context={"request": request})
            serializer.is_valid(raise_exception=True)
            post = serializer.save()
            post.excerpt_uz, post.excerpt_ru, post.excerpt_en = EXCERPT["uz"], EXCERPT["ru"], EXCERPT["en"]
            post.save(update_fields=["excerpt_uz", "excerpt_ru", "excerpt_en"])
            # the pictures carry one description (alt text) per language
            for block in ContentBlock.objects.filter(page=post.page, block_type="image"):
                image = Image.objects.get(pk=block.data["uz"]["image_id"])
                alts = next((a for name, a in IMAGE_ALT.items() if image.file.name == stored[name]), None)
                if alts:
                    for lang in ("uz", "ru", "en"):
                        block.data[lang]["alt"] = alts[lang]
                    block.save(update_fields=["data"])
            # the download cards carry one caption per language
            for block in ContentBlock.objects.filter(page=post.page, block_type="document"):
                document = Document.objects.get(pk=block.data["uz"]["document_id"])
                captions = next((c for name, c in DOC_CAPTIONS.items() if document.file.name == stored[name]), None)
                if captions:
                    for lang in ("uz", "ru", "en"):
                        block.data[lang]["caption"] = captions[lang]
                    block.save(update_fields=["data"])
        print("DONE. Post id", post.pk, "|", post.published_at, "| https://fermi.uz/detail/%s" % post.slug)
        print("(the site shows it within about a minute; edit or delete it later in the admin panel: Yangiliklar)")
