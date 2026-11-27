"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-88/make_plan.py"""
import json
from pathlib import Path

from apps.content.models import Page

SLUGS = ["17-goals-of-un-policies", "quyosh-panellari", "aholini-royxatga-olish-markazlashtirilgan-holda-amalga-oshiriladi",
         "ekofaol-yoshlar-loyihasi", "ekofaol-yoshlar-loyihasi-navbatdagi-bosqich", "ekofaol-xodim"]
entries = []
for slug in SLUGS:
    for block in Page.objects.get(slug=slug).blocks.filter(block_type="document").order_by("order"):
        anchor = block.data["uz"].get("caption", "")[:30]
        for lang in ("uz", "ru", "en"):
            old = block.data[lang].get("style")
            if old == "attachment" or old is None:
                continue
            entries.append({"slug": slug, "order": block.order, "lang": lang, "anchor": anchor, "style_old": old, "style_new": "attachment"})
Path("deploy/content/yillik-hisobot-2026-88/plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "entries in", len({(e["slug"], e["order"]) for e in entries}), "blocks")
