"""Strict conversion for the reviewed legacy text pages in Institut haqida."""
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup, NavigableString, Tag

LANGS = ("uz", "ru", "en")
ARTICLE = re.compile(r"^(?:(\d+)\s*[-–]\s*modda\b|(?:статья|article)\s+(\d+)\b)", re.I)
CHAPTER = re.compile(r"^(?:(\d+)\s*[-–]\s*bob\b|(?:глава|chapter)\s+(\d+)\b)", re.I)


def node_text(node):
    """Keep destinations that the frontend's plain-text links can still open."""
    fragment = BeautifulSoup(str(node), "html.parser")
    for anchor in fragment.find_all("a", href=True):
        href = urljoin("https://fermi.uz/", anchor["href"])
        if urlsplit(href).scheme not in ("http", "https"):
            raise ValueError(f"Unsupported link destination: {anchor['href']}")
        if anchor.get_text(" ", strip=True) != href:
            anchor.insert_after(f" {href} ")
    return " ".join(fragment.get_text(" ", strip=True).split())


def parse(html):
    """Return ordered (kind, payload, numbered heading identifier) units for one language."""
    soup = BeautifulSoup(html, "html.parser")

    def walk(parent):
        for node in parent.children:
            if isinstance(node, NavigableString):
                if node.strip():
                    yield "paragraph", {"text": str(node).strip()}, None
                continue
            if not isinstance(node, Tag) or node.name in ("hr", "br"):
                continue
            if node.name in ("div", "section", "article") and node.find(
                ["p", "ul", "ol", "div", "section", "h2", "h3", "hr"]
            ):
                yield from walk(node)
                continue
            if node.name in ("ul", "ol"):
                if node.find(["img", "ul", "ol"]):
                    raise ValueError("Nested lists or images inside a list require manual alignment.")
                items = [node_text(item) for item in node.find_all("li", recursive=False)]
                if any(not item for item in items):
                    raise ValueError("Empty list item requires review.")
                if items:
                    yield "list", {"items": items}, None
                continue
            text = node_text(node)
            images = node.find_all("img") if node.name != "img" else [node]
            if images:
                if text or len(images) != 1 or not images[0].get("src") or node.find("a", href=True):
                    raise ValueError("Inline or linked images require separate review.")
                image = images[0]
                yield "image", {"image_src": image["src"], "alt": image.get("alt", "")}, None
                continue
            if node.name not in ("p", "div", "span", "strong", "b", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"):
                raise ValueError(f"Unsupported HTML node: {node.name}")
            if node.find(["iframe", "video", "table", "script", "ul", "ol"]):
                raise ValueError("Embedded content requires manual conversion.")
            if not text:
                continue
            article = ARTICLE.match(text)
            chapter = CHAPTER.match(text)
            bold = node if node.name in ("strong", "b") else node.find(["strong", "b"])
            if article or chapter or node.name in ("h1", "h2", "h3", "h4", "h5", "h6") or (
                bold and not node.find("a") and node_text(bold) == text
            ):
                level = 3 if article or node.name in ("h3", "h4", "h5", "h6") else 2
                match = article or chapter
                number = next(group for group in match.groups() if group) if match else None
                yield "heading", {"text": text, "level": level}, number
            else:
                yield "paragraph", {"text": text}, None

    return list(walk(soup))


def signature(unit):
    kind, payload, number = unit
    return kind, payload.get("level"), len(payload["items"]) if kind == "list" else None, number


def build(html_by_lang, *, resolve_image=None):
    """Align the three languages without silently copying a missing translation."""
    if set(html_by_lang) != set(LANGS):
        raise ValueError("The Uzbek, Russian and English source HTML are all required.")
    return build_from_units({lang: parse(html_by_lang[lang]) for lang in LANGS}, resolve_image=resolve_image)


def build_from_units(units, *, resolve_image=None):
    """The same as build() for units already parsed (and, where the languages differ in a known way, corrected by the caller)."""
    source = units["uz"]
    if not source:
        raise ValueError("The Uzbek source has no content.")
    for lang in ("ru", "en"):
        if len(units[lang]) != len(source):
            raise ValueError(f"{lang}: expected {len(source)} blocks, found {len(units[lang])}.")
        for index, (original, translated) in enumerate(zip(source, units[lang]), 1):
            if signature(original) != signature(translated):
                raise ValueError(f"{lang} block #{index}: {signature(original)} != {signature(translated)}.")

    blocks = []
    for index, (kind, _, _) in enumerate(source):
        data = {lang: dict(units[lang][index][1]) for lang in LANGS}
        if kind == "image":
            if resolve_image is None:
                raise ValueError(f"Block #{index + 1}: image resolver is required.")
            for lang in LANGS:
                payload = data[lang]
                src = payload.pop("image_src")
                image_id = resolve_image(src)
                if not image_id:
                    raise ValueError(f"{lang} block #{index + 1}: media not found for {src}.")
                payload["image_id"] = image_id
        blocks.append({"block_type": kind, "data": data})
    return blocks
