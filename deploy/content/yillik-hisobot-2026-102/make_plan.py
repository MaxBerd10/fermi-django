"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-102/make_plan.py

grant-taqsimoti (Magistratura): the same two 11-column tables and the same run-on notes as grantlar-taqsimoti (script 101). Every op replaces `count` consecutive blocks
starting at `order` ("old": what they are now, "new": what they become)."""
import json
import re
import subprocess
from pathlib import Path

LANGS = ("uz", "ru", "en")


def blocks_of(slug):
    return {b["order"]: b for b in json.loads(subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/" % slug], capture_output=True, text=True, check=True).stdout)["blocks"]}


def para(texts):
    return {"block_type": "paragraph", "data": {lang: {"text": texts[lang]} for lang in LANGS}}


def keep(b):
    return {"block_type": b["block_type"], "data": b["data"]}


ops = []

# ---- grantlar-taqsimoti ----------------------------------------------------------------------------------------------------------------------------
SLUG = "grant-taqsimoti"
b = blocks_of(SLUG)


def grouped(data):
    """The 11 long headers "<period> — <kind of grant> — <Jami / oʻzbek / rus>" become 3 group headings (period + kind) over 3 short columns each."""
    out = {}
    for lang in LANGS:
        headers = data[lang]["headers"]
        assert len(headers) == 11
        groups, leaf = [{"label": "", "span": 2}], headers[:2]
        for start in (2, 5, 8):
            parts = [h.split(" — ") for h in headers[start:start + 3]]
            assert all(len(p) == 3 for p in parts) and parts[0][:2] == parts[1][:2] == parts[2][:2], (lang, start)
            groups.append({"label": "%s — %s" % tuple(parts[0][:2]), "span": 3})
            leaf += [p[2][:1].upper() + p[2][1:] for p in parts]
        out[lang] = {**data[lang], "headers": leaf, "header_groups": groups}
    return out


for order in (2, 4):
    assert b[order]["block_type"] == "table"
    ops.append({"slug": SLUG, "order": order, "count": 1, "old": [keep(b[order])], "new": [{"block_type": "table", "data": grouped(b[order]["data"])}]})

# 6: the two notes (* and **) are one run-on line: two lines
assert b[6]["block_type"] == "paragraph"
two = {}
for lang in LANGS:
    parts = re.split(r"\s(?=\*\* )", b[6]["data"][lang]["text"])
    assert len(parts) == 2 and parts[0].startswith("* ") and parts[1].startswith("** "), (lang, parts)
    two[lang] = parts
ops.append({"slug": SLUG, "order": 6, "count": 1, "old": [keep(b[6])], "new": [para({lang: two[lang][0] for lang in LANGS}), para({lang: two[lang][1] for lang in LANGS})]})

Path("deploy/content/yillik-hisobot-2026-102/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ops), "ops")
for op in ops:
    print(op["slug"], "#%d" % op["order"], "%d -> %d blocks" % (op["count"], len(op.get("new", [0]))))
