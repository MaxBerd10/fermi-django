"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-83/make_plan.py"""
import json
from pathlib import Path

from apps.content.migration_tools import sha
from apps.content.models import Page

LANGS = ("uz", "ru", "en")
SLUG, ORDER = "vrachlar-malakasini-oshirish-sertifikati", 2
block = Page.objects.get(slug=SLUG).blocks.get(order=ORDER)
assert block.block_type == "table"
fp = {lang: sha(block.data[lang]) for lang in LANGS}
title_rows = [i for i, r in enumerate(block.data["uz"]["rows"]) if len(r[0]) > 40 and all(not c.strip() for c in r[1:])]
assert title_rows == [56, 75, 88], title_rows
for lang in LANGS:  # the same rows in every language
    rows = block.data[lang]["rows"]
    assert [i for i, r in enumerate(rows) if len(r[0]) > 40 and all(not c.strip() for c in r[1:])] == title_rows, lang
cuts = [0] + title_rows + [len(block.data["uz"]["rows"])]
new = []
for n in range(len(cuts) - 1):
    start = cuts[n]
    if n > 0:
        new.append({"block_type": "heading", "data": {lang: {"text": block.data[lang]["rows"][start][0], "level": 3} for lang in LANGS}})
        start += 1
    new.append({"block_type": "table", "data": {lang: {"headers": block.data[lang]["headers"], "rows": block.data[lang]["rows"][start:cuts[n + 1]]} for lang in LANGS}})
total = sum(len(b["data"]["uz"]["rows"]) for b in new if b["block_type"] == "table")
assert total == len(block.data["uz"]["rows"]) - len(title_rows), total
Path("deploy/content/yillik-hisobot-2026-83/plan.json").write_text(json.dumps([{"slug": SLUG, "order": ORDER, "count": 1, "fp": [fp], "blocks": new}], ensure_ascii=False, indent=1), encoding="utf8")
print("1 entry:", [(b["block_type"], len(b["data"]["uz"].get("rows", []))) for b in new])
