"""Generic converter used by the make_plan.py files of scripts 61 onwards: the old HTML block of a page -> typed blocks for each language (uz, ru, en), and a check that the three languages
have the same blocks in the same order (a block has one type in all languages; only the texts differ). Runs with the project's python (needs bs4):
    .venv/bin/python deploy/content/yillik-hisobot-2026-NN/make_plan.py

  specs_of(html, lang)        -> [{"t": "heading"|"paragraph"|"list"|"table"|"image"|"document"|"video", ...}] for one language
  merge(specs_by_lang)        -> (blocks, None) when the three languages agree, (None, why) when they do not
  review(slug, ...)           -> flags a person must look at (a text that is the same in two languages, a script that does not match the language...)
"""
import re
import sys

from bs4 import BeautifulSoup, NavigableString, Tag

LANGS = ("uz", "ru", "en")
DOC_EXT = re.compile(r"\.(?:pdf|docx?|xlsx?|pptx?|rar|zip)(?:[?#].*)?$", re.I)
BLOCK_TAGS = {"p", "div", "section", "article", "li", "blockquote", "center", "td", "th", "tr", "tbody", "thead", "table", "ul", "ol", "h1", "h2", "h3", "h4", "h5", "h6", "hr", "br", "img", "iframe", "figure", "span", "font", "strong", "b", "em", "i", "u", "a"}
KEEP_UPPER = {"OTM", "ITM", "FJSTI", "PHD", "DSC", "SSV", "MFY", "IELTS", "TOEFL", "HEMIS", "COVID", "PDF", "ID", "USMLE", "MD", "DM", "AI", "IT", "UNESCO", "OOO", "MCHJ", "ATM", "SMS", "WHO", "BMT", "AQSH", "OAV", "OAK", "DTM", "XXI", "XX", "II", "III", "IV", "VI", "VII", "VIII", "IX", "XI"}
SMALL = {"va", "yoki", "bilan", "uchun", "и", "в", "на", "для", "or", "and", "of", "the", "for", "to", "in"}
PROPER_UZ = ("oʻzbekiston", "fargʻona", "toshkent", "margʻilon", "qoʻqon", "quva", "buvayda", "rishton", "beshariq", "samarqand", "buxoro", "andijon", "namangan", "xorazm", "ibn", "sino", "abu", "ali", "fjsti")


def clean(text):
    text = text.replace("\xa0", " ").replace("​", "").replace("﻿", "").replace(" ", " ").replace(" ", " ").replace(" ", " ")
    return re.sub(r"[ \t\r\n]+", " ", text).strip()


SPELLING = [("Maxkamasi", "Mahkamasi"), ("xamkor", "hamkor"), ("Xamkor", "Hamkor"), ("xozir", "hozir"), ("Xozir", "Hozir"), (" xam ", " ham "), (" Xam ", " Ham "), ("maxalla", "mahalla"), ("Maxalla", "Mahalla"), ("suxbat", "suhbat"),
            ("isloxot", "islohot"), ("xolda", "holda"), ("xaqida", "haqida"), ("Xaqida", "Haqida"), ("ximoya", "himoya"), ("xujjat", "hujjat"), ("Xujjat", "Hujjat"), ("xar bir", "har bir"), ("Xar bir", "Har bir"),
            ("xar kuni", "har kuni"), ("xisob", "hisob"), ("Xisob", "Hisob"), ("xafta", "hafta"), ("xayot", "hayot"), ("xarakat", "harakat"), ("Xarakat", "Harakat")]


def uz_text(text):
    """One apostrophe in Uzbek: U+02BB (also for the tutuq); the old spelling x for h in a few common words."""
    for old, new in SPELLING:
        text = text.replace(old, new)
    text = re.sub(r"(?<=\w)['‘’`´ʼʻ](?=\w)", "ʻ", text)
    text = re.sub(r"(?<=[oOgGOʻ])['‘’`´ʼ](?=[\s.,;:!?)\"”»]|$)", "ʻ", text)
    return text


def fix(text, lang):
    text = clean(text)
    if lang == "uz":
        text = uz_text(text)
    text = re.sub(r"\s+([,.;:!?])", r"\1", text)
    text = re.sub(r"\(\s+", "(", text)
    text = re.sub(r"\s+\)", ")", text)
    return text.strip()


