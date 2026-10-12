"""Editing legacy pages (a `raw_html` block, often followed by PDF `document` blocks) from the admin panel.

Until now such a page showed up in the editor as ONE grey "tahrirlanmaydi" chip, so its text, pictures and PDF links
could not be changed at all (194 of the 239 stand-alone pages). This module opens the HTML up without risking it:

* The legacy HTML is cut into its top-level pieces. A piece the editor can express faithfully (paragraphs,
  headings, lists, links, pictures, quotes, rules, plain inline formatting) is handed to the editor as ordinary,
  editable HTML.
* Any other piece (a table, an embedded frame, an element carrying classes/ids/scripts, ...) and every non-text block
  (a PDF card, a table block, ...) travels as an untouchable chip that remembers its place; on save the original
  comes back byte for byte. A chip can be moved or deleted, never edited by accident.
* A language the editor did not change is never rewritten: the text posted back is compared with what this module
  produced for it, and an equal text means "leave what is stored exactly as it is".

The public page keeps rendering the stored blocks through the same client code as before, so a page edited here
looks like a page that was never touched. The structure comes from the Uzbek editor (as in admin_content.py): ru/en
supply the text of each run, paired by position.
"""
from __future__ import annotations

import html as html_lib
import re

from bs4 import BeautifulSoup, Comment, NavigableString, Tag
from django.db import transaction

from .models import ContentBlock, Page

LANGS = ("uz", "ru", "en")

# Block types the text editor cannot express; a page made only of these plus raw_html is opened by this module.
_NON_TEXT_TYPES = frozenset({"table", "document", "gallery", "video", "staff_card"})

# Tags the editor reproduces without losing anything that matters on the public page.
_BLOCK_TAGS = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "blockquote", "hr", "div", "pre"}
_INLINE_TAGS = {
    "a", "strong", "b", "em", "i", "u", "s", "strike", "del", "span", "br", "sup", "sub", "img", "li", "font", "code",
    "small", "big", "mark", "abbr", "cite",
}
_SIMPLE_TAGS = _BLOCK_TAGS | _INLINE_TAGS

# Attributes that decide layout or behaviour: an element carrying one is not "simple".
_BLOCKING_ATTRS = {"class", "id", "role", "aria-hidden"}

# Style properties the public page strips anyway (see stripLegacyStyles in the frontend) or that the editor keeps
# (alignment); any other property (a float, a width, ...) makes the element a chip.
_HARMLESS_STYLE_PROPS = {
    "font-family", "font-size", "font-weight", "font-style", "color", "background-color", "text-align", "margin",
    "margin-top", "margin-bottom", "margin-left", "margin-right", "text-indent", "line-height", "text-decoration",
    "letter-spacing", "word-spacing", "white-space", "text-transform", "vertical-align", "padding", "padding-left",
    "padding-right", "padding-top", "padding-bottom", "orphans", "widows", "font-variant", "font-variant-ligatures",
    "font-variant-caps", "text-decoration-style", "text-decoration-color", "text-decoration-thickness",
    "text-underline-offset", "-webkit-text-stroke-width", "background", "caret-color",
}

_EMPTY_RUN = "<p></p>"  # the raw_html validator needs non-empty html; this renders nothing
_CONTENT_TAGS = ["img", "hr", "iframe", "video", "audio", "table", "object", "embed", "svg"]


def _is_blank(markup: str) -> bool:
    """True for html that shows nothing: only whitespace, empty paragraphs, line breaks. (The editor always leaves an
    empty paragraph after a last chip; it must not become a block of its own.)"""
    soup = BeautifulSoup(markup or "", "html.parser")
    return not soup.find(_CONTENT_TAGS) and not re.sub(r"[\s\u200b\xa0]+", "", soup.get_text())


def _style_is_harmless(style: str, allowed=_HARMLESS_STYLE_PROPS) -> bool:
    for declaration in style.split(";"):
        if not declaration.strip():
            continue
        if declaration.split(":", 1)[0].strip().lower() not in allowed:
            return False
    return True


