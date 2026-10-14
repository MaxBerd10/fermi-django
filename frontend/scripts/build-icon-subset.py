#!/usr/bin/env python3
"""Rebuilds public/vendor/remixicon/remixicon-used.{css,ttf}: the icon font holding only the `ri-*` classes the
frontend actually uses (the full font is ~177 kB, the subset ~27 kB). Run it after adding an icon class anywhere in
src/ or index.html, then commit the two generated files:

    python3 -m venv /tmp/fontvenv && /tmp/fontvenv/bin/pip install fonttools brotli
    /tmp/fontvenv/bin/python scripts/build-icon-subset.py
"""
import re
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = Path(__file__).resolve().parent.parent
VENDOR = ROOT / "public" / "vendor" / "remixicon"

full_css = (VENDOR / "remixicon.min.css").read_text()
codepoints = {m.group(1): m.group(2) for m in re.finditer(r"\.(ri-[a-z0-9-]+):before\{content:\"\\([0-9a-f]+)\"\}", full_css)}

used: set[str] = set()
sources = list((ROOT / "src").rglob("*.ts*")) + list((ROOT / "src").rglob("*.json")) + [ROOT / "index.html"]
for path in sources:
    used.update(re.findall(r"\bri-[a-z0-9]+(?:-[a-z0-9]+)*", path.read_text(errors="ignore")))
# Some classes come from the database (menu / category / social icons chosen in the admin), so what the current
# subset already holds is kept: this script only ever adds icons.
existing = VENDOR / "remixicon-used.css"
if existing.exists():
    used.update(re.findall(r"\.(ri-[a-z0-9-]+):before", existing.read_text()))
used = {name for name in used if name in codepoints}

options = subset.Options()
options.layout_features = []
options.name_IDs = []
options.notdef_outline = False
font = TTFont(VENDOR / "remixicon.woff2")
font.flavor = None
subsetter = subset.Subsetter(options)
subsetter.populate(unicodes=[int(codepoints[name], 16) for name in used])
subsetter.subset(font)
font.save(VENDOR / "remixicon-used.ttf")

rules = "".join(f'.{name}:before{{content:"\\{codepoints[name]}"}}' for name in sorted(used))
head = (
    '@font-face{font-family:remixicon;src:url("/vendor/remixicon/remixicon-used.ttf") format("truetype");font-display:swap}'
    '[class*=" ri-"],[class^=ri-]{font-family:remixicon!important;font-style:normal;'
    "-webkit-font-smoothing:antialiased;-moz-osx-font-smoothing:grayscale}"
)
(VENDOR / "remixicon-used.css").write_text(head + rules)
print(f"{len(used)} icons")
