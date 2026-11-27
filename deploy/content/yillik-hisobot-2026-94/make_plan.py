"""Builds plan.json (read-only) from the Kongress page AFTER script 92:
    python manage.py shell < deploy/content/yillik-hisobot-2026-94/make_plan.py"""
import json
from pathlib import Path

from apps.content.migration_tools import sha
from apps.content.models import Page
from apps.media_lib.models import Image

LANGS = ("uz", "ru", "en")
SLUG = "kongress-2022-2024"
blocks = {b.order: b for b in Page.objects.get(slug=SLUG).blocks.all()}
TYPES = ["heading"] + ["image"] * 3 + ["embed", "document"] + ["heading"] + ["image"] * 4 + ["heading"] + ["image"] * 3 + ["embed", "document", "document"]
assert sorted(blocks) == list(range(1, 19)) and [blocks[o].block_type for o in range(1, 19)] == TYPES, [blocks[o].block_type for o in sorted(blocks)]
old = []
for order in range(1, 19):
    b = blocks[order]
    if b.block_type == "image":
        old.append({"order": order, "type": "image", "file_tail": Image.objects.get(pk=b.data["uz"]["image_id"]).file.name.rsplit("/", 1)[-1]})
    elif b.block_type == "document":
        old.append({"order": order, "type": "document", "caption": {lang: b.data[lang]["caption"] for lang in LANGS}})
    else:
        old.append({"order": order, "type": b.block_type, "fp": {lang: sha(b.data[lang]) for lang in LANGS}})


def sub(uz, ru, en):
    return {"block_type": "heading", "data": {"uz": {"text": uz, "level": 3}, "ru": {"text": ru, "level": 3}, "en": {"text": en, "level": 3}}}


plan = {
    "slug": SLUG,
    "old": old,
    "photos": sub("Plakatlar va fotosuratlar", "Плакаты и фотографии", "Posters and photos"),
    "video": sub("Video", "Видео", "Video"),
    "documents": {"block_type": "heading", "data": {"uz": {"text": "Hujjatlar", "level": 2}, "ru": {"text": "Документы", "level": 2}, "en": {"text": "Documents", "level": 2}}},
}
Path("deploy/content/yillik-hisobot-2026-94/plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf8")
print("plan written;", len(old), "old blocks")
