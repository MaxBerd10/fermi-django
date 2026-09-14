import re

from django.db import models

from .block_schemas import validate_block_data

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{5,}\d")
_URL_RE = re.compile(r"https?://\S+|www\.\S+")
_HANDLE_RE = re.compile(r"@[A-Za-z0-9_]+")
_CYRILLIC_RE = re.compile(r"[Ѐ-ӿ]")
_LATIN_RE = re.compile(r"[A-Za-z]")


def _is_language_invariant(text: str) -> bool:
    """Contact details (phone numbers, emails), bare URLs and @handles
    (Telegram/Instagram, etc.) are correctly identical across languages once
    the surrounding label ("Tel.", "fax", "e-mail") already reads the same in
    Uzbek and English -- there's no prose left to translate. True when
    stripping any email/phone/URL/handle matches out of the text leaves next
    to no letters behind."""
    stripped = _EMAIL_RE.sub("", text)
    stripped = _PHONE_RE.sub("", stripped)
    stripped = _URL_RE.sub("", stripped)
    stripped = _HANDLE_RE.sub("", stripped)
    return sum(1 for ch in stripped if ch.isalpha()) <= 6


_NAME_RE = re.compile(
    r"^[A-Z][A-Za-z.ʻ‘’'`-]*(?:\s+[A-Z][A-Za-z.ʻ‘’'`-]*){1,4}"
    r"(?:\s+(?:[Qq]izi|[Oo][ʻ‘’'`][Gg][ʻ‘’'`][Ll]i))?$"
)


def _is_personal_name(text: str) -> bool:
    """A person's full name (staff bylines: "Xamdamova Shaxnoza
    Yusupalievna", "Sh. Mirziyoyev", "Abdurahimova Manzura Shokirjon qizi")
    is written in Latin script in both uz and en -- there's nothing to
    translate, so an identical 'en' value is correct, not a missing
    translation. Detected as 2-5 capitalized words, optionally followed by
    the lowercase Uzbek patronymic suffix "qizi"/"o'g'li", with no
    sentence-ending punctuation."""
    return bool(_NAME_RE.match(text.strip()))


def _is_ru_source_text(text: str) -> bool:
    """A handful of legacy blocks have Russian prose sitting directly in the
    'uz' slot -- a data-entry mistake on the original site, not a missing
    translation. For those, the correct 'ru' value is simply the same text,
    which would otherwise look like an untranslated fallback copy. Detected
    by the text being predominantly Cyrillic."""
    cyrillic = len(_CYRILLIC_RE.findall(text))
    latin = len(_LATIN_RE.findall(text))
    return cyrillic > 0 and cyrillic >= latin * 3


# A handful of legacy blocks hold genuine English-language source material
# (international-partnership press content, lab-test terms) directly in the
# 'uz' slot -- so an identical 'en' value is the correct translation, not a
# missing one. Verified by hand, one at a time, rather than guessed at with
# a heuristic, since a false positive here would silently skip a block that
# actually still needs translating.
_ENGLISH_SOURCE_BLOCK_IDS = {
    18644, 18739, 18976, 19127, 19128, 19129, 19131, 19132,
    19134, 19135, 19137, 19138, 19139, 19472, 19473, 19475,
    25294, 25550, 25901, 26143, 26163, 26363, 26471,
    # USMLE-style clinical topic checklists (kidney/genetics/heme/cell-bio/
    # micro/biochem/musculoskeletal study outlines) authored directly in
    # English -- there is no separate English "translation" to write.
    29533, 29535, 29537, 29539, 29541, 29543, 29546,
    # USMLE program description (Wikipedia-sourced) and the Thumbay Fergana
    # College of Medical Sciences / Gulf Medical University partnership copy
    # -- both authored directly in English for this English-language
    # partnership announcement.
    27068, 27069, 27071, 27072, 27073, 27074,
    27125, 27126, 27127, 27129, 27130, 27132, 27133, 27134, 27135,
    27136, 27137, 27138, 27139,
    # Journal article/dissertation titles submitted to this institute in
    # English by their (non-Uzbek) authors -- the title itself is the
    # English source; only a Russian rendering is a real translation.
    27226, 27227, 27230, 27241, 27242, 27245, 27253, 27262,
    27286, 27287, 27291, 27309, 27310, 27313, 27317, 27321, 27323,
    27324, 27329, 27331, 27334, 27336, 27337, 27338, 27340, 27346,
    27349, 27352, 27366, 27367, 27378, 27382, 27394, 27396, 27399,
    27401, 27404, 27405, 27406,
    # Fergana Medical Institute of Public Health "Green University"
    # sustainability-policy page (mission/vision statements, UN SDG policy
    # titles) and the India representative-office address block, both
    # authored directly in English for this English-language section.
    28318, 28319, 28320, 28321, 28327, 28328, 28329, 28331,
    28333, 28334, 28336, 28338, 28339, 28340, 28341, 28342,
    28343, 28344, 28345, 28346, 28347, 28348, 28349, 28350,
    28351, 28352, 28353, 28354,
    # A second, near-duplicate "Green University" sustainability-report page
    # (report title plus the same policy statements) on a different Page.
    29611, 29613, 29614, 29615, 29616, 29617, 29618, 29619,
    29620, 29621, 29622, 29623, 29624, 29625, 29626, 29627,
    29628, 29629,
}

