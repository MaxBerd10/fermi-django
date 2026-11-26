"""Builds plan.json of script 68 (Abiturient: the regulation of admission of technical college graduates) from the live pages: pages whose three languages differ in structure. The Uzbek blocks are the base; the Russian and English blocks are aligned to
them (deploy/content/_align.py, _merge3.py); a block that a language lacks (or that only ru/en have) is filled by a text written by us in translations.json (key "slug|row|lang"); every such
text is listed in tarjima-kerak.md. Uzbek text has only U+02BB; a few old spellings (x for h) are fixed by the converter.
    .venv/bin/python deploy/content/yillik-hisobot-2026-68/make_plan.py"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _manual_pages import build  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
SLUGS = [
 "tibbiyot-texnikumi-biturvchilarini-qabul-qilish-nizomi"
]
path = os.path.join(HERE, "translations.json")
translations = json.load(open(path, encoding="utf8")) if os.path.exists(path) else {}
translations = {k: ([x.replace("ʼ", "ʻ") for x in v] if isinstance(v, list) else v.replace("ʼ", "ʻ")) if k.endswith("|uz") and not isinstance(v, dict) else v for k, v in translations.items()}  # one apostrophe in Uzbek
plan, needed, problems = build(SLUGS, translations)
if needed or problems:
    with open(os.path.join(HERE, "needed.txt"), "w", encoding="utf8") as handle:
        for key, source, text, kind in needed:
            handle.write("### %s  [%s, from %s]\n%s\n\n" % (key, kind, source, text))
    print("NOT READY: %d cells need a text (needed.txt), problems: %s" % (len(needed), problems))
    sys.exit(1)
for item in plan:
    for block in item["blocks"]:
        data = block["data"]["uz"]
        text = " ".join([data.get(k, "") for k in ("text", "caption", "alt")] + data.get("items", []) + [c for row in data.get("rows", []) for c in row] + data.get("headers", []))
        assert not re.search(r"['‘’`´ʼ]", re.sub(r"\]\([^)]*\)", "]", text)), (item["slug"], text[:100])
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", len(plan), "pages,", sum(len(e["blocks"]) for e in plan), "blocks")
