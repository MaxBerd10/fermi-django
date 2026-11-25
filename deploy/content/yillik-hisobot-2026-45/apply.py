# The title of the document card (the PDF card under the picture) on four pages of Institut haqida -- yoʻriqnoma, kredit modul nizomi, test markazi nizomi, tuzilma --
# is given in uz, ru and en (the page's menu name; for the first three the corrected ru/en names of script 44). Until now the card showed the Uzbek file name in every language.
# Only the `caption` of the document block is set; the file stays.
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if it still is the document block with the fingerprints of plan.json and has no caption yet
# (edited in the admin since -> SKIPPED and listed); apply is one transaction with a backup (a second apply is refused); undo puts the old data back only where the
# block is still exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-45/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-45/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-45/apply.py
import json
import os

from apps.content.migration_tools import run_modes, sha
from apps.content.models import ContentBlock, Page

NAME = "yillik-hisobot-2026-45"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
LANGS = ("uz", "ru", "en")


def db_data(block):
    return {lang: {k: v for k, v in block.data[lang].items() if k not in ("image", "document")} for lang in LANGS}


def build(apply):
    rows = {"entries": []}
    skipped = []
    for entry in PLAN:
        page = Page.objects.filter(slug=entry["slug"]).first()
        block = page.blocks.filter(order=entry["order"]).first() if page else None
        data = db_data(block) if block else None
        if (block is None or block.block_type != "document" or (block.data.get("uz") or {}).get("document_id") != entry["document_id"]
                or any(sha(data[lang]) != entry["fp"][lang] for lang in LANGS)):
            skipped.append((entry["slug"], "not the document block of the plan (missing or edited since)"))
            continue
        print("%s: caption -> %s" % (entry["slug"], " | ".join(entry["caption"][lang] for lang in LANGS)))
        if not apply:
            continue
        old = json.loads(json.dumps(block.data))
        for lang in LANGS:
            block.data[lang]["caption"] = entry["caption"][lang]
        block.full_clean()
        block.save()
        rows["entries"].append({"pk": block.pk, "old": old, "fp": sha(block.data)})
    for slug, why in skipped:
        print("SKIPPED %s: %s" % (slug, why))
    print("\n%d change(s), %d skipped." % (len(PLAN) - len(skipped), len(skipped)))
    return rows


def undo(rows):
    restored = left = 0
    for entry in reversed(rows["entries"]):
        block = ContentBlock.objects.filter(pk=entry["pk"]).first()
        if block is None or sha(block.data) != entry["fp"]:
            left += 1
            print("left block %s: edited or removed since" % entry["pk"])
            continue
        block.data = entry["old"]
        block.save()
        restored += 1
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
