"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-82/make_plan.py"""
import json
from pathlib import Path

from apps.content.models import Page

FIXES = [
    ("bilim-yurtlari", 12, "Nukus shakar", "Nukus shahar"),
    ("chet-el-talabalari-turar-joyi-togrisidagi-malumotlar", 8, "ush fuqarolar", "shu fuqarolar"),
    ("fargona-shahar-abu-ali-ibn-sino-nomidagi-jamoat-salomatligi-texnikumi", 2, "saqlasʻh", "saqlash"),
]
entries = []
for slug, order, old, new in FIXES:
    uz = Page.objects.get(slug=slug).blocks.get(order=order).data["uz"]
    pieces = uz["items"] if "items" in uz else [uz.get("text", "")]
    assert sum(p.count(old) for p in pieces) == 1, (slug, order)
    entries.append({"slug": slug, "order": order, "lang": "uz", "anchor": pieces[0][:30], "old": old, "new": new})
Path("deploy/content/yillik-hisobot-2026-82/plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections")
