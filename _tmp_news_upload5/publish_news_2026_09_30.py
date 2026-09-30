"""One-off script: publishes the 2026-09-30 batch of news posts through the
same Page/ContentBlock/Image pipeline the admin panel's news form uses (see
apps/admin_api/news_views.py) -- a cover photo plus a trailing `gallery`
block for the rest, exactly what the form's GalleryPicker saves.

Photos are read from PHOTO_ROOT/<post key>/ (default /tmp/fermi-news-2026-09-30;
transferred separately -- photos of people don't belong in git history).
They were already re-encoded to progressive JPEG (q80-82, max 1600px wide).
All uz text uses U+02BB for oʻ/gʻ and U+02BC for the ʼ in eʼtibor.
Safe to re-run: posts whose slug already exists are skipped.

    set -a; source /etc/fermi-django.env; set +a
    .venv/bin/python _tmp_news_upload5/publish_news_2026_09_30.py
"""
import os
import re
import sys

import django

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, REPO_ROOT)
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.core.files import File
from django.db import transaction
from django.utils import timezone

from apps.admin_api.news_views import _append_gallery_block
from apps.content.admin_content import write_blocks_from_html
from apps.content.models import Page
from apps.media_lib.models import Image
from apps.news.models import NewsCategory, NewsPost

PHOTO_ROOT = os.environ.get("PHOTO_ROOT", "/tmp/fermi-news-2026-09-30")

POSTS = [
    {
        "key": "eko-klub",
        "slug": "eko-klub-kochat-ekish-aksiyasi-2026-09-30",
        "category": "institut-yangiliklari",
        "cover": "3.jpg",  # planting in front of the institute building
        "gallery": ["1.jpg", "2.jpg", "4.jpg", "5.jpg", "6.jpg", "7.jpg", "8.jpg"],
        "alt": "Eko klub aʼzolari ishtirokida koʻchat ekish aksiyasi",
        "title": {
            "uz": "Tabiatga eʼtibor — kelajakka eʼtibor!",
            "ru": "Забота о природе — забота о будущем!",
            "en": "Caring for Nature Is Caring for the Future!",
        },
        "paragraphs": {
            "uz": [
                "🌱 Eko klub faoliyati doirasida oʻquvchi-yoshlar ishtirokida koʻchat ekish aksiyalari tashkil etildi. 🌳",
                "Aksiya davomida hududni obodonlashtirish, atrof-muhitni asrash va yashil makonlarni kengaytirish "
                "maqsadida turli xil koʻchatlar ekildi.",
                "🌍 Har bir ekilgan koʻchat — tabiat uchun kichik, ammo kelajak uchun katta qadam!",
                "💚 Tabiatni asraylik, yashil kelajakni birgalikda bunyod etaylik!",
            ],
            "ru": [
                "🌱 В рамках деятельности Эко-клуба с участием учащейся молодёжи были организованы акции по посадке "
                "саженцев. 🌳",
                "В ходе акции были высажены различные саженцы в целях благоустройства территории, охраны окружающей "
                "среды и расширения зелёных зон.",
                "🌍 Каждый посаженный саженец — маленький шаг для природы, но большой шаг для будущего!",
                "💚 Давайте беречь природу и вместе создавать зелёное будущее!",
            ],
            "en": [
                "🌱 As part of the Eco Club's activities, tree-planting actions were organized with the participation "
                "of students and young people. 🌳",
                "During the action, a variety of saplings were planted to landscape the grounds, protect the "
                "environment and expand green spaces.",
                "🌍 Every sapling planted is a small step for nature, but a giant step for the future!",
                "💚 Let's protect nature and build a green future together!",
            ],
        },
    },
    {
        "key": "suv",
        "slug": "suvni-birga-asraymiz-chellenji-2026-09-30",
        "category": "institut-yangiliklari",
        "cover": "1.jpg",  # the "Suvni birgalikda asraymiz!" cup
        "gallery": ["2.jpg", "3.jpg", "4.jpg", "5.jpg", "6.jpg", "7.jpg", "8.jpg"],
        "alt": "“Suvni birga asraymiz” chellenji",
        "title": {
            "uz": "Xalqaro fakultet talabalari “Suvni birga asraymiz” chellenjida",
            "ru": "Студенты международного факультета — участники челленджа «Сбережём воду вместе»",
            "en": "International Faculty Students Join the “Let's Save Water Together” Challenge",
        },
        "paragraphs": {
            "uz": [
                "#SuvniBirgaAsraymiz",
                "Fargʻona jamoat salomatligi tibbiyot instituti Xalqaro fakultet tyutori U.Sobitjonov oʻz talabalari "
                "bilan — “Suvni birga asraymiz” chellenjida faol ishtirok etmoqda!",
                "🖋 Suv — hayotning yuragi. Har bir tomchisi bebaho, har bir tomchisi kelajak uchun muhim. Ushbu "
                "tashabbus orqali biz talabalarni suvdan oqilona foydalanishga, isrofgarchilikdan saqlanishga va "
                "tabiatni asrashga chaqiramiz.",
            ],
            "ru": [
                "#SuvniBirgaAsraymiz",
                "Тьютор международного факультета Ферганского медицинского института общественного здоровья "
                "У.Собитжонов вместе со своими студентами активно участвует в челлендже «Сбережём воду вместе»!",
                "🖋 Вода — сердце жизни. Каждая её капля бесценна, каждая капля важна для будущего. Этой инициативой "
                "мы призываем студентов разумно расходовать воду, не допускать её напрасной траты и беречь природу.",
            ],
            "en": [
                "#SuvniBirgaAsraymiz",
                "U. Sobitjonov, a tutor at the International Faculty of the Fergana Medical Institute of Public "
                "Health, is taking an active part in the “Let's Save Water Together” challenge with his students!",
                "🖋 Water is the heart of life. Every drop is priceless, every drop matters for the future. Through "
                "this initiative, we call on students to use water wisely, avoid waste and protect nature.",
            ],
        },
    },
]


