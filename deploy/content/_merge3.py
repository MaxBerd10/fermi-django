"""Three-language merge of the pages whose languages differ in structure: the Uzbek blocks are the base, the Russian and English blocks are aligned to them (_align.py); a block that exists in
a language only (or is missing in a language) becomes a row with a missing cell, and the missing text is supplied by hand in `translations.json` of the script
(key "slug|row|lang" -> text, or -> {"items": [...]} for a list). `rows_of(specs)` -> rows; `assemble(rows, translations)` -> (blocks, missing)."""
import re

from _align import align, score, tokens

LANGS = ("uz", "ru", "en")
TEXT_KINDS = {"heading", "paragraph"}


def rows_of(specs):
    """specs {lang: [spec]} -> rows [{lang: spec or None}] in the order of the Uzbek text; blocks that only ru/en have are placed after the Uzbek block they follow."""
    uz = specs["uz"]
    pair = {lang: align(uz, specs[lang]) for lang in ("ru", "en")}
    match = {lang: {i: j for i, j in pair[lang] if i is not None and j is not None} for lang in ("ru", "en")}
    # extras of ru/en between the uz blocks: group by the uz block they follow
    extras = {lang: {} for lang in ("ru", "en")}
    last = -1
    for lang in ("ru", "en"):
        last = -1
        for i, j in pair[lang]:
            if i is not None:
                last = i
            if i is None and j is not None:
                extras[lang].setdefault(last, []).append(j)
    rows = []
    for i in range(-1, len(uz)):
        if i >= 0:
            rows.append({"uz": uz[i], "ru": specs["ru"][match["ru"][i]] if i in match["ru"] else None, "en": specs["en"][match["en"][i]] if i in match["en"] else None})
        ru_extra = [specs["ru"][j] for j in extras["ru"].get(i, [])]
        en_extra = [specs["en"][j] for j in extras["en"].get(i, [])]
        for a, b in align(ru_extra, en_extra):
            rows.append({"uz": None, "ru": ru_extra[a] if a is not None else None, "en": en_extra[b] if b is not None else None})
    return reunite(rows)


def reunite(rows):
    """A block that stands in another place of the page in a language (a list after the picture in Uzbek, before it in Russian) is unmatched in both: put the two together."""
    for lang in ("ru", "en"):
        for _ in range(len(rows)):
            best = None
            for a, row_a in enumerate(rows):
                if not (row_a["uz"] and not row_a[lang]):
                    continue
                for b, row_b in enumerate(rows):
                    if a == b or row_b["uz"] or not row_b[lang]:
                        continue
                    sc = score(row_a["uz"], row_b[lang])
                    if sc >= 1.9 and (best is None or sc > best[0]):
                        best = (sc, a, b)
            if best is None:
                break
            _, a, b = best
            rows[a][lang] = rows[b][lang]
            rows[b][lang] = None
            if not any(rows[b].values()):
                rows.pop(b)
    return rows


def kind_of(row):
    kinds = {s["t"] for s in row.values() if s}
    if len(kinds) == 1:
        return kinds.pop()
    if kinds <= TEXT_KINDS:
        return (row["uz"] or row["ru"] or row["en"])["t"]
    if kinds <= TEXT_KINDS | {"list"}:
        return "paragraph"  # a list in one language and a paragraph in another: one paragraph (the items one after another)
    return None


def flat(spec):
    """A list spec as a paragraph spec."""
    if spec and spec["t"] == "list":
        items = [i.strip() for i in spec["items"]]
        return {"t": "paragraph", "text": " ".join(i if i.endswith((".", ";", ":", "!", "?")) else i + ";" for i in items).rstrip(";") + ("." if not items[-1].endswith((".", "!", "?")) else "")}
    return spec


def source_text(row):
    for lang in ("uz", "ru", "en"):
        if row[lang]:
            s = row[lang]
            return lang, (s.get("text") or s.get("caption") or s.get("alt") or "\n".join(s.get("items", [])))
    return None, ""


def assemble(slug, rows, translations):
    """-> (blocks, missing, problems); `missing` = [(key, source_lang, source_text, kind)] of the cells without text and without a translation."""
    blocks, missing, problems = [], [], []
    for k, row in enumerate(rows):
        kind = kind_of(row)
        if kind == "paragraph":
            row = {lang: flat(spec) for lang, spec in row.items()}
        if kind is None:
            problems.append("row %d: incompatible blocks %s" % (k, {l: s["t"] for l, s in row.items() if s}))
            continue
        data = {}
        for lang in LANGS:
            s = row[lang]
            key = "%s|%d|%s" % (slug, k, lang)
            if kind in ("heading", "paragraph"):
                if key in translations:
                    data[lang] = {"text": translations[key]} if kind == "paragraph" else {"text": translations[key], "level": (row["uz"] or row["ru"] or row["en"]).get("level", 3)}
                elif s:
                    data[lang] = {"text": s["text"]} if kind == "paragraph" else {"text": s["text"], "level": (row["uz"] or row["ru"] or row["en"]).get("level", 3)}
                elif key in translations:
                    data[lang] = {"text": translations[key]} if kind == "paragraph" else {"text": translations[key], "level": (row["uz"] or row["ru"] or row["en"]).get("level", 3)}
                else:
                    missing.append((key, source_text(row)[0], source_text(row)[1], kind))
            elif kind == "list":
                if key in translations:
                    data[lang] = {"items": translations[key]}
                elif s:
                    data[lang] = {"items": s["items"]}
                else:
                    missing.append((key, source_text(row)[0], source_text(row)[1], kind))
            elif kind in ("image", "document"):
                base = row["uz"] or row["ru"] or row["en"]
                if kind == "image":
                    data[lang] = {"media": base["media"], "alt": (s or base).get("alt", "")}
                else:
                    cap = (s or {}).get("caption") or translations.get(key)
                    if not cap:
                        missing.append((key, source_text(row)[0], source_text(row)[1], "caption"))
                        continue
                    data[lang] = {"media": (s or base)["media"], "caption": cap}
            elif kind == "table":
                if s:
                    data[lang] = {"headers": s["headers"], "rows": s["rows"]}
                else:
                    problems.append("row %d: a table in one language only" % k)
            elif kind == "video":
                base = row["uz"] or row["ru"] or row["en"]
                data[lang] = {"html": '<p><iframe frameborder="0" height="360" src="%s" width="640" title="YouTube"></iframe></p>' % (s or base)["src"]}
        if len(data) == 3:
            blocks.append({"block_type": {"video": "raw_html"}.get(kind, kind), "data": data, "_row": k})
        elif kind in ("list",) and len(data) < 3:
            pass
    return blocks, missing, problems
