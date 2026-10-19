# Publishes the announcement "InnoMix FJSTI -- innovatsion loyihalar tanlovi" (startup / innovative project contest, 10 directions):
# cover = the poster, category "Tanlovlar" (created if the site has none yet -- the "Ariza topshirish" form shows under every post of this category),
# dated when this runs. It goes through the SAME serializer the admin panel's news form uses.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/news-2026-10-19-innomix/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/news-2026-10-19-innomix/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/news-2026-10-19-innomix/apply.py   (deletes what apply made)
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

from apps.admin_api.news_views import AdminPostSerializer
from apps.media_lib.models import Image
from apps.news.models import NewsCategory, NewsPost

MODE = os.environ.get("MODE", "dry")
SLUG = "innomix-fjsti-innovatsion-loyihalar-tanlovi-2026"
CATEGORY_SLUG = "tanlovlar"
CATEGORY_NAMES = {"uz": "Tanlovlar", "ru": "Конкурсы", "en": "Contests"}
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "news-2026-10-19-innomix")
SUBDIR = "uploads/2026/10"
DEST_DIR = os.path.join(settings.MEDIA_ROOT, SUBDIR)
POSTER = ("innomix-afisha.jpg", "innomix-2026-afisha.jpg", "InnoMix FJSTI innovatsion loyihalar tanlovi afishasi")

TITLE = {
    "uz": "InnoMix FJSTI — innovatsion loyihalar tanlovi boshlandi!",
    "ru": "InnoMix FJSTI — стартовал конкурс инновационных проектов!",
    "en": "InnoMix FJSTI — the innovative projects contest has begun!",
}
DIRECTIONS = {
    "uz": ["Jamoat salomatligi", "Tibbiyot va tibbiy texnologiyalar", "Farmatsevtika va farmakologiya", "Biotexnologiyalar",
           "Tibbiy diagnostika va laboratoriya", "Raqamli tibbiyot va sunʼiy intellekt", "Epidemiologiya va profilaktika",
           "Gigiyena va ekologik salomatlik", "Ona va bola salomatligi", "Tibbiy taʼlimda innovatsiyalar"],
    "ru": ["Общественное здоровье", "Медицина и медицинские технологии", "Фармацевтика и фармакология", "Биотехнологии",
           "Медицинская диагностика и лаборатория", "Цифровая медицина и искусственный интеллект", "Эпидемиология и профилактика",
           "Гигиена и экологическое здоровье", "Здоровье матери и ребёнка", "Инновации в медицинском образовании"],
    "en": ["Public health", "Medicine and medical technologies", "Pharmacy and pharmacology", "Biotechnology",
           "Medical diagnostics and laboratory science", "Digital medicine and artificial intelligence", "Epidemiology and prevention",
           "Hygiene and environmental health", "Maternal and child health", "Innovations in medical education"],
}
TEXT = {
    "uz": {
        "intro": "🚀 FJSTI talabalari, gʻoyangiz bormi? Uni haqiqiy loyihaga aylantirish vaqti keldi! 💡",
        "dirs": "📌 Loyihalar 10 ta yoʻnalish boʻyicha qabul qilinadi:",
        "rest": [
            "🏆 Har bir yoʻnalish gʻolibiga — 3 000 000 soʻm pul mukofoti!",
            "⏳ Loyihalar 31-oktabrgacha qabul qilinadi.",
            "📅 Tanlov 9–13-noyabr kunlari boʻlib oʻtadi.",
            "📝 Ariza topshirish: fermi.uz. Jamoangizni tuzing va oʻz loyihangizni taqdim eting! 👇",
        ],
        "form": "Ariza berish uchun shu sahifaning pastidagi «Ariza topshirish» shaklini toʻldiring.",
    },
    "ru": {
        "intro": "🚀 Студенты ФЖСТИ, есть идея? Пришло время превратить её в настоящий проект! 💡",
        "dirs": "📌 Проекты принимаются по 10 направлениям:",
        "rest": [
            "🏆 Победителю каждого направления — денежная премия 3 000 000 сумов!",
            "⏳ Проекты принимаются до 31 октября.",
            "📅 Конкурс пройдёт 9–13 ноября.",
            "📝 Подать заявку: fermi.uz. Соберите свою команду и представьте свой проект! 👇",
        ],
        "form": "Чтобы подать заявку, заполните форму «Подать заявку» внизу этой страницы.",
    },
    "en": {
        "intro": "🚀 FJSTI students, do you have an idea? It is time to turn it into a real project! 💡",
        "dirs": "📌 Projects are accepted in 10 directions:",
        "rest": [
            "🏆 The winner of each direction receives a cash prize of 3,000,000 UZS!",
            "⏳ Projects are accepted until 31 October.",
            "📅 The contest takes place on 9–13 November.",
            "📝 Apply at fermi.uz. Form your team and present your project! 👇",
        ],
        "form": "To apply, fill in the “Apply” form at the bottom of this page.",
    },
}


