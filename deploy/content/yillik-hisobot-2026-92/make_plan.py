"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-92/make_plan.py
Records what the apply will check before it touches the page (the old structure), plus the new texts."""
import json
import re
from pathlib import Path
from urllib.parse import unquote

from apps.content.migration_tools import sha
from apps.content.models import Page

LANGS = ("uz", "ru", "en")
SLUG = "kongress-2022-2024"
page = Page.objects.get(slug=SLUG)
blocks = {b.order: b for b in page.blocks.all()}
assert sorted(blocks) == list(range(1, 16))
TYPES = ["image"] * 3 + ["raw_html"] + ["image"] * 7 + ["paragraph", "paragraph", "raw_html", "document"]
assert [blocks[o].block_type for o in range(1, 16)] == TYPES, [blocks[o].block_type for o in range(1, 16)]

# the old structure: images by the file name, the text blocks by their whole payload, the document by its caption
old = []
for order in range(1, 16):
    b = blocks[order]
    if b.block_type == "image":
        from apps.media_lib.models import Image
        old.append({"order": order, "type": "image", "file_tail": Image.objects.get(pk=b.data["uz"]["image_id"]).file.name.rsplit("/", 1)[-1]})
    elif b.block_type == "document":
        old.append({"order": order, "type": "document", "caption": {lang: b.data[lang]["caption"] for lang in LANGS}})
    else:
        old.append({"order": order, "type": b.block_type, "fp": {lang: sha(b.data[lang]) for lang in LANGS}})


def heading(uz, ru, en):
    return {"block_type": "heading", "data": {"uz": {"text": uz, "level": 2}, "ru": {"text": ru, "level": 2}, "en": {"text": en, "level": 2}}}


def embed(video_id, title):
    return {"block_type": "embed", "data": {lang: {"provider": "youtube", "video_id": video_id, "title": title} for lang in LANGS}}


def link_target(order):
    m = re.search(r"\]\(https://fermi\.uz/media/([^)]+\.pdf)\)", blocks[order].data["uz"]["text"])
    assert m, order
    return unquote(m.group(1))


plan = {
    "slug": SLUG,
    "old": old,
    "heading": {
        2024: heading("IV Xalqaro ilmiy-amaliy konferensiya, 2024-yil 10–11 may", "IV Международная научно-практическая конференция, 10–11 мая 2024 года", "IV International Scientific and Practical Conference, 10–11 May 2024"),
        2023: heading("III Xalqaro ilmiy-amaliy konferensiya, 2023-yil 6-may", "III Международная научно-практическая конференция, 6 мая 2023 года", "III International Scientific and Practical Conference, 6 May 2023"),
        2022: heading("II Xalqaro ilmiy-amaliy konferensiya, 2022-yil 6-may", "II Международная научно-практическая конференция, 6 мая 2022 года", "II International Scientific and Practical Conference, 6 May 2022"),
    },
    "video_2024": embed("Mg6MBqg4f5o", "Dermatovenerologiya va dermatoonkopatologiyada diagnostika IV xalqaro ilmiy-amaliy konferensiya"),
    "video_2022": embed("rGQRdpp6YfI", "Fargʻona jamoat salomatligi tibbiyot instituti 6 may 2022 yilda oʻtkaziladigan xalqaro konferensiya"),
    "proceedings_caption": {"uz": "Konferensiya materiallari to‘plami, 2024-yil may".replace("‘", "ʻ"), "ru": "Сборник материалов конференции, Фергана, май 2024", "en": "Conference proceedings, Fergana, May 2024"},
    "documents": [
        {"media_path": link_target(12), "captions": {"uz": "Konferensiya axborot xati, 2022-yil 6-may (rus tilida)", "ru": "Информационное письмо конференции, 6 мая 2022 года", "en": "Conference information letter, 6 May 2022"}},
        {"media_path": link_target(13), "captions": {"uz": "Konferensiya dasturi, 2022-yil 6-may (kirill alifbosida)", "ru": "Программа конференции (на узбекском языке, кириллицей)", "en": "Conference programme (in Uzbek, Cyrillic script)"}},
    ],
    "menu": {"old_label_uz": "Konrgress dasturi", "new_label_uz": "Kongress dasturi"},
}
Path("deploy/content/yillik-hisobot-2026-92/plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf8")
print("plan written;", len(old), "old blocks; documents:", [d["media_path"][-40:] for d in plan["documents"]])
