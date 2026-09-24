"""One-off script: publishes the 2026-09-18 forensic-medicine workshop
seminar as a NewsPost, following the exact same Page/ContentBlock/Image
pipeline apps/admin_api/news_views.py's AdminPostSerializer uses for a
real admin-panel submission (see apps/content/admin_content.py's
write_blocks_from_html) -- so this reads back through the public API and
admin panel identically to a post someone created by hand.

Run with the venv active, from anywhere (repo root is added to sys.path below):
    set -a; source /etc/fermi-django.env; set +a
    .venv/bin/python _tmp_news_upload/create_workshop_news.py
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

PHOTO_DIR = os.path.dirname(os.path.abspath(__file__))
PHOTO_FILES = ["1.jpg", "2.jpg", "3.jpg", "4.jpg", "5.jpg"]
ALT_TEXT = "Workshop-amaliy seminar, sud-tibbiy ekspertiza markazi ishtirokida"

SLUG = "sud-tibbiy-ekspertiza-workshop-2026-09-18"

TITLE_UZ = (
    "“Respublika sud-tibbiy ekspertiza ilmiy-amaliy markazi” Farg‘ona filiali "
    "ishtirokida workshop-amaliy seminar bo‘lib o‘tdi"
)
TITLE_RU = (
    "В ФерМИ прошёл практический семинар-воркшоп с участием Ферганского филиала "
    "Республиканского научно-практического центра судебно-медицинской экспертизы"
)
TITLE_EN = (
    "Practical Workshop Seminar Held with the Fergana Branch of the Republican "
    "Scientific-Practical Center for Forensic Medical Examination"
)

EXCERPT_UZ = (
    "Pediatriya fakulteti “Pediatriya” yo‘nalishi bitiruvchi bosqich talabalari uchun "
    "“Respublika sud-tibbiy ekspertiza ilmiy-amaliy markazi” Farg‘ona filiali "
    "mutaxassislari ishtirokida amaliy seminar tashkil etildi."
)
EXCERPT_RU = (
    "Для студентов выпускного курса направления «Педиатрия» педиатрического факультета "
    "организован практический семинар с участием специалистов Ферганского филиала "
    "Республиканского научно-практического центра судебно-медицинской экспертизы."
)
EXCERPT_EN = (
    "A practical seminar was organized for final-year students of the Pediatrics track "
    "at the Faculty of Pediatrics, with specialists from the Fergana branch of the "
    "Republican Scientific-Practical Center for Forensic Medical Examination."
)

BODY_UZ = (
    "2026-yil 18-sentyabr kuni Farg‘ona Jamoat salomatligi tibbiyot institutida "
    "“Respublika sud-tibbiy ekspertiza ilmiy-amaliy markazi” Farg‘ona filiali "
    "mutaxassislari ishtirokida workshop-amaliy seminar tashkil etildi. Tadbirda "
    "Pediatriya fakulteti “Pediatriya” yo‘nalishi bitiruvchi bosqich talabalari "
    "ishtirok etdi."
)
BODY_RU = (
    "18 сентября 2026 года в Фергана Джамоат Саломатлиги медицинском институте "
    "состоялся практический семинар-воркшоп с участием специалистов Ферганского "
    "филиала Республиканского научно-практического центра судебно-медицинской "
    "экспертизы. В мероприятии приняли участие студенты выпускного курса "
    "направления «Педиатрия» педиатрического факультета."
)
BODY_EN = (
    "On September 18, 2026, Fergana Public Health Medical Institute hosted a "
    "practical workshop seminar with specialists from the Fergana branch of the "
    "Republican Scientific-Practical Center for Forensic Medical Examination. "
    "Final-year students of the Pediatrics track at the Faculty of Pediatrics "
    "took part in the event."
)


def upload_images():
    images = []
    for fname in PHOTO_FILES:
        path = os.path.join(PHOTO_DIR, fname)
        with open(path, "rb") as fh:
            image = Image(alt_text=ALT_TEXT)
            image.file.save(fname, File(fh), save=True)
        images.append(image)
        print(f"  uploaded image #{image.id}: {image.file.name} ({image.width}x{image.height})")
    return images


def find_events_category():
    category = (
        NewsCategory.objects.filter(slug__icontains="tadbir").first()
        or NewsCategory.objects.filter(name_uz__icontains="tadbir").first()
    )
    if category:
        print(f"  using category: {category.name_uz!r} (id={category.id})")
    else:
        print("  WARNING: no 'Tadbirlar' (events) category found -- leaving category unset")
    return category


def build_html(body_text, images):
    parts = [f"<p>{body_text}</p>"]
    for image in images:
        parts.append(f'<p><img src="{image.file.url}" alt="{ALT_TEXT}" /></p>')
    return "\n".join(parts)


def main():
    if NewsPost.objects.filter(slug=SLUG).exists():
        print(f"NewsPost with slug={SLUG!r} already exists -- aborting (run is not needed twice).")
        return

    print("Uploading photos...")
    images = upload_images()

    print("Looking up category...")
    category = find_events_category()

    print("Creating page + content blocks...")
    page = Page.objects.create(slug=f"news-{SLUG}")
    write_blocks_from_html(page, {
        "uz": build_html(BODY_UZ, images),
        "ru": build_html(BODY_RU, images),
        "en": build_html(BODY_EN, images),
    })

    print("Creating news post...")
    post = NewsPost.objects.create(
        slug=SLUG,
        title_uz=TITLE_UZ,
        title_ru=TITLE_RU,
        title_en=TITLE_EN,
        excerpt_uz=EXCERPT_UZ,
        excerpt_ru=EXCERPT_RU,
        excerpt_en=EXCERPT_EN,
        cover=images[0],
        category=category,
        page=page,
        published_at=timezone.make_aware(timezone.datetime(2026, 9, 18, 12, 0)),
    )
    print(f"Done. NewsPost id={post.id}, slug={post.slug!r}")


if __name__ == "__main__":
    main()
