"""Builds plan.json of script 40 from the live page and the three translation files (the texts are READ from common.ts, never retyped).
Run again right before applying on the server if the page changed:  python deploy/content/yillik-hisobot-2026-40/make_plan.py"""
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
LANGS = ("uz", "ru", "en")
SLUG = "institut-xaqida"


def sha(payload):
    import hashlib
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def strings(lang):
    source = open(os.path.join(ROOT, "frontend/src/i18n/local", lang, "common.ts"), encoding="utf8").read()
    out = {}
    for key in ("institut.fullName", "institut.aboutParagraph1", "institut.aboutParagraph2", "institut.ecaqaDocument"):
        match = re.search(r'^\s*"%s":\s*("(?:[^"\\]|\\.)*"),?\s*$' % re.escape(key), source, re.M)
        out[key] = json.loads(match.group(1))
        if lang == "uz":  # the site's one Uzbek apostrophe is U+02BB
            out[key] = out[key].replace("\u2018", "\u02bb").replace("\u2019", "\u02bb").replace("'", "\u02bb")
    return out


texts = {lang: strings(lang) for lang in LANGS}
page = json.loads(subprocess.run(["curl", "-s", "https://fermi.uz/api/v1/pages/" + SLUG], capture_output=True, text=True).stdout)
raw = next(b for b in page["blocks"] if b["block_type"] == "raw_html")
document = next(b for b in page["blocks"] if b["block_type"] == "document")
pick = lambda key: {lang: texts[lang][key] for lang in LANGS}
plan = [
    {"slug": SLUG, "kind": "about", "order": raw["order"], "fp": {lang: sha(raw["data"][lang]) for lang in LANGS},
     "heading": pick("institut.fullName"),
     "paragraphs": [pick("institut.aboutParagraph1"), pick("institut.aboutParagraph2")],
     "image": {"file": "institut-about.jpg", "alt": pick("institut.fullName")}},
    {"slug": SLUG, "kind": "caption", "document_id": document["data"]["uz"]["document_id"], "caption": pick("institut.ecaqaDocument")},
]
json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", len(plan), "entries")
