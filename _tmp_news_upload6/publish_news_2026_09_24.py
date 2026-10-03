"""One-off script: publishes the 2026-09-24 batch of news posts through the
same Page/ContentBlock/Image pipeline the admin panel's news form uses (see
apps/admin_api/news_views.py) -- a cover photo plus a trailing `gallery`
block for the rest, exactly what the form's GalleryPicker saves.

Photos are read from PHOTO_ROOT/<post key>/ (default /tmp/fermi-news-2026-09-24;
transferred separately -- photos of people don't belong in git history).
All uz text uses U+02BB for oʻ/gʻ and U+02BC for the ʼ in eʼtibor/maʼlumot.
Posts are back-dated to 2026-09-24 (published_at), not "now".
Safe to re-run: posts whose slug already exists are skipped.

    set -a; source /etc/fermi-django.env; set +a
    .venv/bin/python _tmp_news_upload6/publish_news_2026_09_24.py
"""
import os
import re
import sys
from datetime import datetime

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

PHOTO_ROOT = os.environ.get("PHOTO_ROOT", "/tmp/fermi-news-2026-09-24")

POSTS = [
    {
        "key": "bitiruvchilar-seminari",
        "slug": "bitiruvchilar-uchun-mehnat-bozori-seminari-2026-09-24",
        "category": "tadbirlar",
        "published_at": datetime(2026, 9, 24, 12, 0),
        "cover": "1.jpg",  # wide shot of the whole hall
        "gallery": ["2.jpg", "3.jpg", "4.jpg", "5.jpg", "6.jpg"],
        "alt": "Bitiruvchi bosqich talabalari uchun mehnat bozori boʻyicha seminar",
        "title": {
            "uz": "Bitiruvchi bosqich talabalari uchun mehnat bozori imkoniyatlari boʻyicha seminar oʻtkazildi",
            "ru": "Для студентов выпускных курсов проведён семинар о возможностях на рынке труда",
            "en": "Seminar on Labor Market Opportunities Held for Graduating Students",
        },
        "paragraphs": {
            "uz": [
                "Fargʻona jamoat salomatligi tibbiyot institutining Tibbiy profilaktika fakultetida 2026/2027-oʻquv "
                "yilida Fundamental tibbiyot, Oliy hamshiralik ishi hamda Xalq tabobati yoʻnalishlarining bitiruvchi "
                "bosqich talabalari uchun seminar tashkil etildi.",
                "Seminarda bitiruvchilarning mehnat bozoridagi imkoniyatlarini kengaytirish, ularni munosib ish "
                "oʻrinlariga yoʻnaltirish hamda kasbiy faoliyatini boshlashga tayyorlash masalalariga alohida "
                "eʼtibor qaratildi.",
                "Tadbir davomida “Mehnat yarmarkasi” hamda “Kelajakka qadam” dasturi doirasida "
                "bitiruvchilarga mavjud boʻsh ish oʻrinlari, ishga joylashish tartibi, mehnat bozoridagi talab va "
                "takliflar, shuningdek, kasbiy rivojlanish imkoniyatlari haqida maʼlumotlar berildi.",
                "Seminar yakunida talabalar oʻzlarini qiziqtirgan savollariga mutaxassislardan javob oldilar hamda "
                "kelgusidagi kasbiy faoliyatlari yuzasidan zarur tavsiya va yoʻnalishlarga ega boʻldilar.",
            ],
            "ru": [
                "На факультете медицинской профилактики Ферганского медицинского института общественного здоровья "
                "в 2026/2027 учебном году для студентов выпускных курсов направлений «Фундаментальная медицина», "
                "«Высшее сестринское дело» и «Народная медицина» организован семинар.",
                "На семинаре особое внимание было уделено расширению возможностей выпускников на рынке труда, их "
                "ориентации на достойные рабочие места и подготовке к началу профессиональной деятельности.",
                "В ходе мероприятия в рамках программ «Ярмарка вакансий» и «Шаг в будущее» выпускникам была "
                "представлена информация об имеющихся вакансиях, порядке трудоустройства, спросе и предложении на "
                "рынке труда, а также возможностях профессионального развития.",
                "По итогам семинара студенты получили ответы специалистов на интересующие их вопросы, а также "
                "необходимые рекомендации и ориентиры для будущей профессиональной деятельности.",
            ],
            "en": [
                "A seminar was held at the Faculty of Medical Prevention of the Ferghana Medical Institute of Public "
                "Health for final-year students of the Fundamental Medicine, Higher Nursing, and Traditional "
                "Medicine programs in the 2026/2027 academic year.",
                "The seminar focused on expanding graduates' opportunities in the labor market, steering them toward "
                "suitable jobs, and preparing them to begin their professional careers.",
                "During the event, under the “Job Fair” and “Step to the Future” programs, "
                "graduates were given information on available vacancies, the employment process, labor-market "
                "supply and demand, and professional development opportunities.",
                "At the end of the seminar, students had their questions answered by specialists and received the "
                "recommendations and guidance they need for their future careers.",
            ],
        },
    },
    {
        "key": "workshop-day",
        "slug": "workshop-day-bitiruvchilarni-mehnat-bozoriga-tayyorlash-2026-09-24",
        "category": "tadbirlar",
        "published_at": datetime(2026, 9, 24, 13, 0),
        "cover": "1.jpg",  # wide hall shot with the "WORKSHOP DAY" title slide
        "gallery": ["2.jpg", "3.jpg", "4.jpg", "5.jpg"],
        "alt": "“Workshop Day” tadbiri — bitiruvchilarni mehnat bozoriga tayyorlash",
        "title": {
            "uz": "“Workshop Day” tadbirida bitiruvchilar mehnat bozoriga tayyorlandi",
            "ru": "В рамках «Workshop Day» выпускников подготовили к выходу на рынок труда",
            "en": "“Workshop Day” Prepares Graduates for the Labor Market",
        },
        "paragraphs": {
            "uz": [
                "Bitiruvchilarni mehnat bozoriga tayyorlash va ish beruvchilar bilan toʻgʻridan-toʻgʻri aloqa "
                "oʻrnatish maqsadida “Workshop Day” tadbiri oʻtkazildi. Tadbirda amaliy mashgʻulotlar, "
                "klinik holatlar tahlili hamda kasbiy mahorat darslari tashkil etildi.",
                "Yosh mutaxassislarga ishga qabul qilish jarayonlari va zamonaviy tibbiyotdagi talablar yuzasidan "
                "tushuntirishlar berildi.",
            ],
            "ru": [
                "В целях подготовки выпускников к рынку труда и налаживания прямых контактов с работодателями "
                "проведено мероприятие «Workshop Day». В его рамках были организованы практические занятия, разбор "
                "клинических случаев и занятия по профессиональному мастерству.",
                "Молодым специалистам разъяснили процесс приёма на работу и требования, предъявляемые в "
                "современной медицине.",
            ],
            "en": [
                "To prepare graduates for the labor market and help them connect directly with employers, a "
                "“Workshop Day” event was held, featuring hands-on sessions, clinical case analysis, and "
                "professional skills classes.",
                "Young specialists were given explanations of the hiring process and the requirements of modern "
                "medicine.",
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
        published_at=timezone.make_aware(spec["published_at"]),
    )
    print(f"[{spec['key']}] done: NewsPost id={post.id}, blocks={[b.block_type for b in page.blocks.all()]}")


if __name__ == "__main__":
    for spec in POSTS:
        publish(spec)
