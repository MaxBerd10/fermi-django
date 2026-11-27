"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-106/make_plan.py

The four faculty pages (Davolash ishi, Tibbiy profilaktika, Xalqaro fakultet, Pediatriya) are loose paragraphs whose structure the front end used to find by their database ids
(26890-26937): a bold paragraph meant "heading", "1.Urologiya ..." paragraphs meant "list". Now the structure is in the blocks themselves: bold heading paragraphs become headings,
numbered / dashed paragraphs become ONE list block (the number or dash removed), the clinics list gets the heading the code used to add (the title the page showed, a site text now removed), the pediatric programmes are put in the order the page showed them (pediatriya, stomatologiya, farmatsiya). No sentence is changed
or invented. Each op replaces ALL blocks of one page ("old": what they are now, "new": what they become)."""
import json
import re
from pathlib import Path
import subprocess

LANGS = ("uz", "ru", "en")
CLINICS_TITLE = {"uz": "Klinik amaliyot bazalari", "ru": "Базы клинической практики", "en": "Clinical training sites"}


def blocks_of(slug):
    d = json.loads(subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/" % slug], capture_output=True, text=True, check=True).stdout)
    return [b for b in sorted(d["blocks"], key=lambda b: b["order"])]


def keep(b):
    return {"block_type": b["block_type"], "data": b["data"]}


def heading(b):
    """A short lead-in paragraph (bold or not) becomes a level-3 heading (the closing colon of a lead-in to a list goes)."""
    assert b["block_type"] == "paragraph" and all(len(b["data"][l]["text"]) < 90 for l in LANGS), b["id"]
    return {"block_type": "heading", "data": {l: {"text": b["data"][l]["text"].strip().rstrip(":").strip(), "level": 3} for l in LANGS}}


def listing(group, pattern):
    items = {}
    for lang in LANGS:
        out = []
        for b in group:
            assert b["block_type"] == "paragraph" and not b["data"][lang].get("bold"), (b["id"], lang)
            text = re.sub(pattern, "", b["data"][lang]["text"]).strip()
            assert text, (b["id"], lang)
            out.append(text)
        items[lang] = {"items": out}
    return {"block_type": "list", "data": items}


NUMBER = r"^\s*\d+\s*[.)]\s*"
DASH = r"^\s*[-–—]\s*"
ops = []


def op(slug, old, new):
    assert len(new) >= len(old) - 7
    ops.append({"slug": slug, "order": 1, "count": len(old), "old": [keep(b) for b in old], "new": new})


# davolash-ishi: 4 paragraphs, then the list of clinics, which gets its heading
b = blocks_of("faculty-1")
assert [x["block_type"] for x in b] == ["paragraph"] * 4 + ["list"]
heading_block = {"block_type": "heading", "data": {l: {"text": CLINICS_TITLE[l], "level": 3} for l in LANGS}}
op("faculty-1", b, [keep(x) for x in b[:4]] + [heading_block, keep(b[4])])

# tibbiy-profilaktika: intro, [bold "attached departments" + 7 numbered paragraphs], 3 history paragraphs
b = blocks_of("faculty-2")
assert len(b) == 12 and all(x["block_type"] == "paragraph" for x in b)
op("faculty-2", b, [keep(b[0]), heading(b[1]), listing(b[2:9], NUMBER)] + [keep(x) for x in b[9:]])

# xalqaro-fakultet: 2 paragraphs, [bold "does the following" + 8 dashed paragraphs]
b = blocks_of("faculty-3")
assert len(b) == 11 and all(x["block_type"] == "paragraph" for x in b)
op("faculty-3", b, [keep(b[0]), keep(b[1]), heading(b[2]), listing(b[3:11], DASH)])

# pediatriya: faculty mission (stays a paragraph pair), the 3 programmes (heading + text; pediatriya, stomatologiya, farmatsiya), 4 text paragraphs, [bold departments + 7 numbered]
b = blocks_of("faculty-4")
assert len(b) == 20 and all(x["block_type"] == "paragraph" for x in b)
new = [keep(b[0]), keep(b[1])]
for first in (4, 6, 2):  # pediatriya (5,6), stomatologiya (7,8), farmatsiya (3,4) in 1-based order numbers
    new += [heading(b[first]), keep(b[first + 1])]
new += [keep(x) for x in b[8:12]] + [heading(b[12]), listing(b[13:20], NUMBER)]
op("faculty-4", b, new)

Path("deploy/content/yillik-hisobot-2026-106/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
for o in ops:
    print(o["slug"], o["count"], "->", len(o["new"]), "/".join(x["block_type"][0] for x in o["new"]))
