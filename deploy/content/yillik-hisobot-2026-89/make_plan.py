"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-89/make_plan.py"""
import json
from pathlib import Path

from apps.content.migration_tools import sha
from apps.content.models import Page

LANGS = ("uz", "ru", "en")
SLUG, FIRST, LAST = "aholini-royxatga-olish-markazlashtirilgan-holda-amalga-oshiriladi", 3, 9
page = Page.objects.get(slug=SLUG)
blocks = [page.blocks.get(order=o) for o in range(FIRST, LAST + 1)]
assert all(b.block_type == "paragraph" for b in blocks)
entry = {"slug": SLUG, "order": FIRST, "count": len(blocks), "fp": [{lang: sha(b.data[lang]) for lang in LANGS} for b in blocks],
         "blocks": [{"block_type": "list", "data": {lang: {"items": [b.data[lang]["text"] for b in blocks]} for lang in LANGS}}]}
Path("deploy/content/yillik-hisobot-2026-89/plan.json").write_text(json.dumps([entry], ensure_ascii=False, indent=1), encoding="utf8")
print("1 entry:", len(blocks), "paragraphs -> 1 list")
