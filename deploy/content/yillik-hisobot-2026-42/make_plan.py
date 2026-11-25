"""Builds plan.json of script 42 from the live pages: for each of the six image-only pages the fingerprint of its raw_html block and the pictures it holds
(path in the media folder, alt text = the menu label of the page in each language). Run again right before applying on the server if a page changed:
    python deploy/content/yillik-hisobot-2026-42/make_plan.py"""
import hashlib
import json
import os
import re
import subprocess
from urllib.parse import unquote, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ("uz", "ru", "en")
SLUGS = ["lavozim-yoriqnomasi", "kredit-modul-nizomi", "institut-test-markazi-nizomi", "talabalar-kengashi-nizomi",
         "institut-talim-yonalishlari-va-imkoniyatlari", "ecaqa-xalqaro-maxsus-akkreditatsiya"]
ABOUT_MENU_ID = 1827  # the menu section "Institut haqida"


def sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def fetch(url):
    return json.loads(subprocess.run(["curl", "-s", url], capture_output=True, text=True).stdout)


def labels():
    found = {}

    def walk(items):
        for item in items:
            match = re.fullmatch(r"/blog/%d/([^/?#]+)" % ABOUT_MENU_ID, item.get("url") or "")
            if match:
                found[match.group(1)] = item["label"]
            walk(item.get("children", []))

    menu = fetch("https://fermi.uz/api/v1/menu/?page_size=500")
    walk(menu if isinstance(menu, list) else menu.get("results", []))
    return found


plan = []
menu = labels()
for slug in SLUGS:
    block = fetch("https://fermi.uz/api/v1/pages/" + slug)["blocks"][0]
    assert block["block_type"] == "raw_html" and block["order"] == 1, slug
    sources = {lang: re.findall(r'<img[^>]*\bsrc="([^"]+)"', block["data"][lang]["html"]) for lang in LANGS}
    assert sources["uz"] and sources["uz"] == sources["ru"] == sources["en"], slug  # the same pictures in the three languages
    paths = [unquote(urlsplit(src).path.split("/media/", 1)[1]) for src in sources["uz"]]
    images = []
    for index, path in enumerate(paths, 1):
        suffix = f" ({index}/{len(paths)})" if len(paths) > 1 else ""
        images.append({"media": path, "alt": {lang: menu[slug][lang] + suffix for lang in LANGS}})
    plan.append({"slug": slug, "order": 1, "fp": {lang: sha(block["data"][lang]) for lang in LANGS}, "images": images})
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"], len(e["images"])) for e in plan])
