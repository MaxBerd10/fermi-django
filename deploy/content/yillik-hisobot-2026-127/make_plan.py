"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-127/make_plan.py

Spacing of visible texts (the user, 2026-11-28: "are the spaces between words in the translations in place? we must not be embarrassed"). An audit of 21,654 texts of the menu pages, the 30
department pages and the faculty pages in uz/ru/en found words and sentences run together and spaces where there must be none:
  * a space is missing after . , ; : between two words ("qaratilmoqda.Toshkent", "народу.особое", "ishi,Felman");
  * a space BEFORE , ; : ! ? ("Examination , USMLE");
  * a space just inside quotes ("kolleji ” nomi", "“ Rishton");
  * a number glued to the word it counts ("20tadan", "2019-2021yillar").
The rules (spacing_rules.py) never touch the address part of a [label](url) link, a web address or a file name (lex.uz, ariza.pdf), initials (M.R., t.f.d., Ph.D.) or numbers (3,5).
Tables are not edited by this script (a cell is a different kind of field): they are only counted.
Every op: {slug, order, lang, field, [index,] old, new}."""
import json
import re
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from spacing_rules import fix  # noqa: E402


def api(path):
    for _ in range(5):
        text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/" + path + ("&" if "?" in path else "?") + "v=127"], capture_output=True, text=True).stdout
        try:
            data = json.loads(text)
            if isinstance(data, dict) and set(data) <= {"error", "detail"}:
                time.sleep(5); continue
            time.sleep(0.5)
            return data
        except ValueError:
            time.sleep(3)
    raise SystemExit("API did not answer: " + path)


pages = {}  # page slug -> blocks
menu = api("menu/?page_size=500")
menu = menu if isinstance(menu, list) else menu.get("results", [])
menu_slugs = set()


def walk(items):
    for item in items:
        m = re.fullmatch(r"/blog/\d+/([^/?#]+)", item.get("url") or "")
        if m:
            menu_slugs.add(m.group(1))
        walk(item.get("children", []))


walk(menu)
for slug in sorted(menu_slugs):
    d = api("pages/%s/" % slug)
    pages[d["slug"]] = d["blocks"]
for dep in api("departments/"):
    d = api("departments/%s/" % dep["slug"])
    d = d.get("data", d)["page"]
    pages[d["slug"]] = d["blocks"]
faculties = api("faculties/")
for f in faculties if isinstance(faculties, list) else faculties.get("results", []):
    d = api("faculties/%s/" % f["slug"])
    d = d.get("data", d)
    pg = d.get("page") or {}
    if pg.get("slug"):
        pages[pg["slug"]] = pg.get("blocks", [])

# left for the staff: an abbreviation of an institute's name run together ('Tosh.Dav.TOni ...'): a space alone would not make it right
SKIP = {("department-8", 47)}
ops = []
table_cells = 0
for slug, blocks in sorted(pages.items()):
    for b in blocks:
        if (slug, b["order"]) in SKIP:
            continue
        for lang in ("uz", "ru", "en"):
            data = (b.get("data") or {}).get(lang) or {}
            kind = b["block_type"]
            if kind in ("heading", "paragraph") and isinstance(data.get("text"), str):
                new = fix(data["text"])
                if new != data["text"]:
                    ops.append({"slug": slug, "order": b["order"], "lang": lang, "field": "text", "old": data["text"], "new": new})
            elif kind == "list":
                for i, item in enumerate(data.get("items", [])):
                    if isinstance(item, str) and fix(item) != item:
                        ops.append({"slug": slug, "order": b["order"], "lang": lang, "field": "items", "index": i, "old": item, "new": fix(item)})
            elif kind == "document" and isinstance(data.get("caption"), str):
                new = fix(data["caption"])
                if new != data["caption"]:
                    ops.append({"slug": slug, "order": b["order"], "lang": lang, "field": "caption", "old": data["caption"], "new": new})
            elif kind == "table":
                for row in data.get("rows", []):
                    table_cells += sum(1 for c in row if isinstance(c, str) and fix(c) != c)

Path("deploy/content/yillik-hisobot-2026-127/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(pages), "pages;", len(ops), "texts to fix;", table_cells, "table cells with the same defects (left alone)")
by = {}
for o in ops:
    by[o["lang"]] = by.get(o["lang"], 0) + 1
print("by language:", by)
