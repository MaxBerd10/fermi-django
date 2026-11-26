"""Builds plan.json from the database AFTER scripts 39-79 (read-only):
    python manage.py shell < deploy/content/yillik-hisobot-2026-80/make_plan.py
findings.json: what an independent reviewer found when it read the Russian and English of 14 pages (dissertation defence, foreign students' housing, career day, anti-corruption
department, regional administrations, colleges, ...) against the Uzbek: 152 findings, many of them where the Russian/English blocks had shifted by one place and showed
another block's text. Checks before a finding is planned: its wording is in the block exactly once; every web address of the new wording is in the Uzbek text of the same
block; the findings about the date of the decree PF-4456 (the Uzbek and the reviewer disagree) are HELD."""
import json
import re
from pathlib import Path

from apps.content.models import Page

HERE = Path("deploy/content/yillik-hisobot-2026-80")
FINDINGS = json.loads((HERE / "findings.json").read_text(encoding="utf8"))
URL = re.compile(r"\]\((https?://[^)\s]+|/[^)\s]+)\)|(https?://[^\s)\]]+)")


def items(data):
    return list(data["items"]) if "items" in data else [data.get("text", "")]


entries, held, problems = [], [], []
for index, f in enumerate(FINDINGS):
    block = Page.objects.get(slug=f["page"]).blocks.get(order=f["block"])
    lang = f["lang"]
    if "4456" in f["current"] + f["fix"] + f["uz"]:
        held.append((index, f["page"], f["block"], lang, "decree PF-4456: the date differs from the Uzbek"))
        continue
    found = sum(piece.count(f["current"]) for piece in items(block.data[lang]))
    uz_text = " ".join(items(block.data["uz"]))
    bad_urls = [m.group(0) for m in URL.finditer(f["fix"]) if (m.group(1) or m.group(2)) not in uz_text]
    if found != 1 or block.block_type not in ("heading", "paragraph", "list") or bad_urls:
        problems.append((index, f["page"], f["block"], lang, found, bad_urls[:1]))
        continue
    entries.append({"slug": f["page"], "order": f["block"], "lang": lang, "anchor": items(block.data["uz"])[0][:30], "old": f["current"], "new": f["fix"], "why": f["severity"] + ": " + f["why"]})
for p in problems:
    print("NOT PLANNED", p)
for h in held:
    print("HELD", h)
(HERE / "plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections in", len({(e["slug"], e["order"]) for e in entries}), "blocks;", len(problems), "not planned;", len(held), "held")
