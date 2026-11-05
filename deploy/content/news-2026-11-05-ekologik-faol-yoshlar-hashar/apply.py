# Publishes the news post about the landscaping and clean-up hashar held by the volunteer students of the Davolash ishi faculty
# within the "Ekologik faol yoshlar" events: 9 photos (the first is the cover, the other 8 become the post's gallery), category
# "Yashil universitet" (so it shows on the menu's "Green university-2026" page), dated when this runs. The text is exactly what
# the author sent (no additions; the hashtags are left out). It goes through the SAME serializer the admin panel's news form
# uses, so the post is exactly what the panel would save.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-ekologik-faol-yoshlar-hashar/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-ekologik-faol-yoshlar-hashar/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/news-2026-11-05-ekologik-faol-yoshlar-hashar/apply.py   (deletes what apply made)
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
SLUG = "ekologik-faol-yoshlar-obodonlashtirish-va-tozalik-hashari-davolash-ishi"
CATEGORY_SLUG = "yashil-universitet"
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "news-2026-11-05-ekologik-faol-yoshlar-hashar")
SUBDIR = "uploads/2026/11"
DEST_DIR = os.path.join(settings.MEDIA_ROOT, SUBDIR)

# (file in the folder, name under media/, what the picture shows). The first one is the cover.
PHOTOS = [
    ("01.jpg", "tozalik-hashari-1.jpg", "Volontyor talabalar xiyobon yoʻlagidagi chiqindilarni yigʻmoqda"),
    ("02.jpg", "tozalik-hashari-2.jpg", "Volontyorlar maysazordagi xazonlarni supurmoqda"),
    ("03.jpg", "tozalik-hashari-3.jpg", "Hashar ishtirokchilari guruh boʻlib"),
    ("04.jpg", "tozalik-hashari-4.jpg", "Volontyorlar yigʻilgan xazonni gazlamaga solmoqda"),
    ("05.jpg", "tozalik-hashari-5.jpg", "Volontyorlar maysazorni xazon va chiqindilardan tozalamoqda"),
    ("06.jpg", "tozalik-hashari-6.jpg", "Talabalar va ustoz xazonlarni supurib, chiqindi yigʻmoqda"),
    ("07.jpg", "tozalik-hashari-7.jpg", "Ishtirokchilar chelak va qop bilan chiqindi yigʻmoqda"),
    ("08.jpg", "tozalik-hashari-8.jpg", "Ishtirokchilar yoʻlakdagi xazon va chiqindilarni yigʻmoqda"),
    ("09.jpg", "tozalik-hashari-9.jpg", "Ikki talaba yigʻilgan xazonni gazlamada olib ketmoqda"),
]

TITLE = {
    "uz": "“Ekologik faol yoshlar” tadbirlari doirasida obodonlashtirish va tozalik hashari tashkil etildi",
    "ru": "В рамках мероприятий «Экоактивная молодёжь» организован субботник по благоустройству и наведению чистоты",
    "en": "Landscaping and clean-up day held under the “Eco-Active Youth” events",
}
PARAGRAPHS = {
    "uz": [
        "🌱 Tabiatni asrash — barchamizning burchimiz!",
        "Davolash ishi fakulteti koʻngilli talabalari tomonidan “Ekologik faol yoshlar” tadbirlari doirasida obodonlashtirish va tozalik hashari tashkil etildi.",
        "Hashar davomida talabalar hududni chiqindilardan tozalash, atrof-muhitni obodonlashtirish hamda ekologik madaniyatni yuksaltirishga qaratilgan ishlarda faol ishtirok etdilar.",
        "Mazkur tadbir yoshlar oʻrtasida tabiatga mehr, atrof-muhitga masʼuliyat bilan munosabatda boʻlish va jamoaviy hamjihatlik tuygʻularini mustahkamlashga xizmat qildi.",
        "Zero, toza va obod muhit — sogʻlom hayot garovidir! 🌿",
    ],
    "ru": [
        "🌱 Сохранять природу — наш общий долг!",
        "Студентами-добровольцами факультета «Лечебное дело» в рамках мероприятий «Экоактивная молодёжь» организован субботник по благоустройству и наведению чистоты.",
        "В ходе субботника студенты активно участвовали в работах по очистке территории от мусора, благоустройству окружающей среды и повышению экологической культуры.",
        "Данное мероприятие способствовало укреплению среди молодёжи любви к природе, ответственного отношения к окружающей среде и чувства коллективного единства.",
        "Ведь чистая и благоустроенная среда — залог здоровой жизни! 🌿",
    ],
    "en": [
        "🌱 Protecting nature is the duty of all of us!",
        "A landscaping and clean-up day (hashar) was organised by volunteer students of the General Medicine faculty as part of the “Eco-Active Youth” events.",
        "During the hashar the students took an active part in cleaning the area of waste, improving the surroundings and raising environmental culture.",
        "The event helped strengthen young people’s love of nature, a responsible attitude to the environment and a sense of teamwork.",
        "After all, a clean and well-kept environment is the guarantee of a healthy life! 🌿",
    ],
}
# the list cards show the first real sentence, not the opening slogan line
EXCERPT_FROM = 1


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
            
            post.excerpt_uz, post.excerpt_ru, post.excerpt_en = (PARAGRAPHS[l][EXCERPT_FROM][:500] for l in ("uz", "ru", "en"))
            post.save(update_fields=["excerpt_uz", "excerpt_ru", "excerpt_en"])
            for (_, dest_name, alt), path in zip(PHOTOS, paths):
                Image.objects.filter(file=path).update(alt_text=alt)
        print("DONE. Post id", post.pk, "|", post.published_at, "| https://fermi.uz/detail/%s" % post.slug)
        print("(the site shows it within about a minute; edit or delete it later in the admin panel: Yangiliklar)")
