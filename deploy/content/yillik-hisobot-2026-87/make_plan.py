"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-87/make_plan.py"""
import json
import re
from pathlib import Path

from apps.content.models import Page

HERE = Path("deploy/content/yillik-hisobot-2026-87")
FINDINGS = json.loads((HERE / "findings.json").read_text(encoding="utf8"))
SLUGS = {  # the reviewer's page names are the first 28 letters of the slug in some columns: map by prefix
    "aholini-royxatga-olish-marka": "aholini-royxatga-olish-markazlashtirilgan-holda-amalga-oshiriladi",
    "ekofaol-yoshlar-loyihasi-nav": "ekofaol-yoshlar-loyihasi-navbatdagi-bosqich",
}


def pieces_of(part):
    return list(part["items"]) if "items" in part else [part.get("text", "")]


entries, problems = [], []
for f in FINDINGS:
    slug = SLUGS.get(f["page"], f["page"])
    new = f["new"]
    if f["page"] == "quyosh-panellari" and f["old"] == "Resolutionpresident":
        new = "Resolution of the president"
    block = Page.objects.get(slug=slug).blocks.get(order=f["block"])
    found = sum(p.count(f["old"]) for p in pieces_of(block.data[f["lang"]]))
    if found != 1:
        problems.append((slug, f["block"], f["lang"], f["old"], found)); continue
    entries.append({"slug": slug, "order": f["block"], "lang": f["lang"], "anchor": pieces_of(block.data["uz"])[0][:30], "old": f["old"], "new": new})
# the stray one-character link "[.](same address)" that follows the real link on three lines of 17-goals-of-un-policies
page = Page.objects.get(slug="17-goals-of-un-policies")
for order in (5, 12, 18):
    block = page.blocks.get(order=order)
    for lang in ("uz", "ru", "en"):
        text = block.data[lang]["text"]
        m = re.fullmatch(r"\[([^\]]+)\]\((https?://[^)]+)\)(\[\.\]\(\2\))", text)
        assert m, (order, lang)
        entries.append({"slug": page.slug, "order": order, "lang": lang, "anchor": pieces_of(block.data["uz"])[0][:30], "old": m.group(3), "new": ""})
for p in problems:
    print("NOT PLANNED", p)
(HERE / "plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections in", len({(e["slug"], e["order"]) for e in entries}), "blocks;", len(problems), "not planned")
