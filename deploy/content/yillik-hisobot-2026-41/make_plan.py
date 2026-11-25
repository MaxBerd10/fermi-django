"""Builds plan.json of script 41 (the four text pages of Institut haqida as typed blocks, the same structure in uz, ru and en).
Sources: the live pages (the fingerprints, the Uzbek Missiya, the English USMLE), the reviewed texts of the pending scripts 36, 37, 38 (their plan.json "set.html"),
the translation file common.ts (the USMLE heading). Run again right before applying on the server if a page changed:
    python deploy/content/yillik-hisobot-2026-41/make_plan.py"""
import hashlib
import json
import os
import re
import subprocess
import sys
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "deploy", "content"))
import _html_to_blocks as hb  # noqa: E402

LANGS = ("uz", "ru", "en")
SLUGS = {"missiya": "institut-missiyasi-va-kelajak-tasavvuri", "usmle": "usmle-dasturi", "ichki": "ichki-tartib-qoidalar", "kodeks": "institut-odob-axloq-kodeksi"}


def sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def live(slug):
    return json.loads(subprocess.run(["curl", "-s", "https://fermi.uz/api/v1/pages/" + slug], capture_output=True, text=True).stdout)


def set_html(n):
    """{lang: html} of the reviewed texts of a pending script (36 usmle, 37 missiya, 38 kodeks)."""
    plan = json.load(open(os.path.join(ROOT, "deploy", "content", f"yillik-hisobot-2026-{n}", "plan.json"), encoding="utf8"))
    return {entry["lang"]: entry["set"]["html"] for entry in plan}


def media_path(src):
    return unquote(urlsplit(src).path.split("/media/", 1)[1])


def heading(texts, level=2):
    return {"block_type": "heading", "data": {lang: {"text": texts[lang], "level": level} for lang in LANGS}}


def picture(path, alts):
    """A picture that already lies in the media folder (path relative to MEDIA_ROOT)."""
    return {"block_type": "image", "data": {lang: {"image_media": path, "alt": alts[lang]} for lang in LANGS}}


def repo_picture(file, alts):
    """A picture that is a file of the repository (frontend/public/images/<file>); the Image row of the same file is reused if script 40 made it."""
    return {"block_type": "image", "data": {lang: {"repo_image": file, "alt": alts[lang]} for lang in LANGS}}


def build(html):
    return hb.build(html, resolve_image=lambda src: "media:" + media_path(src))


def finish_images(blocks, alts):
    for block in blocks:
        if block["block_type"] == "image":
            for lang in LANGS:
                payload = block["data"][lang]
                payload["image_media"] = payload.pop("image_id")[len("media:"):]
                payload["alt"] = alts[lang]
    return blocks


def missiya():
    html = set_html(37)
    html["uz"] = live(SLUGS["missiya"])["blocks"][0]["data"]["uz"]["html"]
    blocks = build(html)
    headings = [b for b in blocks if b["block_type"] == "heading"]
    for block in headings[5:]:  # the six values under "Institute values" are items of that section, not sections of their own
        for lang in LANGS:
            block["data"][lang]["level"] = 3
    name = {lang: blocks[0]["data"][lang]["text"] for lang in LANGS}
    at = next(i for i, b in enumerate(blocks) if b["block_type"] == "list") + 1  # the institute's photo (it stood beside the opening text) after the first list
    return blocks[:at] + [repo_picture("institut-about.jpg", name)] + blocks[at:]


def step_headings(html, strip_label):
    """USMLE: every "USMLE Step N" paragraph becomes a level-3 heading + its paragraph (the label is cut from my own uz/ru texts; the English text keeps its sentence)."""
    soup = BeautifulSoup(html, "html.parser")
    for p in soup.find_all("p"):
        strong = p.find("strong")
        label = re.match(r"^\s*(USMLE Step \d)\b", p.get_text(" ", strip=True))
        if not label or strong is None:
            continue
        number = label.group(1)
        title = soup.new_tag("h3")
        title.string = number
        p.insert_before(title)
        if strip_label:
            strong.decompose()
    return str(soup)


