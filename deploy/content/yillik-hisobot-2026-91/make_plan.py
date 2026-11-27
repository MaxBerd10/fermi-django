"""Builds plan.json (read-only):  python manage.py shell < deploy/content/yillik-hisobot-2026-91/make_plan.py"""
import json
import re
from pathlib import Path
from urllib.parse import unquote

from apps.content.migration_tools import sha
from apps.content.models import Page

LANGS = ("uz", "ru", "en")
SLUG = "17-goals-of-un-policies"
# order of the paragraph -> the card captions in uz / ru (translations of the English title of the PDF) / en (the title of the PDF itself)
CAPTIONS = {
    5: {"uz": "Tengsizlikni kamaytirish siyosati", "ru": "Политика по сокращению неравенства"},
    12: {"uz": "Dengizlar va suv ekotizimlarini muhofaza qilish siyosati", "ru": "Политика по защите морей и водных пространств"},
    18: {"uz": "Barqaror ishlab chiqarish va iste'mol siyosati".replace("'", "ʻ"), "ru": "Политика устойчивого производства и потребления"},
}
page = Page.objects.get(slug=SLUG)
entries = []
for order, caps in CAPTIONS.items():
    block = page.blocks.get(order=order)
    assert block.block_type == "paragraph"
    m = re.fullmatch(r"\[([^\]]+)\]\((https://fermi\.uz/media/([^)]+\.pdf))\)", block.data["uz"]["text"])
    assert m, order
    assert all(block.data[lang]["text"] == block.data["uz"]["text"] for lang in LANGS)  # the same line in the three languages
    entries.append({"slug": SLUG, "order": order, "media_path": unquote(m.group(3)), "captions": {**caps, "en": m.group(1)},
                    "fp": {lang: sha(block.data[lang]) for lang in LANGS}})
Path("deploy/content/yillik-hisobot-2026-91/plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "entries:", [e["media_path"][-60:] for e in entries])
