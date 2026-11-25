"""Builds plan.json of script 45: the title of the document card (the PDF card under the picture) in uz, ru and en on four pages of Institut haqida.
Until now the card showed the Uzbek file name in every language ("Lavozim yoriqnomasi", "struk-2023"). The caption is the page's menu name per language
(the corrected labels of script 44 where that script changes them). Run again right before applying if a page changed:
    python deploy/content/yillik-hisobot-2026-45/make_plan.py"""
import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LANGS = ("uz", "ru", "en")
SLUGS = ["lavozim-yoriqnomasi", "kredit-modul-nizomi", "institut-test-markazi-nizomi", "institut-tuzilmasi"]
LABELS_44 = json.load(open(os.path.join(ROOT, "deploy/content/yillik-hisobot-2026-44/plan.json"), encoding="utf8"))


def sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def fetch(url):
    return json.loads(subprocess.run(["curl", "-s", url], capture_output=True, text=True).stdout)


def menu_labels():
    found = {}

    def walk(items):
        for item in items:
            url = item.get("url") or ""
            if url.startswith("/blog/1827/"):
                found[url.rsplit("/", 1)[-1]] = item["label"]
            walk(item.get("children", []))

    menu = fetch("https://fermi.uz/api/v1/menu/?page_size=500")
    walk(menu if isinstance(menu, list) else menu.get("results", []))
    return found


labels = menu_labels()
plan = []
for slug in SLUGS:
    blocks = fetch("https://fermi.uz/api/v1/pages/" + slug)["blocks"]
    block = next(b for b in blocks if b["block_type"] == "document")
    assert not any("caption" in block["data"][lang] for lang in LANGS), slug
    caption = {lang: LABELS_44.get(slug, {}).get(lang) or labels[slug][lang] for lang in LANGS}
    db = {lang: {k: v for k, v in block["data"][lang].items() if k not in ("image", "document")} for lang in LANGS}
    plan.append({"slug": slug, "order": block["order"], "document_id": block["data"]["uz"]["document_id"], "fp": {lang: sha(db[lang]) for lang in LANGS}, "caption": caption})
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
for entry in plan:
    print(entry["slug"], entry["caption"])
