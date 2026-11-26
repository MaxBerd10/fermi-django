"""Builds plan.json from the database AFTER scripts 39-75 (read-only):
    python manage.py shell < deploy/content/yillik-hisobot-2026-76/make_plan.py
The block holds only text (no media ids), so the whole payload of each language is the fingerprint."""
import copy
import json
from pathlib import Path

from apps.content.migration_tools import sha
from apps.content.models import Page

LANGS = ("uz", "ru", "en")
OUT = Path("deploy/content/yillik-hisobot-2026-76/plan.json")
OLD = "[magistr.edu.uz](http://magistr.edu.uz/home)"
NEW = "[my.edu.uz](https://my.edu.uz)"
page = Page.objects.get(slug="magistratura-qabul-hujjatlari-toplami")
found = [b for b in page.blocks.order_by("order") if b.block_type == "paragraph" and all(OLD in (b.data[lang].get("text") or "") for lang in LANGS)]
assert len(found) == 1, len(found)
block = found[0]
new = copy.deepcopy(block.data)
for lang in LANGS:
    assert new[lang]["text"].count(OLD) == 1, lang
    new[lang]["text"] = new[lang]["text"].replace(OLD, NEW)
entries = [{"slug": page.slug, "order": block.order, "why": "master's admission: the portal is my.edu.uz (magistr.edu.uz was the 2024/25 platform)",
            "fp": {lang: sha(block.data[lang]) for lang in LANGS}, "data": new}]
OUT.write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "block ->", OUT, "#%d" % block.order)
for lang in LANGS:
    print(" ", lang, new[lang]["text"][:150])
