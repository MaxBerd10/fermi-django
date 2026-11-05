# Publishes the news post about the institute stage of the "EKO FAOL - 2026" contest ("Ekologiya bilimdoni" nomination,
# Davolash ishi faculty, 2 November 2026): winners and the team that goes on to the regional stage. 2 pictures (each is a
# 4-photo collage; the first is the cover, the second becomes the post's gallery), category "Yashil universitet" (so it shows on
# the menu's "Green university-2026" page), dated when this runs. The text is exactly what the author sent (no additions).
# It goes through the SAME serializer the admin panel's news form uses, so the post is exactly what the panel would save.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-eko-faol-2026/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-eko-faol-2026/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-eko-faol-2026/apply.py   (deletes what apply made)
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
SLUG = "eko-faol-2026-ekologiya-bilimdoni-institut-bosqichi-goliblari"
CATEGORY_SLUG = "yashil-universitet"
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "news-2026-11-05-eko-faol-2026")
SUBDIR = "uploads/2026/11"
DEST_DIR = os.path.join(settings.MEDIA_ROOT, SUBDIR)

# (file in the folder, name under media/, what the picture shows). The first one is the cover.
PHOTOS = [
    ("01.jpg", "eko-faol-2026-institut-bosqichi-1.jpg", "“EKO FAOL – 2026” tanlovi institut bosqichi: ishtirokchi jamoalar, hakamlar va tanlov lavhalari"),
    ("02.jpg", "eko-faol-2026-institut-bosqichi-2.jpg", "“EKO FAOL – 2026” tanlovi institut bosqichi: gʻolib jamoalar tashakkurnomalar bilan taqdirlanmoqda"),
]

TITLE = {
    "uz": "“EKO FAOL – 2026”: “Ekologiya bilimdoni” tanlovining institut bosqichi gʻoliblari aniqlandi",
    "ru": "«EKO FAOL – 2026»: определены победители институтского этапа конкурса «Знаток экологии»",
    "en": "“EKO FAOL – 2026”: winners of the institute stage of the “Ecology Expert” contest announced",
}
PARAGRAPHS = {
    "uz": [
        "🌍 2026-yil 2-noyabr kuni Fargʻona jamoat salomatligi tibbiyot institutida Davolash ishi fakulteti talabalari oʻrtasida “EKO FAOL – 2026” tanlovining “Ekologiya bilimdoni” nominatsiyasi boʻyicha institut bosqichi boʻlib oʻtdi.",
        "🌱 Talaba-yoshlarning ekologik bilim va madaniyatini yuksaltirish, ekologik tashabbuslarini qoʻllab-quvvatlash maqsadida tashkil etilgan tanlovda “EKOFORS”, “YASHIL AVLOD”, “EKOAKTIVIST”, “PARADOKS”, “SIRIUS”, “EKOMED” va “EKOAVLOD” jamoalari 5 ta shart boʻyicha oʻzaro bellashdilar.",
        "🏆 Tanlov natijalariga koʻra:",
        "🥇 1-oʻrin — “PARADOKS” jamoasi",
        "🥈 2-oʻrin — “EKOFORS” jamoasi",
        "🥉 3-oʻrin — “EKOMED” jamoasi",
        "👏 Gʻoliblar Davolash ishi fakultetining tashakkurnomalari bilan taqdirlandilar.",
        "🎯 1-oʻrinni egallagan “PARADOKS” jamoasi viloyat bosqichiga yoʻllanmani qoʻlga kiritdi!",
        "Tabiatga befarq boʻlma — EKO FAOL boʻl!",
    ],
    "ru": [
        "🌍 2 ноября 2026 года в Ферганском медицинском институте общественного здоровья среди студентов факультета «Лечебное дело» прошёл институтский этап конкурса «EKO FAOL – 2026» по номинации «Знаток экологии».",
        "🌱 В конкурсе, организованном с целью повышения экологических знаний и культуры студенческой молодёжи и поддержки её экологических инициатив, команды «EKOFORS», «YASHIL AVLOD», «EKOAKTIVIST», «PARADOKS», «SIRIUS», «EKOMED» и «EKOAVLOD» соревновались по 5 условиям.",
        "🏆 По итогам конкурса:",
        "🥇 1 место — команда «PARADOKS»",
        "🥈 2 место — команда «EKOFORS»",
        "🥉 3 место — команда «EKOMED»",
        "👏 Победители награждены благодарственными письмами факультета «Лечебное дело».",
        "🎯 Команда «PARADOKS», занявшая 1 место, получила путёвку на областной этап!",
        "Не будь равнодушен к природе — будь EKO FAOL!",
    ],
    "en": [
        "🌍 On 2 November 2026 the institute stage of the “EKO FAOL – 2026” contest, in the “Ecology Expert” nomination, was held at the Fergana Medical Institute of Public Health among students of the General Medicine faculty.",
        "🌱 In the contest, organised to raise students’ environmental knowledge and culture and to support their environmental initiatives, the teams “EKOFORS”, “YASHIL AVLOD”, “EKOAKTIVIST”, “PARADOKS”, “SIRIUS”, “EKOMED” and “EKOAVLOD” competed on 5 criteria.",
        "🏆 The results of the contest:",
        "🥇 1st place — team “PARADOKS”",
        "🥈 2nd place — team “EKOFORS”",
        "🥉 3rd place — team “EKOMED”",
        "👏 The winners were awarded certificates of appreciation of the General Medicine faculty.",
        "🎯 Team “PARADOKS”, which took 1st place, won a ticket to the regional stage!",
        "Don’t be indifferent to nature — be EKO FAOL!",
    ],
}


