"""Driver for the make_plan.py files of scripts 61 onwards: slugs -> plan entries (the generic converter of _auto_plan.py) and a report of the pages that need a person.
    from _auto_pages import build; plan, report = build(slugs)"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _auto_plan import LANGS, merge, review, specs_of  # noqa: E402
from _plan_tools import captions_of_cards, entry, fetch, sha  # noqa: E402

CACHE = os.environ.get("PAGE_CACHE", "")


def all_labels():
    found = {}

    def walk(items):
        for item in items:
            match = re.fullmatch(r"/blog/\d+/([^/?#]+)", item.get("url") or "")
            if match and match.group(1) not in found:
                found[match.group(1)] = item["label"]
            walk(item.get("children", []))

    menu = fetch("https://fermi.uz/api/v1/menu/?page_size=500")
    walk(menu if isinstance(menu, list) else menu.get("results", []))
    return found


def page(slug):
    return fetch("https://fermi.uz/api/v1/pages/%s/" % slug)["blocks"]


def build(slugs, labels=None):
    labels = labels or all_labels()
    plan, report = [], {}
    for slug in slugs:
        blocks = page(slug)
        raws = [b for b in blocks if b["block_type"] == "raw_html"]
        documents = [b for b in blocks if b["block_type"] == "document"]
        if len(raws) != 1 or raws[0]["order"] != 1:
            report[slug] = ["not one HTML block at order 1: %s" % [b["block_type"] for b in blocks]]
            continue
        raw = raws[0]
        specs, notes = {}, []
        for lang in LANGS:
            specs[lang], n = specs_of(raw["data"][lang]["html"], lang)
            notes += ["%s: %s" % (lang, x) for x in n]
        merged, why = merge(specs)
        if merged is None:
            report[slug] = ["MANUAL: " + why] + notes + ["blocks: " + " ".join("%s=%s" % (l, "".join(s["t"][0] for s in specs[l])) for l in LANGS)]
            continue
        if not merged:
            report[slug] = ["MANUAL: the old text is empty"] + notes
            continue
        cards = None
        if documents:
            if len(documents) == 1 and slug in labels:
                caption = {lang: labels[slug][lang] for lang in LANGS}
                cards = captions_of_cards(documents, [caption])
            else:
                report[slug] = ["MANUAL: %d existing document cards" % len(documents)] + notes
                continue
        item = entry(slug, raw, merged, cards)
        flags = review(merged)
        item["notes"] = ["%d blocks: %s" % (len(merged), ", ".join(sorted({b["block_type"] for b in merged})))] + notes
        plan.append(item)
        if flags or notes:
            report[slug] = ["REVIEW %d: %s" % f for f in flags] + notes
    return plan, report
