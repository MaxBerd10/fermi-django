"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-86/make_plan.py"""
import json
from pathlib import Path

from apps.content.models import Page

LEX = "https://lex.uz/docs/-3238680"
entries = []
block = Page.objects.get(slug="prezident-farmon-va-qarorlari").blocks.get(order=4)
assert block.block_type == "paragraph"
anchor = block.data["uz"]["text"][:30]
for lang in ("uz", "ru", "en"):
    text = block.data[lang]["text"]
    assert not text.startswith("[") and "](" not in text, lang
    entries.append({"slug": "prezident-farmon-va-qarorlari", "order": 4, "lang": lang, "anchor": anchor, "old": text, "new": "[%s](%s)" % (text, LEX)})
block = Page.objects.get(slug="institut-tuzilmasi").blocks.get(order=2)
assert block.block_type == "document"
anchor = block.data["uz"].get("caption", "")[:30]
for lang in ("uz", "ru", "en"):
    assert block.data[lang].get("style") == "button", lang
    entries.append({"slug": "institut-tuzilmasi", "order": 2, "lang": lang, "anchor": anchor, "style_old": "button", "style_new": "attachment"})
Path("deploy/content/yillik-hisobot-2026-86/plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "entries")
