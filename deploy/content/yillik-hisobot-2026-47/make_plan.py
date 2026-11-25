"""Builds plan.json of script 47 from the live pages: for each of the eight Institut binolari pages the fingerprint of its raw_html block and the pictures of the UZ text
(path in the media folder, alt text = the menu label of the page in each language, numbered when a page has several pictures). The UZ pictures are the base for all three
languages; where ru or en showed another set, the difference is stored in "diff" and printed by the script. Run again right before applying on the server if a page changed:
    python deploy/content/yillik-hisobot-2026-47/make_plan.py"""
import hashlib
import json
import os
import re
import subprocess
from urllib.parse import unquote, urlsplit

HERE = os.path.dirname(os.path.abspath(__file__))
LANGS = ("uz", "ru", "en")
SLUGS = ["rektorat", "oquv-binolari", "2-oquv-kampusi", "vivariy", "simulatsiya-markazi", "kongress-majmuasi", "sport-majmualari", "talabalar-turar-joylari-4"]
SECTION_MENU_ID = 1894  # the menu section "Institut binolari"


def sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def fetch(url):
    return json.loads(subprocess.run(["curl", "-s", url], capture_output=True, text=True).stdout)


def labels():
    found = {}

    def walk(items):
        for item in items:
            match = re.fullmatch(r"/blog/%d/([^/?#]+)" % SECTION_MENU_ID, item.get("url") or "")
            if match:
                found[match.group(1)] = item["label"]
            walk(item.get("children", []))

    menu = fetch("https://fermi.uz/api/v1/menu/?page_size=500")
    walk(menu if isinstance(menu, list) else menu.get("results", []))
    return found


def media_path(src):
    return unquote(urlsplit(src).path.split("/media/", 1)[1])


plan = []
menu = labels()
for slug in SLUGS:
    block = fetch("https://fermi.uz/api/v1/pages/" + slug)["blocks"][0]
    assert block["block_type"] == "raw_html" and block["order"] == 1, slug
    paths = {lang: [media_path(s) for s in re.findall(r'<img[^>]*\bsrc="([^"]+)"', block["data"][lang]["html"])] for lang in LANGS}
    assert paths["uz"], slug
    leftover = {lang: re.sub(r"<img[^>]*>|</?p>|</?div>|&nbsp;|\s+", "", block["data"][lang]["html"]) for lang in LANGS}
    assert not any(leftover.values()), (slug, leftover)  # nothing but pictures: no text is lost
    diff = {}
    for lang in ("ru", "en"):
        if paths[lang] != paths["uz"]:
            diff[lang] = {"was": paths[lang], "missing": [p for p in paths["uz"] if p not in paths[lang]], "extra": [p for p in paths[lang] if p not in paths["uz"]]}
    images = []
    for index, path in enumerate(paths["uz"], 1):
        suffix = f" ({index}/{len(paths['uz'])})" if len(paths["uz"]) > 1 else ""
        images.append({"media": path, "alt": {lang: menu[slug][lang] + suffix for lang in LANGS}})
    plan.append({"slug": slug, "order": 1, "fp": {lang: sha(block["data"][lang]) for lang in LANGS}, "images": images, "diff": diff})
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"], len(e["images"]), sorted(e["diff"])) for e in plan])
