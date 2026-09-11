"""
Pairs up the three independently-extracted per-language ExtractionResults
(see html_extract.py) into single blocks/staff that carry all three
languages together -- what ContentBlock.data and StaffMember actually need.

Reality check from a dry run against all 30 live departments: naive
positional pairing (item #N in uz = item #N in ru = item #N in en) breaks
almost everywhere except the one department first inspected by hand -- the
old site's uz/ru/en bodies are independently authored HTML documents with
real structural drift (missing sections, reordered paragraphs, a
translation that's a stub compared to its uz original), not just markup
noise. So:

  * Blocks are aligned uz-vs-ru and uz-vs-en separately, using
    difflib.SequenceMatcher (stdlib, no custom diff algorithm) over a
    per-block "symbol" -- but that symbol is (block_type, length_bucket),
    not block_type alone. A real bug found live (a news post where ru was
    missing one paragraph uz had in the middle of an otherwise 1:1 run):
    matching on type alone treats a long run of same-typed blocks
    (paragraph, paragraph, paragraph, ...) as indistinguishable symbols, so
    SequenceMatcher can't tell WHICH position is the true gap and picks an
    arbitrary one -- silently shifting every block after it by one and
    confidently pairing unrelated sentences across languages. That's worse
    than a missed match (an honest fallback): it looks like a translation
    but says something else. Bucketing each block's own text length (a
    real bitext-alignment technique -- translations of the same sentence
    are rarely wildly different lengths, even across scripts) gives same-
    type blocks distinct-enough symbols that the true gap is identifiable.
  * uz is always the spine (old schema: content_uz is NOT NULL, content_ru
    /content_en are nullable and frequently much shorter -- uz is the
    closest thing this data has to a "canonical" version).
  * A uz block with no confident match in a language falls back to uz's own
    text for that language, and is counted in `fallback_count` so the
    report -- and later, an admin -- can see how much of a department still
    needs real translation instead of a silent copy.
  * Staff are aligned by photo filename (language-independent -- the same
    photo is reused verbatim across uz/ru/en for a given person) rather
    than by name text, since transliterated names don't match as strings.
    A staff member with no photo, or no cross-language match, also falls
    back to uz's own name/title/bio.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher

from .html_extract import ExtractedBlock, ExtractedStaff, ExtractionResult

LANGS = ("uz", "ru", "en")
OTHER_LANGS = ("ru", "en")

_LENGTH_BUCKET_CHARS = 20  # coarse enough to tolerate normal cross-language length variance


def _text_len(block: ExtractedBlock) -> int:
    if block.block_type in ("heading", "paragraph"):
        return len(block.payload.get("text", ""))
    if block.block_type == "list":
        return len(" ".join(block.payload.get("items", [])))
    if block.block_type == "staff_card":
        return len(block.payload.get("full_name", "")) + len(block.payload.get("title", "") or "")
    return 0  # image/video/document/gallery/table -- no text to compare, type alone is enough


def _block_symbol(block: ExtractedBlock) -> tuple:
    return (block.block_type, _text_len(block) // _LENGTH_BUCKET_CHARS)


@dataclass
class MergedBlock:
    block_type: str
    payload_by_lang: dict[str, dict]
    fallback_langs: tuple[str, ...] = ()  # languages that got uz's text, not their own


@dataclass
class MergedStaff:
    full_name_by_lang: dict[str, str]
    title_by_lang: dict[str, str]
    bio_by_lang: dict[str, str]
    photo_src: str | None
    fallback_langs: tuple[str, ...] = ()


@dataclass
class MergeResult:
    blocks: list[MergedBlock] = field(default_factory=list)
    staff: list[MergedStaff] = field(default_factory=list)
    fallback_block_count: int = 0
    fallback_staff_count: int = 0


def _align_indices(uz_symbols: list[tuple], other_symbols: list[tuple]) -> dict[int, int]:
    """uz index -> other-language index, for positions inside a matching run
    of equal (type, length_bucket) symbols. Positions outside any matching
    run are absent."""
    matcher = SequenceMatcher(None, uz_symbols, other_symbols, autojunk=False)
    mapping: dict[int, int] = {}
    for uz_start, other_start, size in matcher.get_matching_blocks():
        for offset in range(size):
            mapping[uz_start + offset] = other_start + offset
    return mapping


def _merge_blocks(results: dict[str, ExtractionResult]) -> tuple[list[MergedBlock], int]:
    uz_blocks = results["uz"].blocks
    uz_symbols = [_block_symbol(b) for b in uz_blocks]
    index_maps = {
        lang: _align_indices(uz_symbols, [_block_symbol(b) for b in results[lang].blocks])
        for lang in OTHER_LANGS
    }

    merged: list[MergedBlock] = []
    fallback_count = 0
    for i, uz_block in enumerate(uz_blocks):
        payload_by_lang = {"uz": uz_block.payload}
        fallback_langs = []
        for lang in OTHER_LANGS:
            j = index_maps[lang].get(i)
            if j is not None:
                payload_by_lang[lang] = results[lang].blocks[j].payload
            else:
                payload_by_lang[lang] = uz_block.payload
                fallback_langs.append(lang)
        if fallback_langs:
            fallback_count += 1
        merged.append(MergedBlock(uz_block.block_type, payload_by_lang, tuple(fallback_langs)))
    return merged, fallback_count


def _staff_by_photo(staff: list[ExtractedStaff]) -> dict[str, ExtractedStaff]:
    return {s.photo_src: s for s in staff if s.photo_src}


def _merge_staff(results: dict[str, ExtractionResult]) -> tuple[list[MergedStaff], int]:
    uz_staff = results["uz"].staff
    by_photo = {lang: _staff_by_photo(results[lang].staff) for lang in OTHER_LANGS}

    merged: list[MergedStaff] = []
    fallback_count = 0
    for person in uz_staff:
        full_name = {"uz": person.full_name}
        title = {"uz": person.title}
        bio = {"uz": person.bio}
        fallback_langs = []
        for lang in OTHER_LANGS:
            match = by_photo[lang].get(person.photo_src) if person.photo_src else None
            if match:
                full_name[lang] = match.full_name
                title[lang] = match.title
                bio[lang] = match.bio
            else:
                full_name[lang] = person.full_name
                title[lang] = person.title
                bio[lang] = person.bio
                fallback_langs.append(lang)
        if fallback_langs:
            fallback_count += 1
        merged.append(MergedStaff(full_name, title, bio, person.photo_src, tuple(fallback_langs)))
    return merged, fallback_count


def merge_languages(results: dict[str, ExtractionResult]) -> MergeResult:
    blocks, block_fallbacks = _merge_blocks(results)
    staff, staff_fallbacks = _merge_staff(results)
    return MergeResult(
        blocks=blocks,
        staff=staff,
        fallback_block_count=block_fallbacks,
        fallback_staff_count=staff_fallbacks,
    )