def excerpt(paragraphs):
    return re.sub(r"<[^>]+>", "", " ".join(paragraphs[:2]))[:500]


def html(paragraphs):
    return "\n".join(f"<p>{p}</p>" for p in paragraphs)


def load_image(photo_dir, fname, key, alt):
    with open(os.path.join(photo_dir, fname), "rb") as fh:
        image = Image(alt_text=alt)
        image.file.save(f"{key}-{fname}", File(fh), save=True)
    print(f"  uploaded image #{image.id}: {image.file.name} ({image.width}x{image.height})")
    return image


@transaction.atomic
def publish(spec):
    if NewsPost.objects.filter(slug=spec["slug"]).exists():
        print(f"[{spec['key']}] {spec['slug']!r} already exists -- skipped.")
        return

    photo_dir = os.path.join(PHOTO_ROOT, spec["key"])
    missing = [f for f in [spec["cover"], *spec["gallery"]] if not os.path.exists(os.path.join(photo_dir, f))]
    if missing:
        sys.exit(f"[{spec['key']}] missing photos in {photo_dir}: {', '.join(missing)}")

    category = NewsCategory.objects.filter(slug=spec["category"]).first()
    print(f"[{spec['key']}] category: {category.name_uz if category else 'NONE FOUND (left unset)'}")

    cover = load_image(photo_dir, spec["cover"], spec["key"], spec["alt"])
    gallery = [load_image(photo_dir, f, spec["key"], spec["alt"]) for f in spec["gallery"]]

    paragraphs = spec["paragraphs"]
    page = Page.objects.create(slug=f"news-{spec['slug']}")
    write_blocks_from_html(page, {lang: html(paragraphs[lang]) for lang in ("uz", "ru", "en")})
    _append_gallery_block(page, [image.id for image in gallery])

    post = NewsPost.objects.create(
        slug=spec["slug"],
        title_uz=spec["title"]["uz"], title_ru=spec["title"]["ru"], title_en=spec["title"]["en"],
        excerpt_uz=excerpt(paragraphs["uz"]), excerpt_ru=excerpt(paragraphs["ru"]), excerpt_en=excerpt(paragraphs["en"]),
        cover=cover,
        category=category,
        page=page,
        published_at=timezone.now(),
    )
    print(f"[{spec['key']}] done: NewsPost id={post.id}, blocks={[b.block_type for b in page.blocks.all()]}")


if __name__ == "__main__":
    for spec in POSTS:
        publish(spec)