def is_caps(text):
    letters = re.sub(r"[^A-Za-zА-Яа-яЁёʻ’']", "", text)
    return len(letters) >= 6 and letters.upper() == letters


def sentence_case(text, lang):
    words = text.split(" ")
    out = []
    for index, word in enumerate(words):
        core = re.sub(r"^[^\w]+|[^\w]+$", "", word)
        lowered = word.lower()
        if not core:
            out.append(word)
        elif core.upper() in KEEP_UPPER or any(ch.isdigit() for ch in core):
            out.append(word)
        else:
            if lang == "uz" and any(lowered.startswith(p) for p in PROPER_UZ) and index > 0:
                lowered = re.sub(r"\w", lambda m: m.group(0).upper(), lowered, count=1)
            out.append(lowered)
    result = " ".join(out)
    return re.sub(r"\w", lambda m: m.group(0).upper(), result, count=1)


def media_of(url):
    from urllib.parse import unquote
    return unquote(url.split("/media/", 1)[1].split("?", 1)[0].split("#", 1)[0])


def is_media(url):
    return "/media/" in url and url.split("/media/", 1)[0].rstrip("/").endswith(("fermi.uz", "")) or url.startswith("/media/")


class Walker:
    def __init__(self, lang):
        self.lang = lang
        self.out = []
        self.notes = []

    # ---- inline text of a node: plain text with [label](url) for links ----
    def inline(self, node):
        parts = []
        for child in node.children:
            if isinstance(child, NavigableString):
                parts.append(str(child))
            elif isinstance(child, Tag):
                if child.name == "br":
                    parts.append("\n")
                elif child.name == "img":
                    continue
                elif child.name == "a" and child.get("href"):
                    label = clean(child.get_text(" "))
                    href = child["href"].strip()
                    if not label or href.startswith(("#", "javascript:")) or not href:
                        parts.append(label)
                    elif href.startswith(("tel:", "mailto:")):
                        parts.append(label)
                    else:
                        href = href.replace(" ", "%20").replace("(", "%28").replace(")", "%29")
                        if label == href or label.rstrip("/") == href.rstrip("/"):
                            parts.append(href)
                        else:
                            parts.append("[%s](%s)" % (label.replace("]", ")").replace("[", "("), href))
                else:
                    parts.append(self.inline(child))
        return "".join(parts)

    def bold_only(self, node):
        text = clean(node.get_text(" "))
        if not text:
            return False
        bold = "".join(clean(b.get_text(" ")) for b in node.find_all(["strong", "b"]))
        return len(bold.replace(" ", "")) >= len(text.replace(" ", "")) * 0.95

    def add_text(self, raw_text, heading=False, level=3, node=None):
        for segment in raw_text.split("\n"):
            text = fix(segment, self.lang)
            if not text or re.fullmatch(r"[\W_]+", text):
                continue
            # a line that is one link to a file is a document card
            text = re.sub(r"^[>»\s]+", "", text)
            if re.fullmatch(r"/blog/\S+|/detail/\S+|https?://\S+|[\W_]+", text) and not text.startswith("http"):
                continue  # a bare address or a stray sign is not a line of the page
            m = re.fullmatch(r"\[([^\]]+)\]\(([^)]+)\)[\s.;,]*", text)
            if m and DOC_EXT.search(m.group(2)) and "/media/" in m.group(2):
                caption = m.group(1)
                self.out.append({"t": "document", "media": media_of(m.group(2)), "caption": sentence_case(caption, self.lang) if is_caps(caption) else caption})
                continue
            if heading or (node is not None and self.bold_only(node) and len(text) <= 150 and not text.endswith((".", "!", "?", ";", ","))) or (is_caps(text) and len(text) <= 140):
                if is_caps(text):
                    text = sentence_case(text, self.lang)
                self.out.append({"t": "heading", "text": re.sub(r"\*+", "", text), "level": level})
            else:
                self.out.append({"t": "paragraph", "text": text})

    def images(self, node):
        found = [node] if getattr(node, "name", "") == "img" else node.find_all("img")
        for img in found:
            src = (img.get("src") or "").strip()
            if "/media/" in src:
                self.out.append({"t": "image", "media": media_of(src), "alt": clean(img.get("alt") or "")})
            elif src:
                self.notes.append("image not from /media/: %s" % src[:80])

    def table(self, node):
        rows = []
        for tr in node.find_all("tr"):
            cells = [fix(self.inline(td).replace("\n", " "), self.lang) for td in tr.find_all(["td", "th"], recursive=False)]
            if any(cells):
                rows.append(cells)
        if node.find(attrs={"colspan": True}) or node.find(attrs={"rowspan": True}):
            self.notes.append("table with merged cells")
        width = max((len(r) for r in rows), default=0)
        if len(rows) < 2 or width == 0:
            self.notes.append("table too small")
            return
        rows = [r + [""] * (width - len(r)) for r in rows]
        self.out.append({"t": "table", "headers": [h or "—" for h in rows[0]], "rows": [[c for c in r] for r in rows[1:]]})

    def walk(self, node):
        for child in list(node.children):
            if isinstance(child, NavigableString):
                text = fix(str(child), self.lang)
                if text:
                    self.add_text(text)
                continue
            if not isinstance(child, Tag):
                continue
            name = child.name
            if name in ("script", "style", "hr", "br"):
                continue
            if name == "iframe":
                self.out.append({"t": "video", "src": child.get("src", "")})
                continue
            if name == "img":
                self.images(child)
                continue
            if name == "table":
                self.table(child)
                continue
            if name in ("ul", "ol"):
                items = []
                for li in child.find_all("li", recursive=False):
                    text = fix(self.inline(li).replace("\n", " "), self.lang)
                    if text:
                        items.append(re.sub(r"^\s*(?:\d+[.)]\s*|[•·▪–—-]\s+)", "", text))
                if items:
                    self.flush_list_images(child)
                    self.out.append({"t": "list", "items": items})
                continue
            if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
                self.images(child)
                self.add_text(self.inline(child).replace("\n", " "), heading=True, level=2 if name in ("h1", "h2", "h3") else 3)
                continue
            has_block = any(isinstance(c, Tag) and c.name in ("p", "div", "ul", "ol", "table", "h1", "h2", "h3", "h4", "h5", "h6", "section", "article", "blockquote") for c in child.children)
            if name in ("div", "section", "article", "blockquote", "center", "span", "font") and has_block:
                self.walk(child)
                continue
            # a paragraph-like node: images first (they stand where they stand), then the text lines
            for part in self.split_images(child):
                if isinstance(part, Tag) and part.name == "img":
                    self.images(part)
                else:
                    self.add_text(self.inline(part), node=part if part is not child else child)

    def flush_list_images(self, node):
        self.images(node)

    def split_images(self, node):
        """[node] when it has no <img>; otherwise the node itself with the images first (their order against the text is not kept inside a paragraph)."""
        imgs = node.find_all("img")
        if not imgs:
            return [node]
        return list(imgs) + [node]