def usmle():
    uz_ru = set_html(36)
    en = live(SLUGS["usmle"])["blocks"][0]["data"]["en"]["html"]
    soup = BeautifulSoup(en, "html.parser")
    for node in soup.find_all(["p", "div"]):  # Wikipedia leftovers: the "Step 3[edit]" line and the "Main article" hatnote
        text = node.get_text(" ", strip=True)
        if node.parent is not None and (re.match(r"^Step\s*\d\s*\[", text) or re.match(r"^\W*Main article", text)):
            node.decompose()
    for link in soup.find_all("a", href=re.compile(r"wikipedia\.org")):  # the words stay, the Wikipedia address does not (it would be printed after every word)
        link.unwrap()
    html = {"uz": step_headings(uz_ru["uz"], True), "ru": step_headings(uz_ru["ru"], True), "en": step_headings(str(soup), False)}
    blocks = build(html)
    intro = {"uz": "USMLE haqida", "ru": "Об экзамене USMLE", "en": "About the USMLE"}  # the old key usmle.introTitle of common.ts, which leaves with this script
    photo = picture("uploads/2026/09/USMLE_targibot_Ch1ZeuJ.jpg", {lang: "USMLE" for lang in LANGS})
    return [heading(intro)] + blocks[:2] + [photo] + blocks[2:]


PROFESSOR = {  # a line the Russian and English texts of the rules lack: the translation of the Uzbek line "professor-oʻqituvchilar - ..."
    "ru": "профессорско-преподавательский состав — работники, принятые на должности заведующего кафедрой, профессора, доцента, старшего преподавателя, преподавателя;",
    "en": "teaching staff — employees admitted to the positions of head of department, professor, associate professor, senior lecturer, lecturer;",
}
LINK_TAIL = re.compile(r"\s*\.{2,}\s*\.?\s*\w{2,3}\s*$")


def ichki():
    page = live(SLUGS["ichki"])["blocks"][0]["data"]
    units = {lang: hb.parse(page[lang]["html"]) for lang in LANGS}
    for lang in LANGS:  # the stray language marker after the link ("..uzb", ".. .ru", "... en")
        kind, payload, number = units[lang][-1]
        payload["text"] = LINK_TAIL.sub("", payload["text"])
    for lang in ("ru", "en"):
        rows = units[lang]
        at = next(i for i, (kind, payload, _) in enumerate(rows) if kind == "paragraph" and re.search(r"\s2\.\s", payload["text"]))
        head, tail = re.split(r"\s2\.\s", rows[at][1]["text"], maxsplit=1)
        rows[at:at + 1] = [("paragraph", {"text": head}, None), ("paragraph", {"text": "2. " + tail}, None)]
        concept = next(i for i, (kind, payload, _) in enumerate(rows) if kind == "paragraph" and payload["text"].startswith("1."))
        rows.insert(concept + 1, ("paragraph", {"text": PROFESSOR[lang]}, None))
    return hb.build_from_units(units)


def kodeks():
    html = set_html(38)
    blocks = build(html)
    alts = {"uz": "Odob-axloq kodeksi", "ru": "Кодекс этики", "en": "Code of Ethics"}
    return finish_images(blocks, alts)


def entry(key, blocks):
    page = live(SLUGS[key])
    old = page["blocks"][0]
    assert old["block_type"] == "raw_html" and old["order"] == 1, key
    return {"slug": SLUGS[key], "order": 1, "fp": {lang: sha(old["data"][lang]) for lang in LANGS}, "blocks": blocks}


if __name__ == "__main__":
    plan = [entry("missiya", missiya()), entry("usmle", usmle()), entry("ichki", ichki()), entry("kodeks", kodeks())]
    json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
    for item in plan:
        from collections import Counter
        print(item["slug"], len(item["blocks"]), dict(Counter(b["block_type"] for b in item["blocks"])))
