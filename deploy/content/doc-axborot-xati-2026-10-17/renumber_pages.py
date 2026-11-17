"""Re-cuts the ru / en PDFs of the information letter from the ORIGINAL 6-page file and renumbers the footer.

The original has the letter in three languages on pages 1-2 (uz), 3-4 (ru), 5-6 (en); every page carries its page number
in the footer ("... | 3"). Cut into separate 2-page files, the Russian file began with "3" and the English with "5".
The footer number is a separate text object ([(3)] TJ) in the page's own font, so it is changed in place: same font,
size, colour and position, no covering box. Nothing else on the page is touched. The Uzbek file already starts at 1.

usage:  python3 renumber_pages.py <original-6-page.pdf> <output-dir>      (needs PyMuPDF)
"""
import re
import sys

import pymupdf

src_path, out_dir = sys.argv[1], sys.argv[2]
PARTS = {  # lang -> (first page, last page, document title)
    "ru": (2, 3, "Информационное письмо: международная научно-практическая конференция «Роль здорового питания в здоровье населения» (17 октября 2026 года)"),
    "en": (4, 5, "Information letter: international scientific and practical conference “The Role of Healthy Nutrition in Population Health” (17 October 2026)"),
}
# the footer number: the one text object that draws a single digit in the small grey footer font
FOOTER = re.compile(rb"(1 0 0 1 [\d.]+ 27\.12 Tm\r?\n0\.42 0\.435 0\.502 rg\r?\n0\.42 0\.435 0\.502 RG\r?\n\[\()(\d)(\)\] TJ)")

src = pymupdf.open(src_path)
for lang, (first, last, title) in PARTS.items():
    out = pymupdf.open()
    out.insert_pdf(src, from_page=first, to_page=last)
    for number, page in enumerate(out, start=1):
        xrefs = page.get_contents()
        assert len(xrefs) == 1, "expected one content stream per page"
        stream = out.xref_stream(xrefs[0])
        hits = FOOTER.findall(stream)
        assert len(hits) == 1, "%s page %d: expected exactly one footer number, found %d" % (lang, number, len(hits))
        new_stream = FOOTER.sub(lambda m: m.group(1) + str(number).encode() + m.group(3), stream)
        out.update_stream(xrefs[0], new_stream)
    out.set_metadata({"title": title, "author": "", "subject": "", "keywords": "", "creator": "", "producer": ""})
    out.subset_fonts()
    out.save("%s/axborot-xati-2026-10-17-%s.pdf" % (out_dir, lang), garbage=4, deflate=True, clean=True)
    print("wrote", lang)