def specs_of(html, lang):
    soup = BeautifulSoup(html, "html.parser")
    walker = Walker(lang)
    walker.walk(soup)
    # consecutive "1. text" / "• text" paragraphs become a list
    merged = []
    run = []

    def flush():
        if len(run) >= 2:
            merged.append({"t": "list", "items": [re.sub(r"^\s*(?:\d+[.)]\s*|[•·▪–—-]\s*)", "", r["text"]) for r in run]})
        else:
            merged.extend(run)
        run.clear()

    for spec in walker.out:
        if spec["t"] == "paragraph" and re.match(r"^\s*(?:\d{1,2}[.)]\s*\S|[•·▪]\s*\S|[–—-]\s+\S)", spec["text"]) and len(spec["text"]) <= 400:
            run.append(spec)
        else:
            flush()
            merged.append(spec)
    flush()
    return merged, walker.notes


def signature(spec):
    return spec["t"] if spec["t"] != "list" else "list"


def unify(specs):
    """Same number of blocks, but a line is a heading in one language and a paragraph in another (bold in one text only): the Uzbek decides."""
    if len({len(specs[lang]) for lang in LANGS}) != 1:
        return specs
    out = {lang: [dict(s) for s in specs[lang]] for lang in LANGS}
    for i in range(len(out["uz"])):
        base = out["uz"][i]["t"]
        if base not in ("heading", "paragraph"):
            continue
        for lang in ("ru", "en"):
            other = out[lang][i]
            if other["t"] in ("heading", "paragraph") and other["t"] != base:
                other["t"] = base
                if base == "heading":
                    other["level"] = out["uz"][i].get("level", 3)
    return out