def html_of(lang):
    return "\n".join("<p>%s</p>" % p for p in PARAGRAPHS[lang])


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

if MODE == "remove":
    if existing is None:
        raise SystemExit("Nothing to remove: the post is not there.")
    page = existing.page
    images = [i for i in Image.objects.filter(file__in=[SUBDIR + "/" + n for _, n, _ in PHOTOS])]
    with transaction.atomic():
        existing.delete()
        page.delete()
        for image in images:
            image.delete()
    for image in images:
        path = os.path.join(settings.MEDIA_ROOT, image.file.name)
        if os.path.isfile(path):
            os.remove(path)
    print("REMOVED the post, its page and its", len(images), "photos.")
else:
    category = NewsCategory.objects.filter(slug=CATEGORY_SLUG).first()
    if category is None:
        raise SystemExit("STOP: category '%s' not found (have: %s). Nothing was modified." % (CATEGORY_SLUG, list(NewsCategory.objects.values_list("slug", flat=True))))
    missing = [f for f, _, _ in PHOTOS if not os.path.isfile(os.path.join(SRC_DIR, f))]
    if missing:
        raise SystemExit("STOP: photos missing (git pull first?): %s. Nothing was modified." % missing)
    if existing is not None:
        raise SystemExit("The post already exists (id %s): %s. Nothing was modified." % (existing.pk, SLUG))
    print("category:", category.name_uz, "| photos:", len(PHOTOS), "(cover + %d in the gallery)" % (len(PHOTOS) - 1))
    for lang in ("uz", "ru", "en"):
        print("title %s: %s" % (lang, TITLE[lang]))
    print("uz text, paragraph 1:", PARAGRAPHS["uz"][0][:110], "...")
    if MODE != "apply":
        print("DRY RUN: nothing was created. Run again with MODE=apply to publish.")
    else:
        os.makedirs(DEST_DIR, exist_ok=True)
        copied = []
        for src_name, dest_name, _ in PHOTOS:
            dest = os.path.join(DEST_DIR, dest_name)
            shutil.copyfile(os.path.join(SRC_DIR, src_name), dest)
            copied.append(dest)
        hand_to_www_data([DEST_DIR] + copied)
        paths = [SUBDIR + "/" + dest_name for _, dest_name, _ in PHOTOS]
        payload = {
            "title_uz": TITLE["uz"], "title_ru": TITLE["ru"], "title_en": TITLE["en"],
            "content_uz": html_of("uz"), "content_ru": html_of("ru"), "content_en": html_of("en"),
            "slug": SLUG, "category_id": category.pk, "status": 1,
            "date": timezone.now().isoformat(),
            "img": paths[0], "gallery": paths[1:],
        }
        request = Request(APIRequestFactory().post("/api/v1/admin/news", payload, format="json"), parsers=[JSONParser()])
        with transaction.atomic():
            serializer = AdminPostSerializer(data=payload, context={"request": request})
            serializer.is_valid(raise_exception=True)
            post = serializer.save()
            # the list cards show a post's first paragraph, not a cut of both paragraphs
            post.excerpt_uz, post.excerpt_ru, post.excerpt_en = (PARAGRAPHS[l][0][:500] for l in ("uz", "ru", "en"))
            post.save(update_fields=["excerpt_uz", "excerpt_ru", "excerpt_en"])
            for (_, dest_name, alt), path in zip(PHOTOS, paths):
                Image.objects.filter(file=path).update(alt_text=alt)
        print("DONE. Post id", post.pk, "|", post.published_at, "| https://fermi.uz/detail/%s" % post.slug)
        print("(the site shows it within about a minute; edit or delete it later in the admin panel: Yangiliklar)")