# A picture wrapped in a sized <div> (the book cover on the monograph page): the wrapper's size only matters to the
# pre-wrapper layout; the public page re-wraps the cover itself, so losing it on an edit is harmless.
_PICTURE_WRAPPER_PROPS = _HARMLESS_STYLE_PROPS | {"max-width", "width", "max-height", "height"}


def _is_picture_wrapper(node: Tag) -> bool:
    if node.name != "div":
        return False
    children = [c for c in node.children if not (isinstance(c, NavigableString) and not str(c).strip())]
    return len(children) == 1 and isinstance(children[0], Tag) and children[0].name == "img"


def _is_simple(node: Tag) -> bool:
    """True when the editor can carry this top-level element faithfully."""
    wrapper = _is_picture_wrapper(node)
    for element in [node] + node.find_all(True):
        if element.name not in _SIMPLE_TAGS:
            return False
        for attr, value in element.attrs.items():
            name = attr.lower()
            if name in _BLOCKING_ATTRS or name.startswith("on") or name.startswith("data-"):
                return False
            if name == "style":
                allowed = _PICTURE_WRAPPER_PROPS if (wrapper and element is node) else _HARMLESS_STYLE_PROPS
                if not _style_is_harmless(" ".join(value) if isinstance(value, list) else str(value), allowed):
                    return False
            if name in ("href", "src") and str(value).strip().lower().startswith(("javascript:", "data:", "vbscript:")):
                return False
        if element.name in ("div", "pre") and element is not node:
            return False  # nested layout containers: leave them to the chip
        if element.name == "div" and element.find(["div", "pre"]):
            return False
    return True


def _pieces(raw_html: str) -> list[tuple[str, str]]:
    """The HTML's top-level pieces as ("html", markup) or ("text", text); comments and blank text are dropped."""
    soup = BeautifulSoup(raw_html or "", "html.parser")
    pieces: list[tuple[str, str]] = []
    for child in list(soup.children):
        if isinstance(child, Comment):
            continue
        if isinstance(child, NavigableString):
            text = str(child)
            if text.strip():
                pieces.append(("text", text))
            continue
        pieces.append(("html", str(child)))
    return pieces


_KIND_LABELS = {
    "table": "Jadval", "iframe": "Ramka (video/xarita/hujjat)", "script": "Skript", "style": "Uslub", "form": "Forma",
    "video": "Video", "audio": "Audio", "object": "Ob'ekt", "embed": "Ob'ekt",
}


def _chip(ref: str, block_type: str, label: str) -> str:
    return (
        f'<div data-preserved-block="{ref}" data-block-type="{block_type}" class="preserved-block">'
        f"{html_lib.escape(label, quote=False)}</div>"
    )


def _raw_chip_label(markup: str) -> str:
    soup = BeautifulSoup(markup, "html.parser")
    node = next((c for c in soup.children if isinstance(c, Tag)), None)
    found = next(
        (label for tag, label in _KIND_LABELS.items() if node is not None and (node.name == tag or node.find(tag))), None
    )
    snippet = re.sub(r"[\s​\xa0]+", " ", soup.get_text(" ")).strip()[:40]
    head = found or f"Maxsus blok <{node.name if node is not None else 'blok'}>"
    return f"{head}: {snippet} — tahrirlanmaydi" if snippet else f"{head} — tahrirlanmaydi"


def is_raw_capable(page: Page | None) -> bool:
    """A page whose blocks are legacy HTML plus (at most) non-text blocks such as PDF cards: no heading/paragraph/
    list/image blocks, which the older block-by-block bridge in admin_content.py already edits."""
    if page is None or page.pk is None:
        return False
    types = [block.block_type for block in page.blocks.all()]
    return "raw_html" in types and all(t == "raw_html" or t in _NON_TEXT_TYPES for t in types)


