"""Builds docs/ADMIN_QOLLANMA.pdf from the same JSON the in-panel Help page shows
(frontend/src/admin/help/helpContent.json), so the printable guide and the panel never drift apart.

    python3 scripts/build_admin_guide_pdf.py        (needs PyMuPDF: pip install pymupdf)
"""
import html
import json
import shutil
import tempfile
from pathlib import Path

import pymupdf

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "frontend/src/admin/help/helpContent.json"
OUTPUT = ROOT / "docs/ADMIN_QOLLANMA.pdf"
FONT_DIR = Path("/System/Library/Fonts/Supplemental")   # Arial: has the Uzbek letters oʻ gʻ and the tutuq belgisi

CSS = """
@font-face { font-family: guide; src: url(Arial.ttf); }
@font-face { font-family: guide; font-weight: bold; src: url(ArialBold.ttf); }
body { font-family: guide; font-size: 10.5pt; line-height: 1.45; color: #1a1d2e; }
h1 { font-size: 22pt; color: #0a1158; margin: 0 0 4pt 0; }
.sub { color: #555a73; margin: 0 0 14pt 0; }
h2 { font-size: 14pt; color: #0a1158; margin: 16pt 0 6pt 0; border-bottom: 1.5pt solid #ffd600; padding-bottom: 3pt; }
p { margin: 0 0 6pt 0; }
.t { font-weight: bold; margin: 8pt 0 3pt 0; }
ol, ul { margin: 0 0 6pt 0; padding-left: 18pt; }
li { margin-bottom: 3pt; }
.box { margin: 6pt 0 8pt 0; padding: 6pt 9pt; }
.warn { background-color: #fff3cd; border: 1pt solid #e0b84a; }
.tip { background-color: #e8edff; border: 1pt solid #9db0ee; }
.box .t { margin-top: 0; }
table { width: 100%; border-collapse: collapse; margin: 4pt 0 8pt 0; }
th { background-color: #eef0f6; text-align: left; padding: 4pt 6pt; font-size: 9pt; }
td { border-top: 0.5pt solid #ccd0e0; padding: 4pt 6pt; vertical-align: top; }
"""


def esc(text: str) -> str:
    return html.escape(text, quote=False)


def block_html(block: dict) -> str:
    kind = block["type"]
    if kind == "p":
        return f"<p>{esc(block['text'])}</p>"
    if kind == "steps":
        items = "".join(f"<li>{esc(i)}</li>" for i in block["items"])
        return f"<p class='t'>{esc(block['title'])}</p><ol>{items}</ol>"
    if kind in ("warn", "tip"):
        items = "".join(f"<li>{esc(i)}</li>" for i in block["items"])
        return f"<div class='box {kind}'><p class='t'>{esc(block['title'])}</p><ul>{items}</ul></div>"
    if kind == "table":
        head = "".join(f"<th>{esc(h)}</th>" for h in block["head"])
        rows = "".join("<tr>" + "".join(f"<td>{esc(c)}</td>" for c in row) + "</tr>" for row in block["rows"])
        return f"<table><tr>{head}</tr>{rows}</table>"
    raise ValueError(kind)


def main() -> None:
    data = json.loads(CONTENT.read_text(encoding="utf-8"))
    body = [f"<h1>{esc(data['title'])}</h1><p class='sub'>{esc(data['subtitle'])}</p>"]
    for section in data["sections"]:
        body.append(f"<h2>{esc(section['title'])}</h2>")
        body.extend(block_html(b) for b in section["blocks"])
    document = "<html><body>" + "".join(body) + "</body></html>"

    with tempfile.TemporaryDirectory() as tmp:
        shutil.copy(FONT_DIR / "Arial.ttf", Path(tmp) / "Arial.ttf")
        shutil.copy(FONT_DIR / "Arial Bold.ttf", Path(tmp) / "ArialBold.ttf")
        story = pymupdf.Story(html=document, user_css=CSS, archive=pymupdf.Archive(tmp))
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        writer = pymupdf.DocumentWriter(str(OUTPUT))
        page_rect = pymupdf.paper_rect("a4")
        content_rect = page_rect + (48, 48, -48, -54)
        more = True
        while more:
            device = writer.begin_page(page_rect)
            more, _ = story.place(content_rect)
            story.draw(device)
            writer.end_page()
        writer.close()
    print("wrote", OUTPUT)


if __name__ == "__main__":
    main()