def merge(specs):
    """specs = {lang: [spec]} -> (blocks, None) or (None, reason). Images and documents must agree on the file (or the document may differ per language)."""
    specs = unify(specs)
    seq = {lang: [signature(s) for s in specs[lang]] for lang in LANGS}
    if not (seq["uz"] == seq["ru"] == seq["en"]):
        return None, "different blocks: uz %d, ru %d, en %d" % (len(seq["uz"]), len(seq["ru"]), len(seq["en"]))
    blocks = []
    for i in range(len(seq["uz"])):
        kind = seq["uz"][i]
        group = {lang: specs[lang][i] for lang in LANGS}
        if kind == "heading":
            blocks.append({"block_type": "heading", "data": {lang: {"text": group[lang]["text"], "level": group["uz"]["level"]} for lang in LANGS}})
        elif kind == "paragraph":
            blocks.append({"block_type": "paragraph", "data": {lang: {"text": group[lang]["text"]} for lang in LANGS}})
        elif kind == "list":
            n = {len(group[lang]["items"]) for lang in LANGS}
            if len(n) != 1:
                return None, "list %d has different numbers of items: %s" % (i, {lang: len(group[lang]["items"]) for lang in LANGS})
            blocks.append({"block_type": "list", "data": {lang: {"items": group[lang]["items"]} for lang in LANGS}})
        elif kind == "table":
            if len({(len(group[lang]["headers"]), len(group[lang]["rows"])) for lang in LANGS}) != 1:
                return None, "table %d has different shapes" % i
            blocks.append({"block_type": "table", "data": {lang: {"headers": group[lang]["headers"], "rows": group[lang]["rows"]} for lang in LANGS}})
        elif kind == "image":
            if len({group[lang]["media"] for lang in LANGS}) != 1:
                return None, "image %d is another file in a language" % i
            blocks.append({"block_type": "image", "data": {lang: {"media": group[lang]["media"], "alt": group[lang]["alt"] or group["uz"]["alt"]} for lang in LANGS}})
        elif kind == "document":
            blocks.append({"block_type": "document", "data": {lang: {"media": group[lang]["media"], "caption": group[lang]["caption"]} for lang in LANGS}})
        elif kind == "video":
            blocks.append({"block_type": "raw_html", "data": {lang: {"html": '<p><iframe frameborder="0" height="360" src="%s" width="640" title="YouTube"></iframe></p>' % group[lang]["src"]} for lang in LANGS}})
        else:
            return None, "a %s block is not converted" % kind
    return blocks, None


def review(blocks):
    """Things a person must read: a text equal in two languages, a script that does not match the language."""
    flags = []
    cyr = lambda s: len(re.findall(r"[А-Яа-яЁё]", s))
    lat = lambda s: len(re.findall(r"[A-Za-z]", s))

    def texts(data):
        out = []
        for key in ("text", "caption", "alt"):
            if data.get(key):
                out.append(data[key])
        out += data.get("items", [])
        for row in data.get("rows", []):
            out += row
        return out

    for i, block in enumerate(blocks):
        if block["block_type"] in ("image",):
            continue
        by = {lang: " ".join(texts(block["data"][lang])) for lang in LANGS}
        if len(by["uz"]) > 25 and by["uz"] == by["ru"]:
            flags.append((i, "uz == ru: not translated?"))
        if len(by["uz"]) > 25 and by["uz"] == by["en"]:
            flags.append((i, "uz == en: not translated?"))
        if len(by["ru"]) > 25 and cyr(by["ru"]) < 0.5 * (cyr(by["ru"]) + lat(by["ru"])):
            flags.append((i, "ru is not Cyrillic"))
        if len(by["uz"]) > 25 and cyr(by["uz"]) > 0.3 * (cyr(by["uz"]) + lat(by["uz"])):
            flags.append((i, "uz is Cyrillic"))
        if len(by["en"]) > 25 and cyr(by["en"]) > 0:
            flags.append((i, "en has Cyrillic"))
    return flags
