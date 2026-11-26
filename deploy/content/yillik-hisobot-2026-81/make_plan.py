"""Builds plan.json from the database AFTER scripts 39-80 (read-only):
    python manage.py shell < deploy/content/yillik-hisobot-2026-81/make_plan.py
The SECOND review pass: the pages corrected by scripts 79 and 80 were read again by independent reviewers (E2: 27 admission pages, 37 findings left of 157; F2: 14 pages, 19
findings left of 152). Held: the five E2 findings that would restore a sentence which the Uzbek repeats in the next block (a choice, not an error); the date of the decree PF-4456 is
kept as the Uzbek says it (24 June) in both languages, because the reviewers disagreed with each other and with the Uzbek and there is no source."""
import json
from pathlib import Path

from apps.content.models import Page

HERE = Path("deploy/content/yillik-hisobot-2026-81")
E2 = json.loads((HERE / "findings_E2.json").read_text(encoding="utf8"))
F2 = json.loads((HERE / "findings_F2.json").read_text(encoding="utf8"))
HELD_E2 = {19, 20, 27, 28, 30}


def items(data):
    return list(data["items"]) if "items" in data else [data.get("text", "")]


def split_items(f):
    """A finding on a whole list is written as 'item ‖ item ‖ ...': one correction per item."""
    if " ‖ " not in f["current"]:
        return [f]
    old_items, new_items = f["current"].split(" ‖ "), f["fix"].split(" ‖ ")
    assert len(old_items) == len(new_items), f["page"]
    return [dict(f, current=a, fix=b) for a, b in zip(old_items, new_items)]


work = [("E2", i, g) for i, f in enumerate(E2) if i not in HELD_E2 for g in split_items(f)] + [("F2", i, g) for i, f in enumerate(F2) for g in split_items(f)]
entries, problems = [], []
for tag, index, f in work:
    fix = f["fix"]
    if tag == "F2" and "24 июля 2012" in fix:
        fix = fix.replace("24 июля 2012", "24 июня 2012")  # as the Uzbek says
    block = Page.objects.get(slug=f["page"]).blocks.get(order=f["block"])
    lang = f["lang"]
    found = sum(piece.count(f["current"]) for piece in items(block.data[lang]))
    if found != 1 or block.block_type not in ("heading", "paragraph", "list"):
        problems.append((tag, index, f["page"], f["block"], lang, found))
        continue
    entries.append({"slug": f["page"], "order": f["block"], "lang": lang, "anchor": items(block.data["uz"])[0][:30], "old": f["current"], "new": fix, "why": f["severity"] + ": " + f["why"]})
for p in problems:
    print("NOT PLANNED", p)
(HERE / "plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections in", len({(e["slug"], e["order"]) for e in entries}), "blocks;", len(problems), "not planned;", len(HELD_E2), "held")
