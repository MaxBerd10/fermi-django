"""Builds plan.json from the database AFTER scripts 39-74 (read-only):
    python manage.py shell < deploy/content/yillik-hisobot-2026-75/make_plan.py
titles.json holds the real name of each of the 19 annexes (read from the first page of every PDF; the Uzbek ones were checked against the PDF text)."""
import copy
import json
import re
from pathlib import Path

from apps.content.migration_tools import sha
from apps.content.models import Page

HERE = Path("deploy/content/yillik-hisobot-2026-75")
SLUG = "ssv-korrupsiyaga-qarshi-kurashish-siyosati"
LANGS = ("uz", "ru", "en")
TITLES = json.loads((HERE / "titles.json").read_text(encoding="utf8"))
entries = []
for block in Page.objects.get(slug=SLUG).blocks.order_by("order"):
    if block.block_type != "document":
        continue
    key = block.data["uz"].get("caption", "")
    if key not in TITLES:
        continue
    new = copy.deepcopy(block.data)
    for lang in LANGS:
        old = block.data[lang]["caption"]
        assert ":" not in old, (key, lang, old)  # not done already
        new[lang]["caption"] = "%s: %s" % (old, TITLES[key][lang])
    entries.append({"slug": SLUG, "order": block.order, "why": "%s: %s" % (key, TITLES[key]["uz"][:60]), "fp": {lang: sha(block.data[lang]) for lang in LANGS}, "data": new})
assert len(entries) == len(TITLES) == 19, (len(entries), len(TITLES))
(HERE / "plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "blocks")
