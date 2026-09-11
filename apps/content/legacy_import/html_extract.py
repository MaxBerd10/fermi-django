"""
Turns the old Yii2 site's free-form department HTML into structured pieces:
intro/trailing ContentBlocks (heading/paragraph/list/image) plus StaffMember
rows extracted from the repeating "photo + bold name/title + bio paragraph"
pattern found in every department page inspected so far.

Why this exists instead of a generic HTML->block converter: the old content
has NO real <h1>-<h6> tags at all -- "headings" are plain <div>/<p> elements
whose entire text is wrapped in <strong>/<b> and nothing else. And a large
fraction of a department page's content isn't generic prose -- it's staff
biographies that belong in the Department's own StaffMember list, not as
paragraph blocks in its Page.

This module never writes to the database and never raises on malformed
input -- worst case, a fragment lands in `skipped` for a human to look at
in the dry-run report. Real content review, not blind automation, is the
point: see the management command's --dry-run flag.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, NavigableString, Tag

_BLOCK_TEXT_TAGS = ("div", "p", "li")
_PDF_FRAGMENT_POSITION_RE = re.compile(r"position\s*:\s*absolute", re.I)
_PDF_FRAGMENT_TRANSPARENT_RE = re.compile(r"color\s*:\s*transparent", re.I)
_BIO_MIN_CHARS = 120  # below this, a paragraph after a name/title heading probably isn't a bio
_HEADING_MAX_CHARS = 100  # a fully-bold div longer than this is a bold PARAGRAPH, not a heading


@dataclass
class ExtractedBlock:
    block_type: str  # "heading" | "paragraph" | "list" | "image"
    payload: dict


@dataclass
class ExtractedStaff:
    full_name: str
    title: str
    bio: str
    photo_src: str | None


@dataclass
class ExtractionResult:
    blocks: list[ExtractedBlock] = field(default_factory=list)
    staff: list[ExtractedStaff] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)


def _is_pdf_text_layer_fragment(tag: Tag) -> bool:
    style = tag.get("style") or ""
    return bool(_PDF_FRAGMENT_POSITION_RE.search(style) and _PDF_FRAGMENT_TRANSPARENT_RE.search(style))


def _collapse_pdf_text_layer_artifacts(soup: Tag) -> None:
    """Merges runs of 2+ PDF-text-layer character fragments (a <div
    style="position:absolute; color:transparent; ...">X</div> per letter --
    what pasting text straight out of a PDF viewer produces) into one real
    <p> holding the concatenated text. Ports enhanceDepartmentHtml.ts's
    collapsePdfTextLayerArtifacts, built earlier for the exact same
    pollution found live on the old site's own frontend -- that fix only
    covered the display layer there; this extraction pipeline needed its
    own copy or every such fragment becomes its own one-letter block.
    Mutates `soup` in place, before block extraction ever walks the tree.
    """
    containers = [soup, *soup.find_all(True)]
    for container in containers:
        if not isinstance(container, Tag) or container.decomposed:
            continue
        nodes = list(container.children)
        i = 0
        while i < len(nodes):
            start = nodes[i]
            if not (isinstance(start, Tag) and _is_pdf_text_layer_fragment(start)):
                i += 1
                continue
            run = [start]
            texts = [start.get_text()]
            j = i + 1
            while j < len(nodes):
                nxt = nodes[j]
                if isinstance(nxt, Tag) and _is_pdf_text_layer_fragment(nxt):
                    run.append(nxt)
                    texts.append(nxt.get_text())
                    j += 1
                elif isinstance(nxt, NavigableString) and not str(nxt).strip():
                    run.append(nxt)
                    j += 1
                else:
                    break
            if len(texts) >= 2:
                p = soup.new_tag("p")
                p.string = "".join(texts)
                run[0].insert_before(p)
                for node in run:
                    node.extract()
            i = j


def _is_leaf_text_container(tag: Tag) -> bool:
    """A div/p/li that holds text directly, with no descendant div/p/li that
    also holds text -- i.e. the innermost meaningful container, so a stack of
    wrapper <div>s around one sentence is extracted once, not once per div."""
    if tag.name not in _BLOCK_TEXT_TAGS:
        return False
    if not tag.get_text(strip=True):
        return False
    for descendant in tag.find_all(_BLOCK_TEXT_TAGS):
        if descendant.get_text(strip=True):
            return False
    return True


def _is_bold_only(tag: Tag) -> bool:
    """True if every bit of text in `tag` is wrapped in <strong>/<b>, i.e. it
    reads as a heading even though it's really just a bold div/p."""
    text = tag.get_text(strip=True)
    if not text:
        return False
    bold_text = "".join(b.get_text() for b in tag.find_all(["strong", "b"]))
    return "".join(bold_text.split()) == "".join(text.split())


def _normalize(text: str) -> str:
    """Collapses runs of whitespace (a leftover &nbsp; sitting next to a
    normal space becomes a double space once decoded) into single spaces."""
    return " ".join(text.split())