# A smaller handful are bare brand/product/institution names, a proper name
# in a byline, or a malformed URL (a stray space breaks the URL-invariance
# regex) with no translation in any language -- the same text is correct
# verbatim in uz, ru and en alike. Same hand-verified precedent as above.
# 27299 is a different edge case sharing this bucket: real Russian-language
# prose sitting in the 'uz' slot (already correctly handled for 'en'), but
# _is_ru_source_text's Cyrillic-ratio heuristic misses it because the
# embedded Latin scientific name "Helicobacter pylori" pulls the Latin
# character count too high -- hand-verified as needing no further work.
_PROPER_NOUN_BLOCK_IDS = {18891, 19107, 19921, 20836, 20784, 21213, 21711, 21853, 27299}


class Page(models.Model):
    """A generic structured content page — a department's body, a static page,
    etc. Whatever app needs rich content (departments, faculties, ...) points a
    ForeignKey/OneToOne at one of these instead of storing raw HTML itself."""

    slug = models.SlugField(max_length=255, unique=True)
    # Blank for every legacy-imported page (department/faculty/the 235
    # static pages) -- those get their displayed title from the linking
    # MenuItem's own label instead (see frontend's BlogPage ->
    # findTitleBySlug), which is real data for them and has no reason to
    # be duplicated here. Only meaningful for a page the admin panel
    # creates on its own (see admin_api/pages_views.py), which has no
    # MenuItem to borrow a title from.
    title_uz = models.CharField(max_length=255, blank=True)
    title_ru = models.CharField(max_length=255, blank=True)
    title_en = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.slug


class ContentBlock(models.Model):
    class BlockType(models.TextChoices):
        HEADING = "heading", "Heading"
        PARAGRAPH = "paragraph", "Paragraph"
        LIST = "list", "List"
        STAFF_CARD = "staff_card", "Staff card"
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        DOCUMENT = "document", "Document"
        GALLERY = "gallery", "Gallery"
        TABLE = "table", "Table"

    page = models.ForeignKey(Page, related_name="blocks", on_delete=models.CASCADE)
    order = models.PositiveIntegerField()
    block_type = models.CharField(max_length=20, choices=BlockType.choices)
    # {"uz": {...}, "ru": {...}, "en": {...}} — shape of each language's payload
    # depends on block_type, enforced by clean() below. See block_schemas.py.
    data = models.JSONField()

    class Meta:
        ordering = ["order"]
        constraints = [
            models.UniqueConstraint(fields=["page", "order"], name="unique_block_order_per_page"),
        ]

    # The prose field to compare across languages when checking whether a
    # block still needs real translation -- see needs_translation below.
    _TRANSLATABLE_FIELD = {
        "heading": "text",
        "paragraph": "text",
        "staff_card": "full_name",
    }

    def clean(self):
        validate_block_data(self.block_type, self.data)

    def __str__(self) -> str:
        return f"{self.page.slug} #{self.order} ({self.block_type})"

    @property
    def needs_translation(self) -> bool:
        """True when two of the three languages carry byte-identical prose --
        in practice this only happens when a language's real text wasn't
        available and a fallback copy was used instead (see the legacy
        import's merge.py), since genuine independent translations are never
        character-for-character equal. Not meaningful for media blocks
        (image/video/document/gallery/table), which have no single prose
        field to compare."""
        field = self._TRANSLATABLE_FIELD.get(self.block_type)
        if field:
            uz_value = self.data.get("uz", {}).get(field)
            if not isinstance(uz_value, str):
                return False
            if _is_language_invariant(uz_value):
                return False
            if self.id in _PROPER_NOUN_BLOCK_IDS:
                return False
            for lang in ("ru", "en"):
                if self.data.get(lang, {}).get(field) != uz_value:
                    continue
                if lang == "ru" and _is_ru_source_text(uz_value):
                    continue
                if lang == "en" and (
                    self.id in _ENGLISH_SOURCE_BLOCK_IDS or _is_personal_name(uz_value)
                ):
                    continue
                return True
            return False
        if self.block_type == "list":
            if self.id in _PROPER_NOUN_BLOCK_IDS:
                return False
            uz_items = tuple(self.data.get("uz", {}).get("items", []))
            for lang in ("ru", "en"):
                if tuple(self.data.get(lang, {}).get("items", [])) != uz_items:
                    continue
                if lang == "en" and self.id in _ENGLISH_SOURCE_BLOCK_IDS:
                    continue
                return True
            return False
        return False
