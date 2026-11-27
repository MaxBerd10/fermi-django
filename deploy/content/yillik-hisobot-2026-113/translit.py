"""Uzbek Latin -> Russian Cyrillic for personal names (the usual way Uzbek names are written in Russian). Rules, checked by hand on the 101 names of the certificate page."""
import re

APOS = "ʻʼ‘’'`´"
APOS_RE = re.compile("[%s]" % re.escape(APOS))
VOWELS = "aeiouаеиоуы"


def _word(w):
    low = APOS_RE.sub("ʻ", w.lower())
    out = []
    i = 0
    n = len(low)
    while i < n:
        c = low[i]
        nxt = low[i + 1] if i + 1 < n else ""
        nxt2 = low[i + 2] if i + 2 < n else ""
        two = low[i:i + 2]
        three = low[i:i + 3]
        if three == "yoʻ":
            out.append("ю"); i += 3; continue
        if two in ("oʻ",):
            out.append("у"); i += 2; continue
        if two == "gʻ":
            out.append("г"); i += 2; continue
        if c == "ʻ":
            out.append("ъ" if out and out[-1] in VOWELS else ""); i += 1; continue
        if two == "sh":
            out.append("ш"); i += 2; continue
        if two == "ch":
            out.append("ч"); i += 2; continue
        if two == "dj":
            out.append("дж"); i += 2; continue
        if two == "yo":
            out.append("ё"); i += 2; continue
        if two == "yu":
            out.append("ю"); i += 2; continue
        if two == "ya":
            out.append("я"); i += 2; continue
        if two == "ye":
            out.append("е"); i += 2; continue
        if two == "yi":
            out.append("и"); i += 2; continue
        if c == "e":
            out.append("э" if i == 0 else "е"); i += 1; continue
        if c == "y":
            out.append("й"); i += 1; continue
        table = {"a": "а", "b": "б", "d": "д", "f": "ф", "g": "г", "h": "х", "i": "и", "j": "ж", "k": "к", "l": "л", "m": "м", "n": "н", "o": "о", "p": "п",
                 "q": "к", "r": "р", "s": "с", "t": "т", "u": "у", "v": "в", "x": "х", "z": "з", "c": "ц", "w": "в"}
        if c in table:
            out.append(table[c])
        elif c.isalpha() and re.match("[а-яё]", c):
            out.append(c)
        else:
            out.append(c)
        i += 1
    text = "".join(out)
    if not w:
        return w
    # case: first letter of the source decides
    if w.isupper() and len(w) > 3:
        return text.upper()
    if w[0].isupper():
        return text[:1].upper() + text[1:]
    return text


def name_ru(name):
    """'Jurayev Xusanboy Ergashbayevich' -> 'Жураев Хусанбой Эргашбаевич'; tokens that are not words (initials, XXX, digits) stay."""
    parts = re.split(r"(\s+)", name.strip())
    result = []
    for part in parts:
        if not part.strip() or re.fullmatch(r"[A-Z]{1,3}\.?|[A-Z]\.", part) or not re.search(r"[A-Za-zʻ]", part) or part.upper() == "XXX":
            result.append(part)
        else:
            result.append(_word(part))
    return "".join(result)
