"""One-off script: publishes the "Startap loyihalar - 2026" / iShifo open
contest call as a NewsPost in the "tanlovlar" category, through the same
Page/ContentBlock/Image pipeline the admin panel's own news form uses (see
apps/admin_api/news_views.py). The poster graphic is read from
/tmp/ishifo-photo (transferred separately, same as every other one-off
photo upload this project has done -- media stays out of git history).
All uz text uses U+02BB for o'/g'.

Submissions land through the "Ariza topshirish" form that detail/page.tsx
already renders automatically for any post in this category (see
apps.forms.models.ContestSubmission) -- no further wiring needed once this
post exists.

    set -a; source /etc/fermi-django.env; set +a
    .venv/bin/python _tmp_news_upload3/create_ishifo_contest_news.py
"""
import os
import sys

import django

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.files import File
from django.utils import timezone

from apps.content.admin_content import write_blocks_from_html
from apps.content.models import Page
from apps.media_lib.models import Image
from apps.news.models import NewsCategory, NewsPost

PHOTO_DIR = "/tmp/ishifo-photo"
COVER_FILE = "poster.webp"
ALT_TEXT = "“iShifo” loyihasi — “Startap loyihalar – 2026” tanlovi eʼloni"

SLUG = "ishifo-startap-loyihalar-2026-tanlovi"

TITLE_UZ = "“Startap loyihalar – 2026” tanlovi doirasida “iShifo” loyihasini yaratish boʻyicha ochiq tanlov eʼlon qilindi"
TITLE_RU = "Объявлен открытый конкурс на разработку проекта «iShifo» в рамках программы «Стартап-проекты – 2026»"
TITLE_EN = "Open Call Announced for the “iShifo” Project Under the “Startup Projects – 2026” Program"

EXCERPT_UZ = (
    "Institut sunʼiy intellekt yordamidagi masofaviy tibbiy konsultatsiya va tashxis tizimi — "
    "«iShifo»ni yaratish boʻyicha ochiq tanlov eʼlon qiladi. Takliflar 2026-yil 5-oktabrgacha qabul qilinadi."
)
EXCERPT_RU = (
    "Институт объявляет открытый конкурс на разработку системы дистанционных медицинских консультаций и "
    "диагностики с использованием ИИ — «iShifo». Заявки принимаются до 5 октября 2026 года."
)
EXCERPT_EN = (
    "The institute is holding an open call to build “iShifo”, an AI-assisted remote medical "
    "consultation and diagnostics system. Applications are accepted until October 5, 2026."
)

BODY_INTRO_UZ = (
    "Fargʻona jamoat salomatligi tibbiyot instituti sunʼiy intellekt yordamidagi masofaviy tibbiy konsultatsiya "
    "va tashxis tizimi — «iShifo»ni yaratish boʻyicha “Startap loyihalar – 2026” tanlovi "
    "doirasida ochiq tanlov eʼlon qiladi."
)
BODY_INTRO_RU = (
    "Ферганский медицинский институт общественного здоровья объявляет открытый конкурс на разработку системы "
    "дистанционных медицинских консультаций и диагностики с использованием искусственного интеллекта — "
    "«iShifo» — в рамках программы «Стартап-проекты – 2026»."
)
BODY_INTRO_EN = (
    "The Ferghana Medical Institute of Public Health is holding an open call, under its “Startup Projects – "
    "2026” program, to build “iShifo” — an AI-assisted remote medical consultation and "
    "diagnostics system."
)

GOAL_HEADING_UZ = "Loyiha maqsadi"
GOAL_HEADING_RU = "Цель проекта"
GOAL_HEADING_EN = "Project goal"

GOAL_UZ = (
    "Tuman va qishloq shifoxonalaridagi bemorni markaziy klinika tor mutaxassisi bilan video orqali bogʻlash va "
    "sunʼiy intellekt yordamida dastlabki tahlil berish, har bir konsultatsiyani hujjatlashtirish."
)
GOAL_RU = (
    "Связать пациента районной или сельской больницы со специалистом центральной клиники по видеосвязи и "
    "обеспечить предварительный анализ с помощью ИИ, документируя каждую консультацию."
)
GOAL_EN = (
    "Connect a patient at a district or rural hospital with a specialist at the central clinic over video, "
    "provide an initial AI-assisted analysis, and document every consultation."
)