def _html_of(block: ContentBlock, lang: str) -> str:
    data = block.data or {}
    payload = data.get(lang) or {}
    if isinstance(payload, dict) and payload.get("html"):
        return payload["html"]
    return (data.get("uz") or {}).get("html", "")


def _raw_pieces_for(block: ContentBlock, lang: str) -> dict[int, str]:
    return {index: markup for index, (kind, markup) in enumerate(_pieces(_html_of(block, lang))) if kind == "html"}


def page_editor_html(page: Page, lang: str) -> str:
    """The HTML the editor opens for one language: for each block in order, a raw_html block's editable pieces as
    they are and its other pieces as numbered chips, every other block as a chip carrying its id."""
    from .admin_content import _placeholder_label  # imported late: admin_content calls into this module

    parts: list[str] = []
    for block in page.blocks.all():
        if block.block_type == "raw_html":
            for index, (kind, markup) in enumerate(_pieces(_html_of(block, lang))):
                if kind == "text":
                    parts.append(f"<p>{html_lib.escape(markup.strip(), quote=False)}</p>")
                    continue
                node = next((c for c in BeautifulSoup(markup, "html.parser").children if isinstance(c, Tag)), None)
                if node is not None and _is_simple(node):
                    parts.append(markup)
                else:
                    parts.append(_chip(f"raw:{block.id}:{index}", "raw", _raw_chip_label(markup)))
        else:
            parts.append(_chip(str(block.id), block.block_type, _placeholder_label(block, block.data.get("uz") or {})))
    return "\n".join(parts)


_CHIP_RE = re.compile(
    r"""<div\b[^>]*\bdata-preserved-block\s*=\s*["'](raw:\d+:\d+|\d+)["'][^>]*>.*?</div>""", re.S | re.I
)


def _runs(posted: str, originals: dict[tuple[int, int], str]) -> tuple[list[str], list]:
    """Cuts one language's posted HTML into runs of text separated by non-text chips. Returns (runs, layout) where layout
    lists ("run", index) and ("id", block_id) in order. A raw chip is replaced by the piece it stood for (so it belongs to
    the surrounding run); an unknown or repeated chip is skipped."""
    runs: list[str] = []
    layout: list[tuple[str, int]] = []
    buffer: list[str] = []
    seen_raw: set[tuple[int, int]] = set()
    seen_ids: set[int] = set()

    def flush():
        text = "\n".join(piece for piece in buffer if piece.strip()).strip()
        buffer.clear()
        if text and not _is_blank(text):
            layout.append(("run", len(runs)))
            runs.append(text)

    last = 0
    for match in _CHIP_RE.finditer(posted or ""):
        buffer.append((posted or "")[last:match.start()])
        last = match.end()
        ref = match.group(1)
        if ref.startswith("raw:"):
            _, block_id, index = ref.split(":")
            key = (int(block_id), int(index))
            if key in originals and key not in seen_raw:
                seen_raw.add(key)
                buffer.append(originals[key])
        else:
            block_id = int(ref)
            if block_id not in seen_ids:
                seen_ids.add(block_id)
                flush()
                layout.append(("id", block_id))
    buffer.append((posted or "")[last:])
    flush()
    return runs, layout


def _shape(layout: list[tuple[str, int]]) -> list[tuple[str, int]]:
    return [(kind, ref if kind == "id" else 0) for kind, ref in layout]


