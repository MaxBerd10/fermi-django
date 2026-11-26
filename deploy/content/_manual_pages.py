"""Driver for the make_plan.py files of the scripts that write by hand the pages whose languages differ in structure: slugs + translations -> plan entries and a list of the cells that still
need a text (`needed`: [(key, source language, source text, kind)]). Run with the project's python (bs4)."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _auto_pages import all_labels, page  # noqa: E402
from _auto_plan import LANGS, specs_of  # noqa: E402
from _merge3 import assemble, rows_of  # noqa: E402
from _plan_tools import captions_of_cards, entry  # noqa: E402


def build(slugs, translations):
    labels = all_labels()
    plan, needed, problems = [], [], {}
    for slug in slugs:
        blocks = page(slug)
        raws = [b for b in blocks if b["block_type"] == "raw_html"]
        documents = [b for b in blocks if b["block_type"] == "document"]
        if len(raws) != 1 or raws[0]["order"] != 1:
            problems[slug] = ["not one HTML block at order 1"]
            continue
        raw = raws[0]
        if slug + "|blocks" in translations:  # a page written block by block by hand (the three old languages were too different to align)
            merged, missing, issues = [dict(b) for b in translations[slug + "|blocks"]], [], []
        else:
            specs = {lang: specs_of(raw["data"][lang]["html"], lang, drop_notes=(slug + "|drop_notes") in translations, join=(slug + "|join") in translations)[0] for lang in LANGS}
            if (slug + "|uz_only") in translations:  # the Russian and English old texts are other documents: every Russian and English cell is written from the Uzbek text
                specs["ru"], specs["en"] = [], []
            for lang in LANGS:  # a language that has the sections in another order: "slug|order|lang" = the indices of its blocks in the order of the Uzbek page
                if "%s|order|%s" % (slug, lang) in translations:
                    specs[lang] = [specs[lang][i] for i in translations["%s|order|%s" % (slug, lang)]]
            rows = rows_of(specs)
            merged, missing, issues = assemble(slug, rows, translations)
        if issues:
            problems[slug] = issues
        if missing:
            needed.extend(missing)
            continue
        if issues or not merged:
            problems.setdefault(slug, []).append("no blocks" if not merged else "see above")
            continue
        for b in merged:
            b.pop("_row", None)
        cards = None
        if documents:
            if len(documents) == 1 and slug in labels:
                cards = captions_of_cards(documents, [{lang: labels[slug][lang] for lang in LANGS}])
            else:
                problems[slug] = ["%d existing document cards" % len(documents)]
                continue
        item = entry(slug, raw, merged, cards)
        item["notes"] = ["%d blocks aligned by hand (the three languages differ in structure); %d cells translated by us" % (len(merged), sum(1 for k in translations if k.startswith(slug + "|")))]
        plan.append(item)
    return plan, needed, problems
