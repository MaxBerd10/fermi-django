"""Builds plan.json of script 49 (Institut gazetasi, six pages) from the live pages.
  * every page: the cover picture of the UZ text (an `image` block) -- where ru/en showed another picture or none, a note is printed by the script;
  * the archive pages (2021-2024): every issue (a PDF link) becomes a `document` card; the ru/en titles were copies of the Uzbek ones (or missing), now translated;
  * the main page: the ru/en lists of issues (a copy of the archives) are not kept: the archives are in the menu; the page is the picture and the card it already had;
  * the cards the pages already have get a caption (the menu name).
    python deploy/content/yillik-hisobot-2026-49/make_plan.py"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _plan_tools import *  # noqa: E402,F403

HERE = os.path.dirname(os.path.abspath(__file__))
SLUGS = ["institut-ijtimoy-tibbiy-gazetasi", "institut-gazetasi-arxivi-2021", "institut-gazetasi-arxivi-2022", "institut-gazetasi-arxivi-2023",
         "institut-gazetasi-arxivi-2024", "institut-gazetasi-2025"]
NEWSPAPER = {"ru": "Социально-медицинская газета Ферганского медицинского института общественного здоровья от %s",
             "en": "Social and medical newspaper of the Fergana Medical Institute of Public Health, %s"}
DATE = re.compile(r"\d{2}\.\d{2}\.\d{4}")

MENU = menu_labels(1872)
plan = []
for slug in SLUGS:
    raw, documents = page_blocks(slug)
    htmls = {lang: raw["data"][lang]["html"] for lang in LANGS}
    pictures = {lang: images_of(htmls[lang]) for lang in LANGS}
    assert pictures["uz"], slug
    cover = pictures["uz"][0]
    notes = []
    for lang in ("ru", "en"):
        if cover not in pictures[lang]:
            notes.append("%s showed another picture (%s) -> now the uz picture" % (lang, ", ".join(sorted(set(pictures[lang]))) or "none"))
    blocks = [image_block(cover, {lang: MENU[slug][lang] for lang in LANGS})]
    uz_links = [(h, t) for h, t in links_of(htmls["uz"]) if "/media/" in h]
    for href, text in uz_links:
        date = DATE.search(text).group(0)
        assert text.endswith(date), text
        blocks.append(document_block(media_of(href), {"uz": text, "ru": NEWSPAPER["ru"] % date, "en": NEWSPAPER["en"] % date}))
    for lang in ("ru", "en"):
        issues = {media_of(h) for h, _ in links_of(htmls[lang]) if "/media/" in h and h.endswith(".pdf")}
        if issues and issues != {media_of(h) for h, _ in uz_links}:
            notes.append("%s listed %s" % (lang, "the issues of the archives (not kept: the archives are in the menu)" if slug == SLUGS[0]
                                          else "other issues: only in %s: %s" % (lang, sorted(issues - {media_of(h) for h, _ in uz_links})) + "; only in uz: %s" % sorted({media_of(h) for h, _ in uz_links} - issues)))
    plan_entry = entry(slug, raw, blocks, captions_of_cards(documents, [MENU[slug]] * len(documents)))
    plan_entry["notes"] = notes
    plan.append(plan_entry)

json.dump(plan, open(os.path.join(HERE, "plan.json"), "w", encoding="utf8"), ensure_ascii=False, indent=1)
print("plan.json written:", [(e["slug"], len(e["blocks"])) for e in plan])
for e in plan:
    for n in e["notes"]:
        print("  ", e["slug"], n)