def html_of(lang):
    t = TEXT[lang]
    items = "".join("<li>%s</li>" % d for d in DIRECTIONS[lang])
    rest = "".join("<p>%s</p>" % p for p in t["rest"])
    return "<p>%s</p><p>%s</p><ol>%s</ol>%s<p>%s</p>" % (t["intro"], t["dirs"], items, rest, t["form"])


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
poster_path = SUBDIR + "/" + POSTER[1]

if MODE == "remove":
    if existing is None:
        raise SystemExit("Nothing to remove: the post is not there.")
    page = existing.page
    images = list(Image.objects.filter(file=poster_path))
    with transaction.atomic():
        existing.delete()
        page.delete()
        for image in images:
            image.delete()
    for image in images:
        path = os.path.join(settings.MEDIA_ROOT, image.file.name)
        if os.path.isfile(path):
            os.remove(path)
    print("REMOVED the post, its page and its poster (the category '%s' is left in place)." % CATEGORY_SLUG)
else:
    category = NewsCategory.objects.filter(slug=CATEGORY_SLUG).first()
    if not os.path.isfile(os.path.join(SRC_DIR, POSTER[0])):
        raise SystemExit("STOP: the poster is missing (git pull first?). Nothing was modified.")
    if existing is not None:
        raise SystemExit("The post already exists (id %s): %s. Nothing was modified." % (existing.pk, SLUG))
    print("category:", category.name_uz if category else "(will be created: %s)" % CATEGORY_NAMES["uz"])
    for lang in ("uz", "ru", "en"):
        print("title %s: %s" % (lang, TITLE[lang]))
    print("uz html:", html_of("uz")[:160], "...")
    if MODE != "apply":
        print("DRY RUN: nothing was created. Run again with MODE=apply to publish.")
    else:
        os.makedirs(DEST_DIR, exist_ok=True)
        dest = os.path.join(DEST_DIR, POSTER[1])
        shutil.copyfile(os.path.join(SRC_DIR, POSTER[0]), dest)
        hand_to_www_data([DEST_DIR, dest])
        with transaction.atomic():
            if category is None:
                category = NewsCategory.objects.create(
                    slug=CATEGORY_SLUG, name_uz=CATEGORY_NAMES["uz"], name_ru=CATEGORY_NAMES["ru"], name_en=CATEGORY_NAMES["en"]
                )
            payload = {
                "title_uz": TITLE["uz"], "title_ru": TITLE["ru"], "title_en": TITLE["en"],
                "content_uz": html_of("uz"), "content_ru": html_of("ru"), "content_en": html_of("en"),
                "slug": SLUG, "category_id": category.pk, "status": 1,
                "date": timezone.now().isoformat(),
                "img": poster_path,
            }
            request = Request(APIRequestFactory().post("/api/v1/admin/news", payload, format="json"), parsers=[JSONParser()])
            serializer = AdminPostSerializer(data=payload, context={"request": request})
            serializer.is_valid(raise_exception=True)
            post = serializer.save()
            post.excerpt_uz = TEXT["uz"]["intro"]
            post.excerpt_ru = TEXT["ru"]["intro"]
            post.excerpt_en = TEXT["en"]["intro"]
            post.save(update_fields=["excerpt_uz", "excerpt_ru", "excerpt_en"])
            Image.objects.filter(file=poster_path).update(alt_text=POSTER[2])
        print("DONE. Post id", post.pk, "|", post.published_at, "| https://fermi.uz/detail/%s" % post.slug)
        print("(the site shows it within about a minute; edit or delete it later in the admin panel: Yangiliklar)")
