"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-101/make_plan.py

Two pages of the Bakalavriat menu. Every op replaces `count` consecutive blocks starting at `order` ("old": what they are now, "new": what they become)."""
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

LANGS = ("uz", "ru", "en")


def blocks_of(slug):
    return {b["order"]: b for b in json.loads(subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/" % slug], capture_output=True, text=True, check=True).stdout)["blocks"]}


def para(texts):
    return {"block_type": "paragraph", "data": {lang: {"text": texts[lang]} for lang in LANGS}}


def keep(b):
    return {"block_type": b["block_type"], "data": b["data"]}


ops = []

# ---- talabalar-turar-joyi-uchun-ariza-yuborish -------------------------------------------------------------------------------------------------
SLUG = "talabalar-turar-joyi-uchun-ariza-yuborish"
b = blocks_of(SLUG)

# 1: the poster (the picture of the page) is moved by the article layout behind the text of the first section, and the line after it ("Arizalar qabuli ...") turns into its
# caption; as a gallery block of the style "plain" it stays at the top, where the page puts it, and the line stays a line
assert b[1]["block_type"] == "image"
# the picture is recognised by its file name (image ids differ between databases): apply.py builds the gallery from the ids it finds
ops.append({"slug": SLUG, "order": 1, "count": 1, "picture_tail": unquote(b[1]["data"]["uz"]["image"]["file"]).rsplit("/", 1)[-1]})

# 2: the address of the my.gov.uz service was glued to a "(" ... ")" pair of the pasted text: http://%28https://my.gov.uz/oz/service/870%29
new = {}
for lang in LANGS:
    text = b[2]["data"][lang]["text"]
    fixed, n = re.subn(r"\(http://%28https:?//my\.gov\.uz/oz/service/870%29\)", "(https://my.gov.uz/oz/service/870)", text)
    assert n == 1, (lang, text)
    new[lang] = fixed
ops.append({"slug": SLUG, "order": 2, "count": 1, "old": [keep(b[2])], "new": [para(new)]})

# 3: a stray "(" in the Uzbek line ("... ustuvorliklarga (ega talabgorlar ...")
uz = b[3]["data"]["uz"]["text"]
assert uz.count("ustuvorliklarga (ega ") == 1
ops.append({"slug": SLUG, "order": 3, "count": 1, "old": [keep(b[3])],
            "new": [{"block_type": "paragraph", "data": {**{lang: b[3]["data"][lang] for lang in ("ru", "en")}, "uz": {"text": uz.replace("ustuvorliklarga (ega ", "ustuvorliklarga ega ")}}}]})

# 5-7: the three percentages are a list
assert all(b[o]["block_type"] == "paragraph" for o in (5, 6, 7))
ops.append({"slug": SLUG, "order": 5, "count": 3, "old": [keep(b[o]) for o in (5, 6, 7)],
            "new": [{"block_type": "list", "data": {lang: {"items": [b[o]["data"][lang]["text"] for o in (5, 6, 7)]} for lang in LANGS}}]})

# 10-12: the title of the decree was cut into two headings ("... Vazirlar Mahkamasining" / "qarori") and a line: ONE heading and the line with a link to the decree (the decree
# No 376 of 14.08.2023 that the first paragraph names: lex.uz/uz/docs/-6568679 is its Uzbek text, lex.uz/uz/docs/6572093 its Russian one). (The heading also keeps the three
# paragraphs before it from being taken for the closing source / slogan / contacts of an annual report by the page layout: exactly three paragraphs after the last list.)
assert [b[o]["block_type"] for o in (10, 11, 12)] == ["heading", "heading", "paragraph"]
head = {"uz": "%s %s" % (b[10]["data"]["uz"]["text"], b[11]["data"]["uz"]["text"]),
        "ru": "%s %s" % (b[10]["data"]["ru"]["text"], b[11]["data"]["ru"]["text"]),
        "en": "%s of the %s" % (b[10]["data"]["en"]["text"], b[11]["data"]["en"]["text"])}
link = {"uz": "https://lex.uz/uz/docs/-6568679", "ru": "https://lex.uz/uz/docs/-6568679", "en": "https://lex.uz/uz/docs/6572093"}
ops.append({"slug": SLUG, "order": 10, "count": 3, "old": [keep(b[o]) for o in (10, 11, 12)],
            "new": [{"block_type": "heading", "data": {lang: {"text": head[lang], "level": 3} for lang in LANGS}},
                    para({lang: "[%s](%s)" % (b[12]["data"][lang]["text"], link[lang]) for lang in LANGS})]})

# ---- grantlar-taqsimoti ----------------------------------------------------------------------------------------------------------------------------
SLUG = "grantlar-taqsimoti"
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

Path("deploy/content/yillik-hisobot-2026-101/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ops), "ops")
for op in ops:
    print(op["slug"], "#%d" % op["order"], "%d -> %d blocks" % (op["count"], len(op.get("new", [0]))))
