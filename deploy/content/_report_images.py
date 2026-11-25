"""Builds plan.json of script 39 from the live pages: every raw_html block of the nine report pages is a run of report photos (<img src="/images/hisobot/...">),
the report PDF link, or one line of links. Usage (from the repository root):
    .venv/bin/python deploy/content/_report_images.py deploy/content/yillik-hisobot-2026-39/plan.json
The live API is the source of truth for the text (alt texts, link texts) in the three languages; the fingerprints keep apply from touching a block edited since."""
import hashlib
import html
import json
import os
import re
import subprocess
import sys

SLUGS = [
    "yillik-hisobot-2026",
    "reyting-va-akkreditatsiya",
    "strategik-maqsadlar-2027",
    "xalqaro-hamkorlik-va-investitsiyalar",
    "ilmiy-va-innovatsion-faoliyat",
    "suniy-intellekt-tizimlari",
    "2027-yil-vazifalari-batafsil",
    "manaviy-marifiy-ishlar-va-olimpiadalar",
    "moliya-oquv-uslubiy-ishlar-va-raqamlashtirish",
]
LANGS = ("uz", "ru", "en")


def sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


def fetch(slug):
    out = subprocess.run(["curl", "-s", "https://fermi.uz/api/v1/pages/" + slug], capture_output=True, text=True).stdout
    return json.loads(out)


def images_of(markup):
    found = []
    for tag in re.findall(r"<img\b[^>]*>", markup, re.I):
        src = re.search(r'src="([^"]+)"', tag)
        alt = re.search(r'alt="([^"]*)"', tag)
        found.append((src.group(1), html.unescape(alt.group(1)) if alt else ""))
    return found


def entry_for(slug, block):
    markup = {lang: block["data"][lang]["html"] for lang in LANGS}
    fp = {lang: sha(block["data"][lang]) for lang in LANGS}
    base = {"slug": slug, "order": block["order"], "fp": fp}
    pics = {lang: images_of(markup[lang]) for lang in LANGS}
    if pics["uz"]:
        assert all(s.startswith("/images/hisobot/") for s, _ in pics["uz"]), (slug, block["order"], "a picture from another place")
        assert [s for s, _ in pics["uz"]] == [s for s, _ in pics["ru"]] == [s for s, _ in pics["en"]], (slug, block["order"], "pictures differ between languages")
        return {**base, "kind": "images", "images": [{"file": os.path.basename(src), "alt": {lang: pics[lang][i][1] for lang in LANGS}} for i, (src, _) in enumerate(pics["uz"])]}
    pdf = re.search(r'href="/files/([^"]+\.pdf)"', markup["uz"])
    if pdf:
        return {**base, "kind": "pdf", "file": pdf.group(1), "caption": {lang: html.unescape(re.sub(r"<[^>]+>", "", markup[lang])).strip() for lang in LANGS}}
    links = {lang: re.findall(r'href="(https?://[^"]+)"', markup[lang]) for lang in LANGS}
    assert links["uz"] and links["uz"] == links["ru"] == links["en"], (slug, block["order"], "unknown raw_html")
    return {**base, "kind": "links", "text": " · ".join(links["uz"])}


def main(path):
    plan = []
    for slug in SLUGS:
        for block in fetch(slug)["blocks"]:
            if block["block_type"] == "raw_html":
                plan.append(entry_for(slug, block))
    with open(path, "w", encoding="utf8") as handle:
        json.dump(plan, handle, ensure_ascii=False, indent=1)
    pictures = sum(len(e.get("images", [])) for e in plan)
    print(f"{len(plan)} raw_html blocks on {len({e['slug'] for e in plan})} pages -> {pictures} pictures, "
          f"{sum(e['kind'] == 'pdf' for e in plan)} pdf, {sum(e['kind'] == 'links' for e in plan)} links line -> {path}")


if __name__ == "__main__":
    main(sys.argv[1])
