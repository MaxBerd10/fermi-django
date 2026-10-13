# Publishes the news post about the 13.10.2026 job fair ("Kelajak tadbirkorlari-2026", Farg'ona Kasbiy ko'nikmalar markazi):
# 6 photos (the first is the cover, the other 5 become the post's gallery), category "Tadbirlar", dated when this runs.
# It goes through the SAME serializer the admin panel's news form uses, so the post is exactly what the panel would save.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/news-2026-10-13-yarmarka/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/news-2026-10-13-yarmarka/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/news-2026-10-13-yarmarka/apply.py   (deletes what apply made)
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
SLUG = "kelajak-tadbirkorlari-2026-kasb-bandlik-yarmarkasi-2026-10-13"
CATEGORY_SLUG = "tadbirlar"
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "news-2026-10-13-yarmarka")
SUBDIR = "uploads/2026/10"
DEST_DIR = os.path.join(settings.MEDIA_ROOT, SUBDIR)

# (file in the folder, name under media/, what the picture shows). The first one is the cover.
PHOTOS = [
    ("01-kirish-darvozasi.jpg", "yarmarka-2026-10-13-1.jpg", "Yarmarkaning kirish darvozasi: Kasbiy koʻnikmalar markazi"),
    ("02-ochilish-sahnasi.jpg", "yarmarka-2026-10-13-2.jpg", "Yarmarkaning ochilish marosimi sahnasi"),
    ("03-ma-ruzachi.jpg", "yarmarka-2026-10-13-3.jpg", "Sahnada soʻzga chiqqan maʼruzachi"),
    ("04-ishtirokchilar.jpg", "yarmarka-2026-10-13-4.jpg", "Yarmarka ishtirokchilari muloqot qilmoqda"),
    ("05-kelajak-tadbirkori-stendi.jpg", "yarmarka-2026-10-13-5.jpg", "“Kelajak tadbirkori-2026” koʻrgazma maydonchasi"),
    ("06-korgazma-stendlari.jpg", "yarmarka-2026-10-13-6.jpg", "Yarmarkaning koʻrgazma stendlari"),
]

TITLE = {
    "uz": "“Kelajak tadbirkorlari–2026” kasb, bandlik va tadbirkorlik imkoniyatlari yarmarkasi tashkil etildi",
    "ru": "В Фергане организована ярмарка «Будущие предприниматели–2026» по вопросам профессий, занятости и предпринимательства",
    "en": "“Future Entrepreneurs–2026” fair of career, employment and business opportunities held in Fergana",
}
PARAGRAPHS = {
    "uz": [
        "2025–2026-oʻquv yili bitiruvchilarining bandligini taʼminlash, ularning kasbiy bilim va koʻnikmalarini amaliyotga tatbiq etish, mehnat bozorida munosib ish oʻrinlarini topishlariga koʻmaklashish hamda tadbirkorlik faoliyatiga boʻlgan qiziqishlarini oshirish maqsadida 13.10.2026 yil kuni Fargʻona shahar Kasbiy koʻnikmalar markazida “Kelajak tadbirkorlari–2026” kasb, bandlik va tadbirkorlik imkoniyatlari yarmarkasi tashkil etildi.",
        "Mazkur yarmarkaning asosiy maqsadi bitiruvchilarni ish beruvchilar bilan bevosita muloqotga olib chiqish, mavjud boʻsh ish oʻrinlari toʻgʻrisida maʼlumot berish, yoshlarning kasbiy salohiyatini namoyon etishiga sharoit yaratish hamda ularni tadbirkorlik faoliyatiga keng jalb etishdan iborat boʻldi.",
    ],
    "ru": [
        "В целях обеспечения занятости выпускников 2025–2026 учебного года, применения ими профессиональных знаний и навыков на практике, содействия в поиске достойных рабочих мест на рынке труда, а также повышения интереса к предпринимательской деятельности 13.10.2026 в Центре профессиональных навыков города Ферганы организована ярмарка возможностей в сфере профессий, занятости и предпринимательства «Будущие предприниматели–2026».",
        "Основной целью ярмарки стало налаживание прямого общения выпускников с работодателями, информирование об имеющихся вакансиях, создание условий для проявления профессионального потенциала молодёжи и широкое привлечение её к предпринимательской деятельности.",
    ],
    "en": [
        "To ensure the employment of 2025–2026 graduates, help them apply their professional knowledge and skills in practice, find decent jobs on the labour market and raise their interest in entrepreneurship, the “Future Entrepreneurs–2026” fair of career, employment and business opportunities was held at the Vocational Skills Centre of Fergana city on 13 October 2026.",
        "The main aim of the fair was to bring graduates into direct dialogue with employers, inform them about available vacancies, give young people the chance to show their professional potential and widely involve them in entrepreneurial activity.",
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
