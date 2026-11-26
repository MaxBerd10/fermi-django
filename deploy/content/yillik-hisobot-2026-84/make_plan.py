"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-84/make_plan.py"""
import json
import re
from pathlib import Path

from apps.content.models import Page

BLOCKS = [("ichki-tartib-qoidalar", 17), ("usmle-dasturi", 11)]
entries = []
for slug, order in BLOCKS:
    data = Page.objects.get(slug=slug).blocks.get(order=order).data
    anchor = data["uz"]["text"][:30]
    for lang in ("uz", "ru", "en"):
        text = data[lang]["text"]
        m = re.fullmatch(r"(.+?) (https://fermi\.uz/\S+)", text)
        assert m, (slug, lang)
        entries.append({"slug": slug, "order": order, "lang": lang, "anchor": anchor, "old": text, "new": "[%s](%s)" % (m.group(1), m.group(2))})
Path("deploy/content/yillik-hisobot-2026-84/plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections")
