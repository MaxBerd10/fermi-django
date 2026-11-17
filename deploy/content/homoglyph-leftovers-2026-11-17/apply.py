# The 5 places the homoglyph fixes (homoglyph-fixes-2026-11-17) left for a human: a mixed alphabet AND a typo / a web
# address, so each is corrected by hand here, checked against the other language versions of the same text:
#   * "болеpнии"   -> "болезни"            (page klinik-fikrlashga-doir-video-darslar; the English text says "Infectious Disease")
#   * "данaных"    -> "данных"             (page kam-taminlangan-talabalar-uchun-yaratilgan-imkoniyatlar; a stray Latin a)
#   * "кабинетаpm2.gov.uz", "кабинетpm2.gov.uz" -> "cabinetpm2.gov.uz"
#                                          (page fuqarolar-murojaatlari-statistikasi; the same page writes the address this way
#                                           a third time, and the domain exists)
#   * "Cасе-студй" -> "кейс-стади"         (news tashrif-2, the Uzbek-Cyrillic paragraph; the Russian paragraph of the same
#                                           news says "кейс-стади")
# Only the Russian text of those blocks changes, only those words. Same safety as the other scripts: dry (default) shows
# before/after and writes nothing; every replacement must find its text exactly once, otherwise the script stops before
# writing; apply saves a backup first (a second apply is refused) and is one transaction; undo restores byte for byte.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/homoglyph-leftovers-2026-11-17/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/homoglyph-leftovers-2026-11-17/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/homoglyph-leftovers-2026-11-17/apply.py
import json
import os
import re
from datetime import datetime

from django.db import transaction

from apps.content.models import ContentBlock, Page
from apps.news.models import NewsPost

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "homoglyph-leftovers-2026-11-17.json")

# (where, slug, field of the ru payload, old text (escaped so no look-alike can be mistyped), new text)
EDITS = [
    ("page", "klinik-fikrlashga-doir-video-darslar", "html", "болеpнии", "болезни"),
    ("page", "kam-taminlangan-talabalar-uchun-yaratilgan-imkoniyatlar", "html", "данaных", "данных"),
    ("page", "fuqarolar-murojaatlari-statistikasi", "html", "кабинетаpm2.gov.uz", "cabinetpm2.gov.uz"),
    ("page", "fuqarolar-murojaatlari-statistikasi", "html", "кабинетpm2.gov.uz", "cabinetpm2.gov.uz"),
    ("news", "tashrif-2", "text", "Cасе-студй", "кейс-стади"),
]


def context(text, index, length, width=40):
    """The text around the `length` characters at `index`, with the tags taken out."""
    before = re.sub(r"<[^>]+>", " ", text[max(0, index - 200): index])[-width:]
    after = re.sub(r"<[^>]+>", " ", text[index + length: index + length + 200])[:width]
    middle = re.sub(r"<[^>]+>", " ", text[index: index + length])
    return re.sub(r"\s+", " ", before + middle + after).strip()


def find_block(where, slug, field, old):
    page = Page.objects.filter(slug=slug).first() if where == "page" else getattr(NewsPost.objects.filter(slug=slug).first(), "page", None)
    if page is None:
        raise SystemExit("STOP: %s '%s' not found. Nothing was changed." % (where, slug))
    hits = [b for b in page.blocks.all() if isinstance((b.data.get("ru") or {}).get(field), str) and old in b.data["ru"][field]]
    if len(hits) != 1:
        raise SystemExit("STOP: %s '%s': the text %r is in %d block(s), expected exactly 1 (already fixed or edited?). Nothing was changed." % (where, slug, old, len(hits)))
    return page, hits[0]


print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    with transaction.atomic():
        for entry in backup["blocks"]:
            block = ContentBlock.objects.get(pk=entry["block_id"])
            block.data["ru"][entry["field"]] = entry["old"]
            block.save(update_fields=["data"])
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d block(s) are back as they were. (the backup file was kept under a new name)" % len(backup["blocks"]))
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

# plan everything first (several edits may fall into the same block: apply them one after another on the same text)
work = {}  # (block_id, field) -> [block, old_text, new_text]
for where, slug, field, old, new in EDITS:
    page, block = find_block(where, slug, field, old)
    entry = work.setdefault((block.pk, field), [block, block.data["ru"][field], block.data["ru"][field]])
    if entry[2].count(old) != 1:
        raise SystemExit("STOP: %s '%s': the text %r occurs %d times, expected 1. Nothing was changed." % (where, slug, old, entry[2].count(old)))
    print("\n[%s %s] block #%s" % (where, slug, block.pk))
    at = entry[2].find(old)
    print("   - ...%s..." % context(entry[2], at, len(old)))
    entry[2] = entry[2][:at] + new + entry[2][at + len(old):]
    print("   + ...%s..." % context(entry[2], at, len(new)))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. %d edit(s) in %d block(s) would be made. Run again with MODE=apply." % (len(EDITS), len(work)))
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
json.dump(
    {"created": datetime.now().isoformat(), "blocks": [{"block_id": b.pk, "field": f, "old": old} for (_, f), (b, old, _) in work.items()]},
    open(BACKUP_FILE, "w", encoding="utf8"),
    ensure_ascii=False,
)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    for (_, field), (block, old, new) in work.items():
        block.data["ru"][field] = new
        block.save(update_fields=["data"])
print("DONE: %d edit(s) in %d block(s). To put everything back: MODE=undo with the same command." % (len(EDITS), len(work)))
print("(the site shows it within about 10 minutes at most)")
