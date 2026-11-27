"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-116/make_plan.py

A scan of all 238 menu pages for links that stop in the middle of a text ("[2023 год -](file)Год заботы ..." : the file badge stood in the middle of the line and only half of it was a link)
or that touch the next word without a space found:
  * davlat-dasturlari #3 (the 2023 programme): ru and en were split like the 2024 / 2025 lines that script 108 mended: one link round the whole line now;
  * missing spaces after a link: oliy-talimning-davlat-talim-standarti #6 ("qaroriga|muvofiq"), qabul-nizomi #32 ("qarori|hamda") and #71 ("nizom|asosida").
(The other hits are Uzbek suffixes written right after a link -- "tmbm.ssv.uz|da", "...agentligi|ning" -- which are correct.) Every op: {slug, order, lang, field, old, new}."""
import json
import re
import subprocess
import time
from pathlib import Path

ops = []


def blocks_of(slug):
    for _ in range(5):
        text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/?v=116" % slug], capture_output=True, text=True).stdout
        try:
            return {b["order"]: b for b in json.loads(text)["blocks"]}
        except ValueError:
            time.sleep(3)
    raise SystemExit("API did not answer: " + slug)


def put(slug, order, lang, new, blocks):
    old = blocks[order]["data"][lang]["text"]
    assert old != new, (slug, order, lang)
    ops.append({"slug": slug, "order": order, "lang": lang, "field": "text", "old": old, "new": new})


b = blocks_of("davlat-dasturlari")
for lang, label_old, rest in (("ru", "2023 год -", "Год заботы о человеке и качественного образования"), ("en", "2023 -", "The Year of caring for people and quality education")):
    old = b[3]["data"][lang]["text"]
    m = re.fullmatch(r"\[%s\]\((\S+?)\)%s" % (re.escape(label_old), re.escape(rest)), old)
    assert m, old[:60]
    put("davlat-dasturlari", 3, lang, "[%s %s](%s)" % (label_old, rest, m.group(1)), b)

GLUED = re.compile(r"(\]\(\S+?\))([A-Za-zʻʼ‘’'])")
blocks = blocks_of("oliy-talimning-davlat-talim-standarti")
put("oliy-talimning-davlat-talim-standarti", 6, "uz", GLUED.sub(r"\1 \2", blocks[6]["data"]["uz"]["text"]), blocks)
blocks = blocks_of("qabul-nizomi")
for order in (32, 71):  # lists: item 0
    old = blocks[order]["data"]["uz"]["items"][0]
    assert GLUED.search(old)
    ops.append({"slug": "qabul-nizomi", "order": order, "lang": "uz", "field": "items", "index": 0, "old": old, "new": GLUED.sub(r"\1 \2", old)})

Path("deploy/content/yillik-hisobot-2026-116/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
for o in ops:
    print(o["slug"], o["order"], o["lang"], "|", o["old"][-60:].replace("\n", " "), "->", o["new"][-60:].replace("\n", " "))