def _heading_lines(tag: Tag) -> list[str]:
    return [_normalize(line) for line in tag.get_text("\n").split("\n") if line.strip()]


def _looks_like_person_name(text: str) -> bool:
    """Guards the staff-bio heuristic against false positives seen on real
    data -- a stray single letter, a zero-width space, or a title fragment
    like "Tibbiyot fanlari doktori, professor," that happened to land as
    the first <br>-separated line of a bold block. A real name here is
    always 2+ space-separated words with no digits or commas."""
    words = text.split()
    if len(words) < 2 or "," in text or any(ch.isdigit() for ch in text):
        return False
    return all(any(ch.isalpha() for ch in word) for word in words)


def _walk_flat_items(soup: Tag):
    """Yields ('image', src) and ('list', [items]) and ('text', tag) in
    document order, skipping inside anything already yielded so nested
    wrapper divs don't produce duplicate items."""
    seen_ids = set()

    def walk(node):
        for child in node.children:
            if not isinstance(child, Tag):
                continue
            if id(child) in seen_ids:
                continue
            if child.name == "img":
                src = child.get("src")
                if src:
                    yield ("image", src)
                seen_ids.add(id(child))
                continue
            if child.name in ("ul", "ol"):
                items = [_normalize(li.get_text(" ")) for li in child.find_all("li", recursive=False)]
                items = [i for i in items if i]
                if items:
                    yield ("list", items)
                for descendant in child.find_all(True):
                    seen_ids.add(id(descendant))
                seen_ids.add(id(child))
                continue
            if _is_leaf_text_container(child):
                yield ("text", child)
                seen_ids.add(id(child))
                continue
            # Not a leaf and not an image/list -- recurse into it.
            yield from walk(child)

    yield from walk(soup)


def extract(html: str) -> ExtractionResult:
    result = ExtractionResult()
    if not html or not html.strip():
        return result

    # The old editor filled whitespace with &nbsp; throughout -- decoded by
    # the parser to U+00A0, which looks identical to a normal space but
    # isn't one (and would otherwise leak into every extracted text field).
    html = html.replace("&nbsp;", " ").replace("\xa0", " ")
    soup = BeautifulSoup(html, "lxml")
    _collapse_pdf_text_layer_artifacts(soup)
    items = list(_walk_flat_items(soup))

    pending_image: str | None = None
    i = 0
    while i < len(items):
        kind, value = items[i]

        if kind == "image":
            pending_image = value
            i += 1
            continue

        if kind == "list":
            result.blocks.append(ExtractedBlock("list", {"items": value}))
            i += 1
            continue

        # kind == "text"
        tag = value
        # get_text(" ") rather than strip=True: adjacent inline elements
        # with no whitespace between their tags in the source (common in
        # this content) would otherwise glue their text together with no
        # separator at all once stripped.
        text = _normalize(tag.get_text(" "))

        if _is_bold_only(tag):
            lines = _heading_lines(tag)
            # A name/title heading has two lines (via <br>) and is followed by
            # a long-enough paragraph -- that's a staff bio, not a section
            # heading. Everything else (single-line bold, or no bio after it)
            # is a generic heading block.
            next_is_long_paragraph = (
                i + 1 < len(items)
                and items[i + 1][0] == "text"
                and not _is_bold_only(items[i + 1][1])
                and len(items[i + 1][1].get_text(strip=True)) >= _BIO_MIN_CHARS
            )
            if len(lines) >= 2 and next_is_long_paragraph and _looks_like_person_name(lines[0]):
                full_name, title = lines[0], " ".join(lines[1:])
                bio = _normalize(items[i + 1][1].get_text(" "))
                result.staff.append(ExtractedStaff(full_name, title, bio, pending_image))
                pending_image = None
                i += 2
                continue
            # Not a staff bio -- a short fully-bold div/p is a real heading,
            # but a long one (e.g. the intro sentence, entirely bolded by the
            # original author) is a bold PARAGRAPH, not a heading. A real
            # heading in this content is a short label ("Kafedraning tarixi",
            # "Davolash fakulteti:") and never ends in sentence punctuation --
            # a bolded full sentence does, regardless of length.
            if len(text) <= _HEADING_MAX_CHARS and not text.rstrip().endswith((".", "!", "?")):
                result.blocks.append(ExtractedBlock("heading", {"text": " ".join(lines)}))
                i += 1
                continue
            # else: falls through to the plain-paragraph handling below

        # Plain paragraph (including a long fully-bold div that didn't
        # qualify as a heading above). A leftover pending_image with no
        # heading/bio after it (e.g. a standalone photo) becomes its own
        # image block first.
        if pending_image:
            result.blocks.append(ExtractedBlock("image", {"image_src": pending_image}))
            pending_image = None
        if len(text) < 2:
            i += 1
            continue
        result.blocks.append(ExtractedBlock("paragraph", {"text": text}))
        i += 1

    if pending_image:
        result.blocks.append(ExtractedBlock("image", {"image_src": pending_image}))

    return result
