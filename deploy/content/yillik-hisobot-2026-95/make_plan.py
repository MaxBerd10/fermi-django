"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-95/make_plan.py"""
import json
from pathlib import Path

from apps.content.models import Page
from apps.media_lib.models import Image

LANGS = ("uz", "ru", "en")
SLUG = "17-goals-of-un-policies"
blocks = {b.order: b for b in Page.objects.get(slug=SLUG).blocks.all()}
TYPES = ["image"] * 3 + ["document"] * 17 + ["image", "document"]
assert sorted(blocks) == list(range(1, 23)) and [blocks[o].block_type for o in range(1, 23)] == TYPES
old = []
for order in range(1, 23):
    b = blocks[order]
    if b.block_type == "image":
        old.append({"order": order, "type": "image", "file_tail": Image.objects.get(pk=b.data["uz"]["image_id"]).file.name.rsplit("/", 1)[-1]})
    else:
        old.append({"order": order, "type": "document", "caption": {lang: b.data[lang]["caption"] for lang in LANGS}})
plan = {"slug": SLUG, "old": old,
        "documents": {"block_type": "heading", "data": {"uz": {"text": "Hujjatlar", "level": 2}, "ru": {"text": "Документы", "level": 2}, "en": {"text": "Documents", "level": 2}}}}
Path("deploy/content/yillik-hisobot-2026-95/plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf8")
print("plan written;", len(old), "old blocks")