TASKS_HEADING_UZ = "Ishlar tarkibi"
TASKS_HEADING_RU = "Состав работ"
TASKS_HEADING_EN = "Scope of work"

TASKS_UZ = [
    "Veb-interfeys va UI/UX dizayn (5 ta rol, 3 ta panel)",
    "Mobil va planshet moslashuvi",
    "Server qismi / REST API",
    "Video konsultatsiya (WebRTC, PTZ)",
    "Sunʼiy intellekt tahlili (4 bosqich)",
    "Maʼlumotlar bazasi, shifrlash, audit",
    "PDF hisobot va DICOM koʻruvchi",
    "Testlash va sifat nazorati",
]
TASKS_RU = [
    "Веб-интерфейс и UI/UX дизайн (5 ролей, 3 панели)",
    "Адаптация для мобильных устройств и планшетов",
    "Серверная часть / REST API",
    "Видеоконсультация (WebRTC, PTZ)",
    "Анализ на основе ИИ (4 этапа)",
    "База данных, шифрование, аудит",
    "PDF-отчёт и просмотр DICOM",
    "Тестирование и контроль качества",
]
TASKS_EN = [
    "Web interface and UI/UX design (5 roles, 3 panels)",
    "Mobile and tablet adaptation",
    "Server-side / REST API",
    "Video consultation (WebRTC, PTZ)",
    "AI analysis module (4 stages)",
    "Database, encryption, audit logging",
    "PDF reporting and DICOM viewer",
    "Testing and quality control",
]

REQ_HEADING_UZ = "Talablar"
REQ_HEADING_RU = "Требования"
REQ_HEADING_EN = "Who can apply"

REQ_UZ = (
    "Talabalar, oʻqituvchilar, kafedra jamoalari va spin-off tashkilotlar ishtirok etishi mumkin. Nomzodlar veb "
    "va tibbiy IT sohasida tajribaga, portfolio va narx (smeta) taklifiga, shuningdek kafolat va texnik "
    "qoʻllab-quvvatlash rejasiga ega boʻlishi kerak."
)
REQ_RU = (
    "В конкурсе могут участвовать студенты, преподаватели, коллективы кафедр и спин-офф организации. У "
    "участников должны быть опыт в сфере веб- и медицинских ИТ-решений, портфолио и ценовое предложение (смета), "
    "а также план гарантийного и технического сопровождения."
)
REQ_EN = (
    "Students, faculty members, department teams and spin-off organizations may all take part. Applicants "
    "should have experience in web and medical IT, a portfolio, a price proposal, and a warranty/technical "
    "support plan."
)

EVAL_HEADING_UZ = "Baholash mezonlari"
EVAL_HEADING_RU = "Критерии оценки"
EVAL_HEADING_EN = "Evaluation criteria"

EVAL_UZ = (
    "Takliflar quyidagi mezonlar boʻyicha baholanadi: innovatsionlik — 20%, ilmiy salohiyat — 15%, "
    "tijoratlashtirish — 15%, narx (smeta) — 30%, bajarilish muddati — 20%."
)
EVAL_RU = (
    "Заявки оцениваются по следующим критериям: инновационность — 20%, научный потенциал — 15%, "
    "коммерциализация — 15%, стоимость (смета) — 30%, срок выполнения — 20%."
)
EVAL_EN = (
    "Proposals are scored on: innovation — 20%, scientific merit — 15%, commercialization potential "
    "— 15%, price/budget — 30%, and delivery timeline — 20%."
)

APPLY_HEADING_UZ = "Ariza qanday topshiriladi"
APPLY_HEADING_RU = "Как подать заявку"
APPLY_HEADING_EN = "How to apply"

