"""
Tests for the cross-language block alignment in merge.py -- no Django or
database dependency, works directly on ExtractionResult objects.
"""
from .html_extract import ExtractedBlock, ExtractionResult
from .merge import merge_languages


def _para(text: str) -> ExtractedBlock:
    return ExtractedBlock("paragraph", {"text": text})


def test_a_missing_middle_paragraph_does_not_shift_everything_after_it():
    # Real bug found on a live news post: ru was missing one paragraph uz
    # had, in the middle of an otherwise 1:1 run of paragraphs. Matching on
    # block_type alone can't tell same-typed blocks apart, so SequenceMatcher
    # picked an arbitrary alignment and confidently paired every later
    # paragraph with the WRONG one -- displaying unrelated sentences side by
    # side as if they were translations of each other. That's worse than an
    # honest "no translation found" fallback: it looks correct but isn't.
    uz = ExtractionResult(
        blocks=[
            _para("Bugungi obhavo yaxshi va quyoshli boldi kun davomida."),
            _para("Qoshimcha jumla."),
            _para(
                "Ertaga barcha hududlarda kuchli yomgir yogishi kutilmoqda deb rasman "
                "ogohlantirildi va aholi ehtiyot boolishi soralmoqda butunlay."
            ),
        ]
    )
    ru = ExtractionResult(
        blocks=[
            _para("Segodnya pogoda byla horoshaya i solnechnaya ves den."),
            _para(
                "Zavtra vo vseh regionah strany ozhidaetsya silny dozhd, ob etom oficialno "
                "preduprezhdayut sinoptiki i naselenie prosyat byt ostorozhnym."
            ),
        ]
    )
    en = ExtractionResult(
        blocks=[
            _para("Today the weather was nice and sunny for the entire day."),
            _para(
                "Tomorrow heavy rain is expected in all regions of the country, forecasters "
                "officially warned and residents are asked to be careful today."
            ),
        ]
    )

    merged = merge_languages({"uz": uz, "ru": ru, "en": en})

    assert len(merged.blocks) == 3
    # block 0 must pair the real "today's weather" sentences, not something else
    assert merged.blocks[0].fallback_langs == ()
    assert "pogoda" in merged.blocks[0].payload_by_lang["ru"]["text"]
    assert "weather" in merged.blocks[0].payload_by_lang["en"]["text"]
    # block 1 (a uz-only insertion) has no real ru/en counterpart at all --
    # an honest fallback, not a confidently-wrong pairing
    assert merged.blocks[1].fallback_langs == ("ru", "en")
    # block 2 must pair the real "tomorrow's rain" sentences, not block 1's
    # fallback text or block 0's sentences
    assert merged.blocks[2].fallback_langs == ()
    assert "dozhd" in merged.blocks[2].payload_by_lang["ru"]["text"]
    assert "rain" in merged.blocks[2].payload_by_lang["en"]["text"]


def test_identical_length_paragraphs_still_align_positionally():
    # Sanity check that ordinary same-length runs (the common case) still
    # align 1:1 when there's genuinely nothing to disambiguate.
    uz = ExtractionResult(blocks=[_para("Birinchi xabar matni shu yerda."), _para("Ikkinchi xabar matni shu yerda.")])
    ru = ExtractionResult(blocks=[_para("Pervoe soobschenie tekst zdes."), _para("Vtoroe soobschenie tekst zdes.")])
    en = ExtractionResult(blocks=[_para("First message text goes here."), _para("Second message text goes here.")])

    merged = merge_languages({"uz": uz, "ru": ru, "en": en})

    assert len(merged.blocks) == 2
    assert merged.blocks[0].fallback_langs == ()
    assert merged.blocks[1].fallback_langs == ()
    assert "Pervoe" in merged.blocks[0].payload_by_lang["ru"]["text"]
    assert "Vtoroe" in merged.blocks[1].payload_by_lang["ru"]["text"]
