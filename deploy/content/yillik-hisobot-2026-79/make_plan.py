"""Builds plan.json from the database AFTER scripts 39-78 (read-only):
    python manage.py shell < deploy/content/yillik-hisobot-2026-79/make_plan.py
findings.json: what an independent reviewer found when it read the Russian and English of 27 admission pages against the Uzbek (157 findings). Each one was read
and judged before it was taken over; HELD (not applied here) are the ones that need a decision of people who know the facts or that move/add list items:
  * xalqaro-qabul-hujjatlar-toplami #7: the list of documents differs between the languages (translated + notarised passport, photo 3x4, AIDS-free certificate in ru/en;
    biometric passport, photo 3,5x4,5, certificate from the AIDS centre in uz): which one is true must be said by the admission office;
  * eng-kop-beriladigan-savollar #15 (an extra third item of the English list), yoriqnoma-klinik-ordinatura #18/#19 (a sentence that sits in the wrong block, a missing 4th item)."""
import json
from pathlib import Path

from apps.content.models import Page

HERE = Path("deploy/content/yillik-hisobot-2026-79")
FINDINGS = json.loads((HERE / "findings.json").read_text(encoding="utf8"))
HELD = {31, 84, 85, 86, 87, 88, 89, 90, 91, 137, 138, 139, 140}


def items(data):
    return list(data["items"]) if "items" in data else [data.get("text", "")]


entries, problems = [], []
for index, f in enumerate(FINDINGS):
    if index in HELD:
        continue
    block = Page.objects.get(slug=f["page"]).blocks.get(order=f["block"])
    lang = f["lang"]
    found = sum(piece.count(f["current"]) for piece in items(block.data[lang]))
    if found != 1 or block.block_type not in ("heading", "paragraph", "list"):
        problems.append((index, f["page"], f["block"], lang, found))
        continue
    anchor = items(block.data["uz"])[0][:30]
    entries.append({"slug": f["page"], "order": f["block"], "lang": lang, "anchor": anchor, "old": f["current"], "new": f["fix"], "why": f["severity"] + ": " + f["why"]})
for p in problems:
    print("NOT PLANNED", p)
(HERE / "plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections in", len({(e["slug"], e["order"]) for e in entries}), "blocks;", len(problems), "not planned;", len(HELD), "held")
