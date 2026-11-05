# Publishes the news post about the clean-up and landscaping at the "Jannatmozor" cemetery (Guliston MFY, Fergana) done by the
# "Ekofaol yoshlar" project and the Davolash ishi faculty: 9 pictures (the first is the cover, the other 8 become the post's
# gallery), category "Yashil universitet" (so it shows on the menu's "Green university-2026" page), dated when this runs.
# The text is exactly what the author sent (no additions). It goes through the SAME serializer the admin panel's news form
# uses, so the post is exactly what the panel would save.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-jannatmozor-obodonlashtirish/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-jannatmozor-obodonlashtirish/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-jannatmozor-obodonlashtirish/apply.py   (deletes what apply made)
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
SLUG = "ekofaol-yoshlar-jannatmozor-qabristonida-obodonlashtirish-ishlari"
CATEGORY_SLUG = "yashil-universitet"
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "news-2026-11-05-jannatmozor-obodonlashtirish")
SUBDIR = "uploads/2026/11"
DEST_DIR = os.path.join(settings.MEDIA_ROOT, SUBDIR)

# (file in the folder, name under media/, what the picture shows). The first one is the cover.
PHOTOS = [
    ("01.jpg", "jannatmozor-obodonlashtirish-1.jpg", "“Abadiylik” sheʼri yozilgan kartochka: qabriston hududida ishlayotgan ishtirokchi"),
    ("02.jpg", "jannatmozor-obodonlashtirish-2.jpg", "Obodonlashtirish ishtirokchilari qabriston yoʻlagida"),
    ("03.jpg", "jannatmozor-obodonlashtirish-3.jpg", "Ishtirokchilar qabriston hududini tozalamoqda"),
    ("04.jpg", "jannatmozor-obodonlashtirish-4.jpg", "Tadbir yakunida ishtirokchilar Qurʼon tilovati uchun jamlandi"),
    ("05.jpg", "jannatmozor-obodonlashtirish-5.jpg", "Yigʻilgan chiqindi va xazonlar yuk mashinasiga ortilmoqda"),
    ("06.jpg", "jannatmozor-obodonlashtirish-6.jpg", "Ishtirokchilar ezgu duo qilmoqda"),
    ("07.jpg", "jannatmozor-obodonlashtirish-7.jpg", "Talabalar va masʼullar qabriston hududini tartibga keltirmoqda"),
    ("08.jpg", "jannatmozor-obodonlashtirish-8.jpg", "Ishtirokchilar qabristondagi oʻt va chiqindilarni yigʻishtirmoqda"),
    ("09.jpg", "jannatmozor-obodonlashtirish-9.jpg", "Qabriston dargohi va uning atrofini tozalash ishlari"),
]

TITLE = {
    "uz": "“Ekofaol yoshlar” loyihasi doirasida obodonlashtirish ishlari olib borildi",
    "ru": "В рамках проекта «Экоактивная молодёжь» проведены работы по благоустройству",
    "en": "Landscaping work carried out under the “Eco-Active Youth” project",
}
PARAGRAPHS = {
    "uz": [
        "Institut talaba-yoshlari oʻrtasida ekologik madaniyatni shakllantirish, atrof-muhitga masʼuliyatli munosabatni kuchaytirish hamda yashil tashabbuslarni qoʻllab-quvvatlash maqsadida Fargʻona shahridagi Guliston MFY hamkorligida “Jannatmozor” qabriston dargohida obodonlashtirish ishlari tashkil etildi.",
        "Unda Davolash ishi fakulteti masʼullari hamda eko-faol talabalar faol ishtirok etib, hududni tozalash va obodonlashtirish ishlariga hissa qoʻshdilar.",
        "Tadbir yakunida mangulikka bosh qoʻygan ajdodlarimiz ruhiga Qurʼon tilovatlari qilinib, ezgu duolar oʻqildi.",
        "🌿 Obod maskan — yuksak madaniyat va masʼuliyatli yoshlar timsolidir!",
    ],
    "ru": [
        "С целью формирования экологической культуры среди студенческой молодёжи института, усиления ответственного отношения к окружающей среде и поддержки «зелёных» инициатив совместно с махаллёй «Гулистон» города Ферганы на территории кладбища «Жаннатмазор» были организованы работы по благоустройству.",
        "В них приняли активное участие ответственные лица факультета «Лечебное дело» и эко-активные студенты, внеся свой вклад в уборку и благоустройство территории.",
        "По завершении мероприятия были прочитаны аяты Корана и вознесены добрые молитвы за души ушедших в вечность предков.",
        "🌿 Благоустроенное место — символ высокой культуры и ответственной молодёжи!",
    ],
    "en": [
        "To build an environmental culture among the institute’s students, strengthen a responsible attitude to the environment and support green initiatives, landscaping work was organised at the “Jannatmozor” cemetery in Fergana city together with the Guliston neighbourhood community (MFY).",
        "Representatives of the General Medicine faculty and eco-active students took an active part, contributing to cleaning and improving the area.",
        "At the end of the event, verses of the Qur’an were recited and good prayers were said for the souls of our ancestors who have passed into eternity.",
        "🌿 A well-kept place is a symbol of high culture and responsible youth!",
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
