"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-90/make_plan.py"""
import json
from pathlib import Path

from apps.content.models import Page

SLUG, ORDER = "raqamli-talim-texnologiyalari-markazi", 2
FIXES = {"uz": ("25.0.2001-yildagi", "25.06.2001-yildagi"), "ru": ("от 25.05.2001 года", "от 25.06.2001 года"), "en": ("dated May 25, 2001", "dated June 25, 2001")}
block = Page.objects.get(slug=SLUG).blocks.get(order=ORDER)
anchor = block.data["uz"]["text"][:30]
entries = []
for lang, (old, new) in FIXES.items():
    assert block.data[lang]["text"].count(old) == 1, (lang, old)
    entries.append({"slug": SLUG, "order": ORDER, "lang": lang, "anchor": anchor, "old": old, "new": new})
Path("deploy/content/yillik-hisobot-2026-90/plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections")
