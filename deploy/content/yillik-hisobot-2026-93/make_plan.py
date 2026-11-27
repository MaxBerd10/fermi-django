"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-93/make_plan.py"""
import json
import re
from pathlib import Path

from apps.content.migration_tools import sha
from apps.content.models import Page

LANGS = ("uz", "ru", "en")
TITLES = {  # the titles YouTube prints for the videos (oEmbed), the backtick / typographic apostrophe of the uz ones put as U+02BB
    "Mg6MBqg4f5o": "Dermatovenerologiya va dermatoonkopatologiyada diagnostika IV xalqaro ilmiy-amaliy konferensiya",
    "7F4qi9PEtKQ": "Test sinovlarini oʻtkazish tartibi (oʻzbek tilida)",
    "seD6Xs647rI": "Test materiallaridan foydalanish",
    "Kk2XS_td190": "Порядок проведения тестовых испытаний (на русском языке)",
    "RFGX89bZsCY": "Работа с тестовыми материалами",
}
PAGES = [("ilmiy-konferensiyalar", 1), ("test-sinovlarini-otkazish-tartibi-2025", 1), ("test-materiallaridan-foydalanish-2025", 1)]
entries = []
for slug, order in PAGES:
    block = Page.objects.get(slug=slug).blocks.get(order=order)
    assert block.block_type == "raw_html"
    data = {}
    for lang in LANGS:  # the uz page shows the Uzbek video, ru and en the Russian one: each language keeps its own
        m = re.fullmatch(r'\s*<p>\s*<iframe[^>]*\bsrc="https://www\.youtube\.com/embed/([A-Za-z0-9_-]{11})"[^>]*></iframe>\s*</p>\s*', block.data[lang]["html"])
        assert m, (slug, lang)
        data[lang] = {"provider": "youtube", "video_id": m.group(1), "title": TITLES[m.group(1)]}
    entries.append({"slug": slug, "order": order, "count": 1, "fp": [{lang: sha(block.data[lang]) for lang in LANGS}],
                    "blocks": [{"block_type": "embed", "data": data}]})
Path("deploy/content/yillik-hisobot-2026-93/plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "entries:", [[e["blocks"][0]["data"][l]["video_id"] for l in LANGS] for e in entries])
