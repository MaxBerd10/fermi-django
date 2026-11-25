"""Builds plan.json of script 46: "Institut konferensiyalari" (4 pages) from raw HTML to typed blocks.
 * Xalqaro konferensiyalar / Respublika ilmiy konferensiyalar: every linked title (a PDF of proceedings) becomes a `document` block; the three languages are paired by the
   ADDRESS of the file (the titles differ per language, the file does not); a title a language lacks falls back to the Uzbek-page title and is listed in tarjima-kerak.md;
   a link whose file is gone (api.fermi.uz answers 410) becomes a paragraph with the title only (listed in oʻlik-havolalar); the YouTube embed stays a raw_html block (first).
 * Tillar konferensiyasi / Konferensiya toʻplami: the one text line becomes a paragraph (the PDF card they already have stays).
Run again right before applying if a page changed:  python deploy/content/yillik-hisobot-2026-46/make_plan.py"""
import hashlib
import json
import os
import re
import subprocess
from collections import OrderedDict
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup

HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ("uz", "ru", "en")
PAGES = ["ilmiy-konferensiyalar", "respublika-ilmiy-konferensiyalari", "tillar-konferensiyasi-materiallari-15102025", "konferensiya-toplami-11122023"]
ZERO_WIDTH = re.compile("[​-‍﻿]")


def sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def fetch(slug):
    return json.loads(subprocess.run(["curl", "-s", "https://fermi.uz/api/v1/pages/" + slug], capture_output=True, text=True).stdout)


def clean(text):
    return re.sub(r"\s+", " ", ZERO_WIDTH.sub("", text)).strip()


def media_path(href):
    parts = urlsplit(href)
    if parts.netloc not in ("fermi.uz", "www.fermi.uz") or "/media/" not in parts.path:
        return None
    return unquote(parts.path.split("/media/", 1)[1])


def link_blocks(page):
    """(blocks, tarjima_kerak, dead) of one list page."""
    raw = page["blocks"][0]["data"]
    soups = {lang: BeautifulSoup(raw[lang]["html"], "html.parser") for lang in LANGS}
    titles = {lang: OrderedDict() for lang in LANGS}  # href -> first title in that language
    for lang, soup in soups.items():
        for anchor in soup.find_all("a", href=True):
            text = clean(anchor.get_text(" ", strip=True))
            if text:
                titles[lang].setdefault(anchor["href"], text)
    order = list(titles["uz"]) + [h for lang in ("ru", "en") for h in titles[lang] if h not in titles["uz"]]
    order = list(OrderedDict.fromkeys(order))
    blocks, need, dead = [], [], []
    for href in order:
        caption = {}
        for lang in LANGS:
            if href in titles[lang]:
                caption[lang] = titles[lang][href]
            else:
                caption[lang] = titles["uz"].get(href) or next(t[href] for t in titles.values() if href in t)
                need.append((lang, href, caption[lang]))
        path = media_path(href)
        if path is None:
            dead.append((href, caption["uz"]))
            blocks.append({"block_type": "paragraph", "data": {lang: {"text": caption[lang]} for lang in LANGS}})
        else:
            blocks.append({"block_type": "document", "data": {lang: {"media": path, "caption": caption[lang]} for lang in LANGS}})
    frames = {lang: soup.find("iframe") for lang, soup in soups.items()}
    if all(frames.values()):
        video = {lang: {"html": '<p><iframe frameborder="0" height="360" src="%s" width="640" title="YouTube"></iframe></p>' % frames[lang]["src"]} for lang in LANGS}
        blocks.insert(0, {"block_type": "raw_html", "data": video})
    return blocks, need, dead


def text_blocks(page):
    raw = page["blocks"][0]["data"]
    texts = {lang: clean(BeautifulSoup(raw[lang]["html"], "html.parser").get_text(" ", strip=True)) for lang in LANGS}
    assert all(texts.values()), texts
    return [{"block_type": "paragraph", "data": {lang: {"text": texts[lang]} for lang in LANGS}}]


plan, report = [], []
for slug in PAGES:
    page = fetch(slug)
    old = page["blocks"][0]
    assert old["block_type"] == "raw_html" and old["order"] == 1, slug
    if slug in PAGES[:2]:
        blocks, need, dead = link_blocks(page)
    else:
        blocks, need, dead = text_blocks(page), [], []
    plan.append({"slug": slug, "order": 1, "fp": {lang: sha(old["data"][lang]) for lang in LANGS}, "blocks": blocks})
    report.append((slug, need, dead))
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
with open(os.path.join(HERE, "tarjima-kerak.md"), "w", encoding="utf8") as out:
    out.write("# Konferensiyalar: tarjima va oʻlik havolalar (46-skript)\n\nHar bir qator: sahifa, til, fayl manzili. Ushbu tilda sarlavha yoʻq edi, oʻzbekcha sahifadagi sarlavha qoʻyildi.\n\n")
    for slug, need, dead in report:
        out.write("## %s\n\n" % slug)
        for lang, href, text in need:
            out.write("- [%s] `%s` -> «%s»\n" % (lang, unquote(href).rsplit("/", 1)[-1], text))
        for href, text in dead:
            out.write("- OʻLIK havola (fayl yoʻq, sarlavha matn boʻlib qoldi): `%s` «%s»\n" % (unquote(href), text))
        out.write("\n")
for entry in plan:
    kinds = [b["block_type"] for b in entry["blocks"]]
    print(entry["slug"], len(kinds), {k: kinds.count(k) for k in set(kinds)})
