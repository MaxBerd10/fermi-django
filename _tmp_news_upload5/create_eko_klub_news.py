"""One-off script: publishes the Eko klub tree-planting action as a NewsPost,
through the same Page/ContentBlock/Image pipeline the admin panel's news form
uses (see apps/admin_api/news_views.py) -- cover photo plus a trailing
`gallery` block for the rest, exactly what the form's GalleryPicker saves.

Photos are read from PHOTO_DIR (default /tmp/eko-klub-photos; transferred
separately -- photos of people don't belong in git history). They were
already re-encoded to progressive JPEG q80 at their original 1280x960.
All uz text uses U+02BB for oʻ/gʻ and U+02BC for the ʼ in eʼtibor.

    set -a; source /etc/fermi-django.env; set +a
    .venv/bin/python _tmp_news_upload5/create_eko_klub_news.py
"""
import os
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

PHOTO_DIR = os.environ.get("PHOTO_DIR", "/tmp/eko-klub-photos")
COVER_FILE = "3.jpg"  # planting in front of the institute building
GALLERY_FILES = ["1.jpg", "2.jpg", "4.jpg", "5.jpg", "6.jpg", "7.jpg", "8.jpg"]
CATEGORY_SLUG = "institut-yangiliklari"
ALT_TEXT = "Eko klub aʼzolari ishtirokida koʻchat ekish aksiyasi"

SLUG = "eko-klub-kochat-ekish-aksiyasi-2026-09-30"

TITLE_UZ = "Tabiatga eʼtibor — kelajakka eʼtibor!"
TITLE_RU = "Забота о природе — забота о будущем!"
TITLE_EN = "Caring for Nature Is Caring for the Future!"

PARAGRAPHS_UZ = [
    "🌱 Eko klub faoliyati doirasida oʻquvchi-yoshlar ishtirokida koʻchat ekish aksiyalari tashkil etildi. 🌳",
    "Aksiya davomida hududni obodonlashtirish, atrof-muhitni asrash va yashil makonlarni kengaytirish "
    "maqsadida turli xil koʻchatlar ekildi.",
    "🌍 Har bir ekilgan koʻchat — tabiat uchun kichik, ammo kelajak uchun katta qadam!",
    "💚 <strong>Tabiatni asraylik, yashil kelajakni birgalikda bunyod etaylik!</strong>",
]
PARAGRAPHS_RU = [
    "🌱 В рамках деятельности Эко-клуба с участием учащейся молодёжи были организованы акции по посадке "
    "саженцев. 🌳",
    "В ходе акции были высажены различные саженцы в целях благоустройства территории, охраны окружающей "
    "среды и расширения зелёных зон.",
    "🌍 Каждый посаженный саженец — маленький шаг для природы, но большой шаг для будущего!",
    "💚 <strong>Давайте беречь природу и вместе создавать зелёное будущее!</strong>",
]
PARAGRAPHS_EN = [
    "🌱 As part of the Eco Club's activities, tree-planting actions were organized with the participation "
    "of students and young people. 🌳",
    "During the action, a variety of saplings were planted to landscape the grounds, protect the "
    "environment and expand green spaces.",
    "🌍 Every sapling planted is a small step for nature, but a giant step for the future!",
    "💚 <strong>Let's protect nature and build a green future together!</strong>",
]


def excerpt(paragraphs):
    import re

    text = re.sub(r"<[^>]+>", "", " ".join(paragraphs[:2]))
    return text[:500]


def load_image(fname):
    with open(os.path.join(PHOTO_DIR, fname), "rb") as fh:
        image = Image(alt_text=ALT_TEXT)
        image.file.save(f"eko-klub-{fname}", File(fh), save=True)
    print(f"  uploaded image #{image.id}: {image.file.name} ({image.width}x{image.height})")
    return image


def html(paragraphs):
    return "\n".join(f"<p>{p}</p>" for p in paragraphs)


@transaction.atomic
def main():
    if NewsPost.objects.filter(slug=SLUG).exists():
        print(f"NewsPost {SLUG!r} already exists -- nothing to do.")
        return

    missing = [f for f in [COVER_FILE, *GALLERY_FILES] if not os.path.exists(os.path.join(PHOTO_DIR, f))]
    if missing:
        sys.exit(f"Missing photos in {PHOTO_DIR}: {', '.join(missing)}")

    category = NewsCategory.objects.filter(slug=CATEGORY_SLUG).first()
    print(f"Category: {category.name_uz if category else 'NONE FOUND (left unset)'}")

    print("Uploading photos...")
    cover = load_image(COVER_FILE)
    gallery = [load_image(f) for f in GALLERY_FILES]

    page = Page.objects.create(slug=f"news-{SLUG}")
    write_blocks_from_html(page, {"uz": html(PARAGRAPHS_UZ), "ru": html(PARAGRAPHS_RU), "en": html(PARAGRAPHS_EN)})
    _append_gallery_block(page, [image.id for image in gallery])

    post = NewsPost.objects.create(
        slug=SLUG,
        title_uz=TITLE_UZ, title_ru=TITLE_RU, title_en=TITLE_EN,
        excerpt_uz=excerpt(PARAGRAPHS_UZ), excerpt_ru=excerpt(PARAGRAPHS_RU), excerpt_en=excerpt(PARAGRAPHS_EN),
        cover=cover,
        category=category,
        page=page,
        published_at=timezone.now(),
    )
    print(f"Done. NewsPost id={post.id}, slug={post.slug!r}, blocks={[b.block_type for b in page.blocks.all()]}")


if __name__ == "__main__":
    main()
