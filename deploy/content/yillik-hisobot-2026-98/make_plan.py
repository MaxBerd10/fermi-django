"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-98/make_plan.py"""
import json
import re
from pathlib import Path

from apps.content.migration_tools import sha
from apps.content.models import ContentBlock

LANGS = ("uz", "ru", "en")
TITLES = {"uz": "Xarita", "ru": "Карта", "en": "Map"}
SRC_RE = re.compile(r"https://www\.google\.com/maps/embed\?pb=[A-Za-z0-9!%._\-]+")
entries = []
for block in ContentBlock.objects.filter(block_type="raw_html").select_related("page").order_by("page__slug", "order"):
    html = block.data["uz"]["html"]
    if "google.com/maps" not in html:
        continue
    assert all(block.data[lang]["html"] == html for lang in LANGS), block  # the same <iframe> in the three languages
    m = re.fullmatch(r'\s*<p>\s*<iframe[^>]*\bsrc="([^"]+)"[^>]*\bheight="(\d+)"[^>]*></iframe>\s*</p>\s*', html) or re.fullmatch(r'\s*<p>\s*<iframe[^>]*\bheight="(\d+)"[^>]*\bsrc="([^"]+)"[^>]*></iframe>\s*</p>\s*', html)
    assert m, block
    src, height = (m.group(1), int(m.group(2))) if m.group(1).startswith("http") else (m.group(2), int(m.group(1)))
    clean = SRC_RE.match(src).group(0)
    assert src.startswith(clean) and (src == clean or src[len(clean)] == " "), (block, src[len(clean):][:30])
    entries.append({"slug": block.page.slug, "order": block.order, "count": 1, "fp": [{lang: sha(block.data[lang]) for lang in LANGS}],
                    "blocks": [{"block_type": "embed", "data": {lang: {"provider": "map", "src": clean, "height": height, "title": TITLES[lang]} for lang in LANGS}}]})
Path("deploy/content/yillik-hisobot-2026-98/plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "entries on", len({e["slug"] for e in entries}), "pages")
