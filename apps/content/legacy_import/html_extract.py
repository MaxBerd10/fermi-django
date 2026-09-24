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
    data -- a stray single letter, a zero-width space, a title fragment
    like "Tibbiyot fanlari doktori, professor," that happened to land as
    the first <br>-separated line of a bold block, or (found live, after
    adding the second staff-bio shape below) an ordinary bold SENTENCE like
    "Kafedra ... markazi bazasida joylashgan." that happens to read as
    multiple plain words with no digits or commas. A real name here is
    always 2+ space-separated words, with no digits/commas, and never ends
    in sentence-terminal punctuation the way a real sentence does."""
    words = text.split()
    if len(words) < 2 or "," in text or any(ch.isdigit() for ch in text):
        return False
    if text.rstrip().endswith((".", "!", "?", ":")):
        return False
    return all(any(ch.isalpha() for ch in word) for word in words)


_HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6")


def _build_table_grid(table: Tag) -> tuple[list[str], list[list[str]]] | None:
    """Reconstructs a <table>'s flat grid (expanding rowspan/colspan into
    repeated cell values -- the "table" ContentBlock schema has no concept
    of a spanning cell) and splits it into (headers, data rows).

    The old site's tables have no <thead>/<th> at all -- every row, header
    or data, is a plain <tr><td> (confirmed against real content), so the
    header row(s) aren't distinguished by tag, only by being fully bold
    (the same "cell holds nothing but a <strong>/<b>" signal _is_bold_only
    already uses for headings). A table can have more than one such leading
    bold row -- a merged multi-level header, e.g. one grouping row via
    colspan ("TOʻLOV KONTRAKTI MIQDORLARI" spanning 2 columns) followed by
    a row of the actual sub-labels ("MDH davlatlar uchun" / "Xorijiy
    davlatlar uchun") for those same 2 columns. Taking the LAST such row's
    value per column is exactly right here: a rowspan cell's value already
    reappears in that later row via the carry mechanism below (so a column
    the grouping row solely owns still comes through correctly), while a
    colspan grouping label that a later row overrides with real per-column
    labels is correctly dropped in favor of the more specific ones.

    Returns None (caller falls back to the pre-existing paragraph-flattening
    behavior) when there's no usable header row -- this only auto-converts
    the pattern that's actually been verified against real content, rather
    than guessing on one this hasn't been checked against.
    """
    trs = table.find_all("tr")
    if not trs:
        return None

    grid: list[list[str]] = []
    bold: list[list[bool]] = []
    carry: dict[int, tuple[int, str, bool]] = {}  # col -> (rows remaining, text, is_bold)

    for tr in trs:
        cells = tr.find_all(["td", "th"], recursive=False)
        row_text: list[str] = []
        row_bold: list[bool] = []
        col = 0
        cell_idx = 0
        while cell_idx < len(cells) or col in carry:
            if col in carry:
                remaining, text, is_bold = carry[col]
                row_text.append(text)
                row_bold.append(is_bold)
                carry[col] = (remaining - 1, text, is_bold) if remaining > 1 else None
                if carry[col] is None:
                    del carry[col]
                col += 1
                continue
            cell = cells[cell_idx]
            text = _normalize(cell.get_text(" "))
            is_bold = bool(text) and _is_bold_only(cell)
            try:
                colspan = max(1, int(cell.get("colspan", 1)))
            except (TypeError, ValueError):
                colspan = 1
            try:
                rowspan = max(1, int(cell.get("rowspan", 1)))
            except (TypeError, ValueError):
                rowspan = 1
            # A colspan cell's real text goes in only the first column it
            # spans, blank in the rest -- the "table" ContentBlock schema
            # (and BlockRenderer's plain <td> per cell, with no colSpan
            # attribute) has no concept of a merged cell, so repeating the
            # text into every spanned column would render as that same text
            # sitting in 2+ adjacent cells, looking like a duplication bug
            # (found live: a "Jami:" totals cell with colspan="2" became
            # two side-by-side "Jami:" cells). Rowspan still repeats a
            # cell's value down every row it spans (that's a real per-row
            # value, e.g. a multi-row header's shared "№" column), just
            # blank-after-first now applies per column there too.
            for span_i in range(colspan):
                # Only the TEXT is blanked past the first spanned column --
                # is_bold stays the same for all of them, since a blanked
                # column is still logically part of the same (possibly
                # bold) cell, just not repeating its text. Forcing it False
                # here previously broke the header-row detection below: the
                # leading "is this whole row bold" chain would break on the
                # blanked cell in a colspan'd header row before ever
                # reaching a real header row underneath it.
                col_text = text if span_i == 0 else ""
                row_text.append(col_text)
                row_bold.append(is_bold)
                if rowspan > 1:
                    carry[col] = (rowspan - 1, col_text, is_bold)
                col += 1
            cell_idx += 1
        if any(cell.strip() for cell in row_text):
            grid.append(row_text)
            bold.append(row_bold)

    if len(grid) < 2:
        return None  # a header with no data rows isn't a usable table

    width = max(len(r) for r in grid)
    grid = [r + [""] * (width - len(r)) for r in grid]
    bold = [b + [False] * (width - len(b)) for b in bold]

    header_idx = 0
    for idx, row_bold in enumerate(bold):
        if all(row_bold):
            header_idx = idx
        else:
            break

    if not all(bold[header_idx]) or header_idx >= len(grid) - 1:
        return None  # no real bold header row, or it's the table's only row

    headers = _combine_header_levels(grid[: header_idx + 1], width)
    data_rows = [row for row in grid[header_idx + 1 :] if any(cell.strip() for cell in row)]
    if not headers or not data_rows or any(not h.strip() for h in headers):
        return None
    return headers, data_rows


def _combine_header_levels(header_rows: list[list[str]], width: int) -> list[str]:
    """Combines a 1+-row leading header block into one flat header per
    column. A real multi-level header (a grantlar-taqsimoti-shaped table:
    a year group, split into grant-type groups, split into Jami/oʻzbek/rus
    sub-columns -- 3 real levels, not just 2) needs every level's own text,
    not only the bottom row's -- dropping the group levels would make two
    columns from DIFFERENT year groups both read as just "Jami", losing
    exactly which year/grant-type each one is. But a column that's the
    SAME text at every level (e.g. "№", "Ta'lim yo'nalishi nomi" -- a
    single cell spanning all header rows via rowspan, not a real grouped
    column) must stay as that one word, not become "№ — № — №".

    Each row's blanks (colspan continuation cells, marked "" by the
    colspan-handling above) are forward-filled with the nearest real value
    to their left before combining, so a whole colspan group's real label
    reaches every column it covers.
    """
    propagated_rows = []
    for row in header_rows:
        propagated = []
        current = ""
        for cell in row:
            if cell.strip():
                current = cell
            propagated.append(current)
        propagated_rows.append(propagated)

    headers = []
    for col in range(width):
        parts = []
        for row in propagated_rows:
            value = row[col]
            if value and (not parts or parts[-1] != value):
                parts.append(value)
        headers.append(" — ".join(parts))
    return headers


def _walk_flat_items(soup: Tag):
    """Yields ('image', src), ('list', [items]), ('heading_tag', text) and
    ('text', tag) in document order, skipping inside anything already
    yielded so nested wrapper divs don't produce duplicate items."""
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
            if child.name == "table":
                extracted = _build_table_grid(child)
                if extracted is not None:
                    yield ("table", extracted)
                    for descendant in child.find_all(True):
                        seen_ids.add(id(descendant))
                    seen_ids.add(id(child))
                    continue
                # Couldn't confidently extract this one (see
                # _build_table_grid's own docstring for why) -- fall through
                # to the existing recursion below, same as before this table
                # branch existed at all: each cell's own div/p still becomes
                # its own paragraph/heading block, exactly like today.
            if child.name in ("ul", "ol"):
                items = [_normalize(li.get_text(" ")) for li in child.find_all("li", recursive=False)]
                items = [i for i in items if i]
                if items:
                    yield ("list", items)
                for descendant in child.find_all(True):
                    seen_ids.add(id(descendant))
                seen_ids.add(id(child))
                continue
            if child.name in _HEADING_TAGS:
                # A real semantic heading -- only ever produced by the admin
                # panel's own rich text editor (h2/h3 on its toolbar); the
                # old site's scraped content has none of these at all (see
                # this module's own docstring), so this path never fires on
                # legacy content and can't regress it.
                text = _normalize(child.get_text(" "))
                if text:
                    yield ("heading_tag", text)
                for descendant in child.find_all(True):
                    seen_ids.add(id(descendant))
                seen_ids.add(id(child))
                continue
            if child.name == "blockquote":
                text = _normalize(child.get_text(" "))
                if text:
                    yield ("text_raw", text)
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
            # A second image arriving with nothing (no staff bio) between it
            # and the first means the first was never anyone's photo -- a
            # standalone picture (or one of several, e.g. a building's
            # inline photo gallery: several bare <img> tags in a row with no
            # other content). Flush it as its own block now, rather than
            # silently overwriting it below and losing every image but the
            # last one in the run.
            if pending_image:
                result.blocks.append(ExtractedBlock("image", {"image_src": pending_image}))
            pending_image = value
            i += 1
            continue

        if kind == "list":
            result.blocks.append(ExtractedBlock("list", {"items": value}))
            i += 1
            continue

        if kind == "table":
            if pending_image:
                result.blocks.append(ExtractedBlock("image", {"image_src": pending_image}))
                pending_image = None
            headers, rows = value
            result.blocks.append(ExtractedBlock("table", {"headers": headers, "rows": rows}))
            i += 1
            continue

        if kind == "heading_tag":
            # A real <h1>-<h6>, always a genuine section heading -- never a
            # staff bio's name line (that shape only ever comes from the
            # bold-paragraph heuristic below, for legacy content), so any
            # pending_image is a standalone picture, not this heading's photo.
            if pending_image:
                result.blocks.append(ExtractedBlock("image", {"image_src": pending_image}))
                pending_image = None
            result.blocks.append(ExtractedBlock("heading", {"text": value}))
            i += 1
            continue

        if kind == "text_raw":
            if pending_image:
                result.blocks.append(ExtractedBlock("image", {"image_src": pending_image}))
                pending_image = None
            result.blocks.append(ExtractedBlock("paragraph", {"text": value}))
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
            # A different real staff-bio shape found live: name and title
            # in two SEPARATE bold blocks (not one block with a <br>) --
            # name alone, then a title block (itself possibly 2 lines), then
            # the bio paragraph. Without this, the name-only heading reads
            # as a generic section heading and the title block's own first
            # line (often itself several plain words, e.g. a department
            # name) gets mistaken for the person's name instead.
            if len(lines) == 1 and _looks_like_person_name(lines[0]):
                has_title_then_bio = (
                    i + 2 < len(items)
                    and items[i + 1][0] == "text"
                    and _is_bold_only(items[i + 1][1])
                    and items[i + 2][0] == "text"
                    and not _is_bold_only(items[i + 2][1])
                    and len(items[i + 2][1].get_text(strip=True)) >= _BIO_MIN_CHARS
                )
                if has_title_then_bio:
                    full_name = lines[0]
                    title = " ".join(_heading_lines(items[i + 1][1]))
                    bio = _normalize(items[i + 2][1].get_text(" "))
                    result.staff.append(ExtractedStaff(full_name, title, bio, pending_image))
                    pending_image = None
                    i += 3
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
