"""Builds the PDF copy of the guide from the .docx (same colours, tables and callouts) so it can be opened in the browser.
Usage: python3 make_pdf.py <in.docx> <out.pdf>   (needs python-docx and Google Chrome)"""
import sys, html, subprocess, tempfile, os
import docx
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph
from docx.table import Table

src, out = sys.argv[1], sys.argv[2]
d = docx.Document(src)

def run_html(r):
    t = html.escape(r.text)
    if not t: return ""
    st = []
    if r.font.color is not None and r.font.color.type is not None: st.append(f"color:#{r.font.color.rgb}")
    if r.font.size: st.append(f"font-size:{r.font.size.pt}pt")
    if r.bold: st.append("font-weight:700")
    if r.italic: st.append("font-style:italic")
    return f'<span style="{";".join(st)}">{t}</span>'

def par_html(p, tag="p"):
    inner = "".join(run_html(r) for r in p.runs)
    cls = "li" if p.style.name.startswith("List") else ""
    if cls: return f'<li>{inner}</li>'
    return f"<{tag}>{inner or '&nbsp;'}</{tag}>"

def cell_html(tc, tag):
    tcPr = tc._tc.tcPr
    st = []
    shd = tcPr.find(qn("w:shd")) if tcPr is not None else None
    if shd is not None and shd.get(qn("w:fill")) not in (None, "auto"): st.append(f"background:#{shd.get(qn('w:fill'))}")
    bd = tcPr.find(qn("w:tcBorders")) if tcPr is not None else None
    if bd is not None:
        left = bd.find(qn("w:left"))
        if left is not None and left.get(qn("w:color")): st.append(f"border-left:5px solid #{left.get(qn('w:color'))}")
    body = ""
    for p in tc.paragraphs:
        body += par_html(p, "div")
    return f'<{tag} style="{";".join(st)}">{body}</{tag}>'

def table_html(t):
    single = len(t.rows) == 1 and len(t.columns) == 1
    cls = "box" if single else "grid"
    rows = ""
    for i, r in enumerate(t.rows):
        rows += "<tr>" + "".join(cell_html(c, "td") for c in r.cells) + "</tr>"
    return f'<table class="{cls}">{rows}</table>'

parts, in_list = [], False
for el in d.element.body.iterchildren():
    tag = el.tag.split("}")[1]
    if tag == "p":
        p = Paragraph(el, d)
        is_li = p.style.name.startswith("List")
        if is_li and not in_list: parts.append("<ul>"); in_list = True
        if not is_li and in_list: parts.append("</ul>"); in_list = False
        if is_li or p.text.strip(): parts.append(par_html(p))
    elif tag == "tbl":
        if in_list: parts.append("</ul>"); in_list = False
        parts.append(table_html(Table(el, d)))
if in_list: parts.append("</ul>")

page = f"""<!doctype html><html lang="uz"><head><meta charset="utf-8"><title>Konferensiya jurnalini indekslash qo‘llanmasi</title>
<style>
@page {{ size: A4; margin: 18mm 18mm 18mm 18mm }}
body {{ font-family: "Helvetica Neue", Arial, sans-serif; font-size: 10.5pt; color:#1A202C; line-height:1.5; margin:0 }}
p {{ margin: 0 0 8pt }} div {{ margin: 0 0 3pt }}
ul {{ margin: 0 0 10pt; padding-left: 18pt }} li {{ margin-bottom: 5pt }}
table {{ width:100%; border-collapse: collapse; margin: 6pt 0 10pt; page-break-inside: auto }}
tr {{ page-break-inside: avoid }}
table.box td {{ padding: 12pt 16pt }}
table.grid td {{ padding: 6pt 8pt; border:1px solid #CBD5E0; vertical-align: top }}
table.grid td div {{ margin:0 }}
* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact }}
</style></head><body>{''.join(parts)}</body></html>"""
with tempfile.TemporaryDirectory() as tmp:
    h = os.path.join(tmp, "g.html"); open(h, "w", encoding="utf-8").write(page)
    chrome = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    subprocess.run([chrome, "--headless=new", "--disable-gpu", "--no-pdf-header-footer", f"--print-to-pdf={out}", "file://" + h], check=True, capture_output=True)
print("wrote", out)
