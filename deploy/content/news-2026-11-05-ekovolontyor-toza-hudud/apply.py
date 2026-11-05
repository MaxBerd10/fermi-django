# Publishes the news post about the "Toza hudud" hashar (community clean-up day) held by the "Diamond dent" student volunteers of the
# Pediatriya faculty (eco-volunteering): 10 photos (the first is the cover, the other 9 become the post's gallery), category
# "Yashil universitet" (so it shows on the menu's "Green university-2026" page), dated when this runs. The text is exactly what
# the author sent (no additions). It goes through the SAME serializer the admin panel's news form uses, so the post is exactly
# what the panel would save.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-ekovolontyor-toza-hudud/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-ekovolontyor-toza-hudud/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-ekovolontyor-toza-hudud/apply.py   (deletes what apply made)
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
SLUG = "ekovolontyorlar-toza-hudud-hashari-pediatriya-fakulteti"
CATEGORY_SLUG = "yashil-universitet"
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "news-2026-11-05-ekovolontyor-toza-hudud")
SUBDIR = "uploads/2026/11"
DEST_DIR = os.path.join(settings.MEDIA_ROOT, SUBDIR)

# (file in the folder, name under media/, what the picture shows). The first one is the cover.
PHOTOS = [
    ("01.jpg", "toza-hudud-hashari-1.jpg", "Pediatriya fakulteti “Diamond dent” volontyorlari guruh boʻlib"),
    ("02.jpg", "toza-hudud-hashari-2.jpg", "Volontyorlar institut hududida"),
    ("03.jpg", "toza-hudud-hashari-3.jpg", "Volontyorlar supurgi bilan xazonlarni yigʻmoqda"),
    ("04.jpg", "toza-hudud-hashari-4.jpg", "Uch volontyor yigʻilgan oʻtni qopga solmoqda"),
    ("05.jpg", "toza-hudud-hashari-5.jpg", "Uch volontyor oʻt va xazonlarni qopga solmoqda"),
    ("06.jpg", "toza-hudud-hashari-6.jpg", "Orqasida “Diamond-Dent volontyori” yozuvi bor futbolkadagi talabalar qop koʻtarib ketmoqda"),
    ("07.jpg", "toza-hudud-hashari-7.jpg", "Volontyorlar yigʻilgan xazonni institut binosi yonidan olib oʻtmoqda"),
    ("08.jpg", "toza-hudud-hashari-8.jpg", "Ikki volontyor chiqindi toʻldirilgan qopni koʻtarib ketmoqda"),
    ("09.jpg", "toza-hudud-hashari-9.jpg", "Ikki talaba oʻt va xazonlarni qopga solmoqda"),
    ("10.jpg", "toza-hudud-hashari-10.jpg", "Volontyorlar yigʻilgan xazonni chiqindi konteyneriga olib kelmoqda"),
]

TITLE = {
    "uz": "Ekovolontyorlar ishtirokida “Toza hudud” hashari tashkil etildi",
    "ru": "Эковолонтёры провели субботник «Чистая территория»",
    "en": "Eco-volunteers hold a “Clean Area” community clean-up day",
}
PARAGRAPHS = {
    "uz": [
        "Ekovolontyorlik — atrof-muhitni muhofaza qilish, tabiatni asrash va ekologik muammolarni kamaytirishga qaratilgan koʻngilli faoliyatdir.",
        "Pediatriya fakulteti “Diamond dent” koʻngilli talabalardan tashkil topgan volontyorlar ishtirokida “Toza hudud” hashari tashkil etildi.",
        "Hashar davomida institut hududi hamda uning atrofida chiqindilardan tozalanishiga oʻz hissalarini qoʻshdilar.",
    ],
    "ru": [
        "Эковолонтёрство — это добровольная деятельность, направленная на охрану окружающей среды, сохранение природы и уменьшение экологических проблем.",
        "При участии волонтёров факультета педиатрии, состоящих из студентов-добровольцев «Diamond dent», организован субботник «Чистая территория».",
        "В ходе субботника они внесли свой вклад в очистку территории института и прилегающих к нему участков от мусора.",
    ],
    "en": [
        "Eco-volunteering is voluntary activity aimed at protecting the environment, conserving nature and reducing environmental problems.",
        "A “Clean Area” hashar (community clean-up day) was organised with the participation of volunteers of the Faculty of Pediatrics, made up of “Diamond dent” student volunteers.",
        "During the hashar they contributed to cleaning the institute grounds and the area around them of waste.",
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
