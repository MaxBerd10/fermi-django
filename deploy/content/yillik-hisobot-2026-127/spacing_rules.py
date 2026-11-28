"""Safe spacing fixes for visible texts. fix(text) returns the corrected text (the same text when nothing is wrong).

Never touches the address part of a [label](url) link or a token that is an address / a file name."""
import re

LINK = re.compile(r"(\]\([^)]*\))")
ADDRESS_TOKEN = re.compile(r"(?:https?://|www\.|@)|\.(?:uz|ru|com|org|net|edu|gov|de|pdf|jpe?g|png|docx?|xlsx?|pptx?|html?|php|zip|ssv|dtm|mf|fjsti)\b", re.I)
LOWER = "a-zа-яёўқғҳʻʼ"
UPPER = "A-ZА-ЯЁЎҚҒҲ"


def _token_at(text: str, pos: int) -> str:
    start = pos
    while start > 0 and not text[start - 1].isspace():
        start -= 1
    end = pos
    while end < len(text) and not text[end].isspace():
        end += 1
    return text[start:end]


def _fix_part(part: str) -> str:
    # 1) a space BEFORE , ; : ! ?  ("Examination , USMLE")  (not after a digit: "1 : 2")
    part = re.sub(r"(?<=[%s%s»”)\]]) +([,;:!?])(?=\s|$)" % (LOWER, UPPER), r"\1", part, flags=re.I)
    # 2) a space just inside quotes: “ text ” -> “text”. Only a quote that really is an opening one (not glued to a word before it, and
    # a closing quote follows it) / a closing one (followed by a space, punctuation or the end): the old texts sometimes use the wrong
    # curly quote ("tarzi“ va", "Xozirda ”Gistologiya"): those are left alone, joining them would glue two words.
    def opening(match):
        rest = part[match.end():]
        first = re.search(r"[”»“«\"]", rest)
        return match.group(1) if first and first.group(0) in "”»" else match.group(0)

    part = re.sub(r"(?<![\wʻʼ’])([“«]) +", opening, part)
    part = re.sub(r" +([”»])(?=[\s.,;:!?)\]]|$)", r"\1", part)

    # 3) a space is missing after . , ; : between two words
    def sentence(match):
        token = _token_at(part, match.start())
        if ADDRESS_TOKEN.search(token):
            return match.group(0)
        return match.group(1) + match.group(2) + " " + match.group(3)

    # . ; between a word of 3+ lower-case letters and the next capitalised word / a 3+ letter Cyrillic word
    part = re.sub(r"([%s]{3})([.;])([%s][%s]{2})" % (LOWER, UPPER, LOWER), sentence, part, flags=re.I if False else 0)
    part = re.sub(r"([а-яёўқғҳ]{3})([.;])([а-яё]{3})", sentence, part)
    # , between two words (3+ letters each)
    part = re.sub(r"([%s]{3})(,)([%s%s]{3})" % (LOWER, UPPER, LOWER), sentence, part)
    # : followed by a capital ("ishlari:Ilmiy")
    part = re.sub(r"([%s]{3})(:)([%s][%s]{2})" % (LOWER, UPPER, LOWER), sentence, part)

    # 4) a number glued to the word it counts: "20tadan" -> "20 tadan", "2019-2021yillar" -> "2019-2021 yillar"
    part = re.sub(r"(?<![\w.])(\d{1,4}(?:-\d{4})?)(tadan|nafar|yillar|sentyabrdagi)\b", r"\1 \2", part)
    return part


def fix(text: str) -> str:
    pieces = LINK.split(text)
    return "".join(piece if LINK.fullmatch(piece) else _fix_part(piece) for piece in pieces)
