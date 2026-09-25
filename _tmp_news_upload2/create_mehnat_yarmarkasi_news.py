"""One-off script: publishes the 2026-09-21 "Kelajakka qadam" job fair as a
NewsPost through the same Page/ContentBlock/Image pipeline the admin panel's
own news form uses (see apps/admin_api/news_views.py). Photos are read from
/tmp/news-photos-2 (transferred separately -- photos of people don't belong
in git history). All uz text uses U+02BB for oʻ/gʻ.

    set -a; source /etc/fermi-django.env; set +a
    .venv/bin/python _tmp_news_upload2/create_mehnat_yarmarkasi_news.py
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

PHOTO_DIR = "/tmp/news-photos-2"
COVER_FILE = "5.jpg"  # the slide with the readable "Mehnat yarmarkasi" title
BODY_FILES = ["1.jpg", "2.jpg", "3.jpg", "4.jpg"]
ALT_TEXT = "“Kelajakka qadam” dasturi doirasidagi mehnat yarmarkasi"

SLUG = "kelajakka-qadam-mehnat-yarmarkasi-2026-09-21"

TITLE_UZ = "Bitiruvchi talabalar uchun “Kelajakka qadam” dasturi doirasida mehnat yarmarkasi oʻtkazildi"
TITLE_RU = "Для выпускников проведена ярмарка вакансий в рамках программы «Шаг в будущее»"
TITLE_EN = "Job Fair Held for Graduating Students Under the “Step to the Future” Program"

EXCERPT_UZ = (
    "Institutning 2026–2027 oʻquv yili bitiruvchi talabalari uchun ish beruvchi korxonalar, "
    "tijorat banklari va tadbirkorlar ishtirokida “Kelajakka qadam” dasturi doirasida "
    "mehnat yarmarkasi tashkil etildi."
)
EXCERPT_RU = (
    "Для выпускников института 2026–2027 учебного года организована ярмарка вакансий "
    "в рамках программы «Шаг в будущее» с участием работодателей, коммерческих банков и предпринимателей."
)
EXCERPT_EN = (
    "A job fair was organized under the “Step to the Future” program for the institute's "
    "2026–2027 graduating students, with employers, commercial banks and entrepreneurs taking part."
)

BODY_UZ = (
    "Fargʻona jamoat salomatligi tibbiyot instituti 2026–2027 oʻquv yilining bitiruvchi talabalari uchun "
    "2026-yil 21-sentyabr kuni ish beruvchi korxonalar, tijorat banklari hamda tadbirkorlar oʻrtasida "
    "“Kelajakka qadam” dasturi doirasida mehnat yarmarkasi tadbiri oʻtkazildi."
)
BODY_RU = (
    "21 сентября 2026 года в Ферганском медицинском институте общественного здоровья для выпускников "
    "2026–2027 учебного года прошла ярмарка вакансий в рамках программы «Шаг в будущее» "
    "с участием предприятий-работодателей, коммерческих банков и предпринимателей."
)
BODY_EN = (
    "On September 21, 2026, the Ferghana Medical Institute of Public Health held a job fair for its "
    "2026–2027 graduating students under the “Step to the Future” program, bringing together "
    "employers, commercial banks and entrepreneurs."
)


def load_image(fname):
    with open(os.path.join(PHOTO_DIR, fname), "rb") as fh:
        image = Image(alt_text=ALT_TEXT)
        image.file.save(fname, File(fh), save=True)
    print(f"  uploaded image #{image.id}: {image.file.name} ({image.width}x{image.height})")
    return image


def build_html(body_text, images):
    parts = [f"<p>{body_text}</p>"]
    for image in images:
        parts.append(f'<p><img src="{image.file.url}" alt="{ALT_TEXT}" /></p>')
    return "\n".join(parts)


def main():
    if NewsPost.objects.filter(slug=SLUG).exists():
        print(f"NewsPost {SLUG!r} already exists -- nothing to do.")
        return

    print("Uploading photos...")
    cover = load_image(COVER_FILE)
    body_images = [load_image(f) for f in BODY_FILES]

    category = (
        NewsCategory.objects.filter(slug__icontains="tadbir").first()
        or NewsCategory.objects.filter(name_uz__icontains="tadbir").first()
    )
    print(f"Category: {category.name_uz if category else 'NONE FOUND (left unset)'}")

    page = Page.objects.create(slug=f"news-{SLUG}")
    write_blocks_from_html(page, {
        "uz": build_html(BODY_UZ, body_images),
        "ru": build_html(BODY_RU, body_images),
        "en": build_html(BODY_EN, body_images),
    })

    post = NewsPost.objects.create(
        slug=SLUG,
        title_uz=TITLE_UZ, title_ru=TITLE_RU, title_en=TITLE_EN,
        excerpt_uz=EXCERPT_UZ, excerpt_ru=EXCERPT_RU, excerpt_en=EXCERPT_EN,
        cover=cover,
        category=category,
        page=page,
        published_at=timezone.make_aware(timezone.datetime(2026, 9, 21, 12, 0)),
    )
    print(f"Done. NewsPost id={post.id}, slug={post.slug!r}")


if __name__ == "__main__":
    main()
