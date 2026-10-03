"""Keeps the Uzbek (`uz`) text in the Latin alphabet, whatever an editor types.

The site's canonical Uzbek is Latin (oʻ gʻ with U+02BB, tutuq belgisi U+02BC). Staff were filling the
same `uz` fields some in Cyrillic and some in Latin, and the machine translation to ru/en (and the
public pages) broke on the mix. Everything an admin form sends for an Uzbek field is therefore run
through `to_latin` on its way in -- see UzbekLatinJSONParser, which does this for every admin
request in one place -- and the translate endpoint does the same to its Uzbek source text.

Latin text passes through untouched, so the conversion is idempotent. HTML is handled tag-aware:
only the text between tags is converted, never a tag or attribute.
"""
import re

from rest_framework.parsers import JSONParser

_VOWELS = set("аеёиоуэюяўАЕЁИОУЭЮЯЎъЪьЬ")

# letter -> (lowercase latin, kind). kind "D" = digraph/longer (cased "Sh"/"SH"), "S" = single letter.
_MAP = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "ё": "yo", "ж": "j", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o", "п": "p", "р": "r", "с": "s",
    "т": "t", "у": "u", "ф": "f", "х": "x", "ц": "ts", "ч": "ch", "ш": "sh", "щ": "shch",
    "ы": "i", "э": "e", "ю": "yu", "я": "ya", "ў": "oʻ", "қ": "q", "ғ": "gʻ", "ҳ": "h",
    "ъ": "ʼ", "ь": "",
}
# Cyrillic letters that look exactly like a Latin one: inside a word that is otherwise Latin they
# are a keyboard slip ("bаhоlаsh" typed with Cyrillic а/о), so they map to their look-alike, not
# to their Cyrillic sound.
_HOMOGLYPHS = {
    "а": "a", "с": "c", "е": "e", "о": "o", "р": "p", "х": "x", "у": "y", "к": "k",
    "А": "A", "В": "B", "С": "C", "Е": "E", "Н": "H", "К": "K", "М": "M", "О": "O", "Р": "P",
    "Т": "T", "Х": "X",
}
_CYRILLIC_RE = re.compile("[Ѐ-ӿ]")
_LATIN_RE = re.compile("[A-Za-z]")
_WORD_RE = re.compile(r"[A-Za-zЀ-ӿʻʼ]+")
_TAG_SPLIT_RE = re.compile(r"(<[^>]*>)")


def has_cyrillic(text: str) -> bool:
    return bool(_CYRILLIC_RE.search(text))


def _convert_letter(ch: str, prev: str, nxt: str) -> str:
    lower = ch.lower()
    if lower == "е":
        latin = "ye" if (not prev or not prev.isalpha() or prev in _VOWELS) else "e"
    else:
        latin = _MAP.get(lower)
    if latin is None:
        return ch
    if not ch.isupper() or not latin:
        return latin
    letters = [c for c in latin if c.isalpha()]
    if len(letters) == 1:
        return latin.upper() if latin.isalpha() else latin
    # digraph from a capital: "Sh" normally, "SH" when it sits inside an all-caps word
    all_caps = (nxt.isalpha() and nxt.isupper()) or (prev.isalpha() and prev.isupper())
    if all_caps:
        return latin.upper()
    return latin[0].upper() + latin[1:]


def _convert_word(word: str) -> str:
    if not has_cyrillic(word):
        return word
    if _LATIN_RE.search(word):
        return "".join(_HOMOGLYPHS.get(ch, ch) for ch in word)
    out = []
    for i, ch in enumerate(word):
        prev = word[i - 1] if i else ""
        nxt = word[i + 1] if i + 1 < len(word) else ""
        out.append(_convert_letter(ch, prev, nxt))
    return "".join(out)


def _plain_to_latin(text: str) -> str:
    if not has_cyrillic(text):
        return text
    return _WORD_RE.sub(lambda m: _convert_word(m.group(0)), text)


def to_latin(text: str) -> str:
    """Cyrillic -> Latin Uzbek for plain text or editor HTML; anything already Latin is returned as is."""
    if not isinstance(text, str) or not has_cyrillic(text):
        return text
    if "<" not in text:
        return _plain_to_latin(text)
    return "".join(part if part.startswith("<") else _plain_to_latin(part) for part in _TAG_SPLIT_RE.split(text))


def latinize_payload(value, in_uz: bool = False):
    """Walks a parsed admin request body and converts every Uzbek string in place:
    values under a `*_uz` key, and everything below a bare `uz` key (the {uz, ru, en} block payloads)."""
    if isinstance(value, dict):
        for key in list(value):
            child = value[key]
            uz_here = in_uz or key == "uz" or (isinstance(key, str) and key.endswith("_uz"))
            if isinstance(child, str):
                if uz_here:
                    value[key] = to_latin(child)
            elif isinstance(child, (dict, list)):
                latinize_payload(child, uz_here)
    elif isinstance(value, list):
        for index, child in enumerate(value):
            if isinstance(child, str):
                if in_uz:
                    value[index] = to_latin(child)
            elif isinstance(child, (dict, list)):
                latinize_payload(child, in_uz)
    return value


class UzbekLatinJSONParser(JSONParser):
    """The default JSON parser, plus: on the admin API every Uzbek field in the body is converted to
    Latin before any view or serializer sees it. One chokepoint instead of a hook in each of the
    ~30 admin resources (several of which read `request.data` directly rather than validated_data)."""

    def parse(self, stream, media_type=None, parser_context=None):
        data = super().parse(stream, media_type, parser_context)
        request = (parser_context or {}).get("request")
        if request is not None and request.path.startswith("/api/v1/admin/"):
            latinize_payload(data)
        return data