@transaction.atomic
def write_page_from_html(page: Page, html_by_lang: dict[str, str]) -> bool:
    """Stores what the editor posted. Returns True when anything changed (an untouched save changes nothing)."""
    from .admin_content import _NEW_DOC_RE, _materialize_new_documents  # imported late: admin_content calls into this module

    produced = {lang: page_editor_html(page, lang) for lang in LANGS}
    posted = {lang: html_by_lang.get(lang) if html_by_lang.get(lang) is not None else produced[lang] for lang in LANGS}
    if all(posted[lang] == produced[lang] for lang in LANGS):
        return False

    # A file attached in the editor ("Fayl qo'shish", Uzbek tab) becomes a document block first; its id chip then
    # takes part in the normal layout below. ru/en markers are dropped, as in admin_content.write_blocks_from_html.
    posted["uz"] = _materialize_new_documents(page, posted["uz"])
    for lang in ("ru", "en"):
        posted[lang] = _NEW_DOC_RE.sub("", posted[lang])

    existing = list(ContentBlock.objects.filter(page=page).order_by("order"))
    raw_blocks = [b for b in existing if b.block_type == "raw_html"]
    other_ids = {b.id for b in existing if b.block_type != "raw_html"}
    originals = {
        lang: {(b.id, i): markup for b in raw_blocks for i, markup in _raw_pieces_for(b, lang).items()} for lang in LANGS
    }

    runs: dict[str, list[str]] = {}
    layouts: dict[str, list] = {}
    for lang in LANGS:
        runs[lang], layouts[lang] = _runs(posted[lang], originals[lang])
    # Structure comes from uz; only ids that still exist on this page can be kept.
    layout = [(kind, ref) for kind, ref in layouts["uz"] if kind == "run" or ref in other_ids]
    kept_ids = [ref for kind, ref in layout if kind == "id"]

    def text_of_run(lang: str, index: int) -> str:
        if lang == "uz":
            return runs["uz"][index]
        same_shape = _shape(layouts[lang]) == _shape(layouts["uz"])
        if same_shape and index < len(runs[lang]):
            return runs[lang][index]
        # ru/en whose chips no longer line up with uz: their whole text goes to the first run rather than being lost
        if index == 0:
            return "\n".join(runs[lang]) or _EMPTY_RUN
        return _EMPTY_RUN

    stored_layout = [("run", 0) if b.block_type == "raw_html" else ("id", b.id) for b in existing]
    layout_unchanged = _shape(layout) == _shape(stored_layout)

    # Which existing raw block holds which run: in order. Untouched languages keep their stored html when the layout
    # did not change, so a save that edited only Uzbek leaves ru/en byte for byte as they were.
    reuse = list(raw_blocks)
    plan: list[tuple] = []
    run_index = 0
    for kind, ref in layout:
        if kind == "id":
            plan.append(("keep", ref))
            continue
        block = reuse.pop(0) if reuse else None
        data = {}
        for lang in LANGS:
            old = dict((block.data.get(lang) or {}) if block is not None else {})
            if block is not None and layout_unchanged and posted[lang] == produced[lang]:
                data[lang] = old or {"html": _EMPTY_RUN}
            else:
                old["html"] = text_of_run(lang, run_index)
                data[lang] = old
        slug = ((block.data.get("uz") or {}).get("slug") if block is not None else None) or page.slug
        for lang in LANGS:
            data[lang].setdefault("slug", slug)
        plan.append(("raw", block, data))
        run_index += 1

    surviving = {item[1].id for item in plan if item[0] == "raw" and item[1] is not None} | set(kept_ids)
    ContentBlock.objects.filter(page=page).exclude(id__in=surviving).delete()
    for block in ContentBlock.objects.filter(page=page):  # (page, order) is unique: park survivors out of the way
        block.order += 1_000_000
        block.save(update_fields=["order"])
    by_id = {b.id: b for b in ContentBlock.objects.filter(page=page)}

    order = 1
    for item in plan:
        if item[0] == "keep":
            block = by_id[item[1]]
            block.order = order
            block.save(update_fields=["order"])
        else:
            _, block, data = item
            if block is not None:
                block = by_id[block.id]
                block.order = order
                block.data = data
                block.full_clean()
                block.save()
            else:
                block = ContentBlock(page=page, order=order, block_type="raw_html", data=data)
                block.full_clean()
                block.save()
        order += 1
    page.save(update_fields=["updated_at"])
    return True
