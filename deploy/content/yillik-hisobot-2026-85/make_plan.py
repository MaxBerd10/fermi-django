"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-85/make_plan.py"""
import json
from pathlib import Path

from apps.content.models import Page

HERE = Path("deploy/content/yillik-hisobot-2026-85")
FINDINGS = json.loads((HERE / "findings.json").read_text(encoding="utf8"))
SLUG = "institut-odob-axloq-kodeksi"
HELD = {2, 37, 45, 67, 72, 73}  # 'medium' findings (and the scrambled 29th-article heading)
SPACE_ONLY = {"block": 120, "old": "modda . Kodeksga rioya", "new": "modda. Kodeksga rioya"}  # the certain part of finding 72
page = Page.objects.get(slug=SLUG)
work = [f for i, f in enumerate(FINDINGS) if i not in HELD] + [SPACE_ONLY]
entries = []
for f in work:
    uz = page.blocks.get(order=f["block"]).data["uz"]
    pieces = uz["items"] if "items" in uz else [uz.get("text", "")]
    assert sum(p.count(f["old"]) for p in pieces) == 1, f
    entries.append({"slug": SLUG, "order": f["block"], "lang": "uz", "anchor": pieces[0][:30], "old": f["old"], "new": f["new"]})
(HERE / "plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections in", len({e["order"] for e in entries}), "blocks")
