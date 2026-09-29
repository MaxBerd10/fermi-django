"""One-off script: publishes the "Ekofaol yoshlar" environmental-awareness
event as a NewsPost, through the same Page/ContentBlock/Image pipeline the
admin panel's own news form uses (see apps/admin_api/news_views.py). Photos
are read from /tmp/ekofaol-photos (transferred separately -- photos of
people don't belong in git history). All uz text uses U+02BB for oʻ/gʻ.

    set -a; source /etc/fermi-django.env; set +a
    .venv/bin/python _tmp_news_upload4/create_ekofaol_yoshlar_news.py
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

PHOTO_DIR = "/tmp/ekofaol-photos"
COVER_FILE = "1.jpg"  # the "EKO FAOL YOSHLAR" LOYIHASI title-slide photo
BODY_FILES = [f"{i}.jpg" for i in range(2, 11)]
ALT_TEXT = "“Ekofaol yoshlar” loyihasi doirasidagi targʻibot-tashviqot tadbiri"

SLUG = "ekofaol-yoshlar-targibot-tadbiri-2026-09-29"

TITLE_UZ = "Tibbiy profilaktika va jamoat salomatligi fakultetida “Ekofaol yoshlar” loyihasi doirasida targʻibot-tashviqot tadbiri oʻtkazildi"
TITLE_RU = "На факультете медицинской профилактики и общественного здоровья проведено просветительское мероприятие в рамках проекта «Экоактивная молодёжь»"
TITLE_EN = "Faculty of Medical Prevention and Public Health Holds Awareness Event Under the “Eco-Active Youth” Project"

EXCERPT_UZ = (
    "Tyutor M.Tojiboyeva tashabbusi bilan talabalarning ekologik madaniyatini yuksaltirish va tabiatni asrashga "
    "faol jalb etish maqsadida “Ekofaol yoshlar” loyihasi doirasida tadbir tashkil etildi."
)
EXCERPT_RU = (
    "По инициативе тьютора М.Тожибоевой в рамках проекта «Экоактивная молодёжь» проведено мероприятие, "
    "направленное на повышение экологической культуры студентов и их активное вовлечение в охрану природы."
)
EXCERPT_EN = (
    "At the initiative of tutor M. Tojiboyeva, an event was held under the “Eco-Active Youth” project to "
    "raise students' environmental awareness and actively involve them in protecting nature."
)

BODY_UZ = (
    "Tibbiy profilaktika va jamoat salomatligi fakultetida tyutor M.Tojiboyeva tashabbusi bilan talabalarning "
    "ekologik madaniyatini yuksaltirish, atrof-muhitga masʼuliyatli munosabatini shakllantirish hamda yoshlarni "
    "tabiatni asrash va ekologik muammolarning oldini olishga faol jalb etish maqsadida “Ekofaol yoshlar” "
    "loyihasi doirasida targʻibot-tashviqot tadbiri oʻtkazildi. Tadbir davomida yoshlarning ekologik bilimlarini "
    "oshirishga qaratilgan suhbatlar, savol-javoblar hamda amaliy targʻibot ishlari tashkil etildi. Talabalar "
    "tomonidan hududlarni obodonlashtirish, tozalikni saqlash va daraxtlarni asrash boʻyicha tashabbuslar ilgari "
    "surildi."
)
BODY_RU = (
    "На факультете медицинской профилактики и общественного здоровья по инициативе тьютора М.Тожибоевой в целях "
    "повышения экологической культуры студентов, формирования у них ответственного отношения к окружающей "
    "среде, а также активного вовлечения молодёжи в охрану природы и предотвращение экологических проблем "
    "проведено просветительское мероприятие в рамках проекта «Экоактивная молодёжь». В ходе мероприятия были "
    "организованы беседы, вопросы-ответы и практические просветительские работы, направленные на повышение "
    "экологических знаний молодёжи. Студенты выступили с инициативами по благоустройству территорий, "
    "поддержанию чистоты и сохранению деревьев."
)
BODY_EN = (
    "At the Faculty of Medical Prevention and Public Health, tutor M. Tojiboyeva initiated an awareness event "
    "under the “Eco-Active Youth” project, aimed at raising students' environmental culture, fostering "
    "a responsible attitude toward the environment, and actively engaging young people in protecting nature and "
    "preventing environmental problems. The event included discussions, Q&A sessions, and practical outreach "
    "activities aimed at deepening students' environmental knowledge. Students put forward initiatives for "
    "improving local areas, maintaining cleanliness, and protecting trees."
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
        published_at=timezone.now(),
    )
    print(f"Done. NewsPost id={post.id}, slug={post.slug!r}")


if __name__ == "__main__":
    main()