APPLY_UZ = (
    "Takliflar ushbu sahifadagi “Ariza topshirish” formasi orqali 2026-yil 5-oktabrgacha qabul qilinadi. "
    "Qoʻshimcha savollar boʻyicha murojaat uchun: Institut Iqtidorli talabalar bilan ishlash boʻlimi."
)
APPLY_RU = (
    "Заявки принимаются через форму «Подать заявку» на этой странице до 5 октября 2026 года. По "
    "вопросам обращайтесь в Отдел работы с одарёнными студентами института."
)
APPLY_EN = (
    "Applications are accepted through the “Submit an application” form on this page until October 5, "
    "2026. For questions, contact the institute's Office for Work with Gifted Students."
)


def load_image(fname):
    with open(os.path.join(PHOTO_DIR, fname), "rb") as fh:
        image = Image(alt_text=ALT_TEXT)
        image.file.save(fname, File(fh), save=True)
    print(f"  uploaded image #{image.id}: {image.file.name} ({image.width}x{image.height})")
    return image


def build_html(lang):
    parts = [
        f"<p>{{intro}}</p>",
        f"<h2>{{goal_h}}</h2>",
        f"<p>{{goal}}</p>",
        f"<h2>{{tasks_h}}</h2>",
        "<ol>" + "".join(f"<li>{{t{ i }}}</li>" for i in range(8)) + "</ol>",
        f"<h2>{{req_h}}</h2>",
        f"<p>{{req}}</p>",
        f"<h2>{{eval_h}}</h2>",
        f"<p>{{eval}}</p>",
        f"<h2>{{apply_h}}</h2>",
        f"<p>{{apply}}</p>",
    ]
    tasks = TASKS_UZ if lang == "uz" else TASKS_RU if lang == "ru" else TASKS_EN
    values = {
        "intro": {"uz": BODY_INTRO_UZ, "ru": BODY_INTRO_RU, "en": BODY_INTRO_EN}[lang],
        "goal_h": {"uz": GOAL_HEADING_UZ, "ru": GOAL_HEADING_RU, "en": GOAL_HEADING_EN}[lang],
        "goal": {"uz": GOAL_UZ, "ru": GOAL_RU, "en": GOAL_EN}[lang],
        "tasks_h": {"uz": TASKS_HEADING_UZ, "ru": TASKS_HEADING_RU, "en": TASKS_HEADING_EN}[lang],
        "req_h": {"uz": REQ_HEADING_UZ, "ru": REQ_HEADING_RU, "en": REQ_HEADING_EN}[lang],
        "req": {"uz": REQ_UZ, "ru": REQ_RU, "en": REQ_EN}[lang],
        "eval_h": {"uz": EVAL_HEADING_UZ, "ru": EVAL_HEADING_RU, "en": EVAL_HEADING_EN}[lang],
        "eval": {"uz": EVAL_UZ, "ru": EVAL_RU, "en": EVAL_EN}[lang],
        "apply_h": {"uz": APPLY_HEADING_UZ, "ru": APPLY_HEADING_RU, "en": APPLY_HEADING_EN}[lang],
        "apply": {"uz": APPLY_UZ, "ru": APPLY_RU, "en": APPLY_EN}[lang],
    }
    for i, t in enumerate(tasks):
        values[f"t{i}"] = t
    html = "\n".join(parts)
    return html.format(**values)


def main():
    if NewsPost.objects.filter(slug=SLUG).exists():
        print(f"NewsPost {SLUG!r} already exists -- nothing to do.")
        return

    print("Uploading poster image...")
    cover = load_image(COVER_FILE)

    category = NewsCategory.objects.filter(slug="tanlovlar").first()
    if category is None:
        print("WARNING: 'tanlovlar' category not found -- post will be created without a category.")

    page = Page.objects.create(slug=f"news-{SLUG}")
    write_blocks_from_html(page, {
        "uz": build_html("uz"),
        "ru": build_html("ru"),
        "en": build_html("en"),
    })

    post = NewsPost.objects.create(
        slug=SLUG,
        title_uz=TITLE_UZ, title_ru=TITLE_RU, title_en=TITLE_EN,
        excerpt_uz=EXCERPT_UZ, excerpt_ru=EXCERPT_RU, excerpt_en=EXCERPT_EN,
        cover=cover,
        category=category,
        page=page,
        published_at=timezone.now(),
    )
    print(f"Done. NewsPost id={post.id}, slug={post.slug!r}")


if __name__ == "__main__":
    main()
