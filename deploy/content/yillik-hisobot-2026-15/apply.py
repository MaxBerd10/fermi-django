# Small Cyrillic leftovers inside Latin-script Uzbek / English text. Every change is a plain letter-for-letter or word-for-word fix,
# the surrounding text is not touched:
#   "ОАК ruxsatnomasi" (Cyrillic letters)  -> "OAK ruxsatnomasi"      news-416, 391, 481, 322 (uz)
#   "ОК ruxsatnomasi"  (typo, the ru text says ОАК) -> "OAK ruxsatnomasi"   news-586, 552 (uz)
#   "Тип аккредитации:" -> "Accreditation type:"                       news-668 #10, #17 (en; the uz text says "Akkreditatsiya turi:")
#   "3,5 х 4,5 sm." (Cyrillic х) -> "3,5 x 4,5 sm."                    hujjat-turlari #3 (uz, ru, en), ordinaturaga-hujjat-topshirish-2025 #1 (uz, ru)
#   "куни соат" -> "kuni soat"; ", Узбекистан" -> ", Oʻzbekiston"      news-255 #2, #3, news-466 #3 (uz)
#   "мультимедия taqdimotlari" -> "multimedia taqdimotlari"            department-29 #60 (uz)
#   news-143 #2 (uz): "Батафсил маълумот учун - Диагностика маркази" -> "Batafsil maʻlumot uchun - Diagnostika markazi"  (Uzbek Cyrillic -> Latin)
#   news-155 #6, #7 (uz): "Модул телеграмм канал:" -> "Modul telegramm kanal:", "Ишонч телефонлари" -> "Ishonch telefonlari"  (Uzbek Cyrillic -> Latin)
# Not touched: the Russian titles of articles and theses inside Uzbek text, the Russian Zoom details of the conference news, and the
# Russian paragraphs of the admission news 237 and 326 (they need real translation).
#
# SAFE BY DESIGN: dry (default) writes nothing; every block is found by page slug + order and every old fragment must occur exactly once
# in the named language (anything else = STOP); apply saves the old data to a backup file (a second apply is refused) and writes in one
# transaction; undo puts the old data back, but only for a block that still holds exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-15/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-15/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-15/apply.py
import copy
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.models import ContentBlock, Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-15.json")

# (page slug, order, languages, old fragment, new fragment)  -- written with \u escapes on purpose
EDITS = [
    ("news-416", 4, ['uz'], "ОАК ruxsatnomasi", "OAK ruxsatnomasi"),
    ("news-391", 5, ['uz'], "ОАК ruxsatnomasi", "OAK ruxsatnomasi"),
    ("news-481", 2, ['uz'], "ОАК ruxsatnomasi", "OAK ruxsatnomasi"),
    ("news-322", 2, ['uz'], "ОАК ruxsatnomasi", "OAK ruxsatnomasi"),
    ("news-586", 4, ['uz'], "ОК ruxsatnomasi", "OAK ruxsatnomasi"),
    ("news-552", 4, ['uz'], "ОК ruxsatnomasi", "OAK ruxsatnomasi"),
    ("news-668", 10, ['en'], "Тип аккредитации:", "Accreditation type:"),
    ("news-668", 17, ['en'], "Тип аккредитации:", "Accreditation type:"),
    ("hujjat-turlari", 3, ['uz', 'ru', 'en'], "3,5 х 4,5 sm.", "3,5 x 4,5 sm."),
    ("ordinaturaga-hujjat-topshirish-2025", 1, ['uz', 'ru'], "3,5 х 4,5 sm.", "3,5 x 4,5 sm."),
    ("news-255", 2, ['uz'], "куни соат", "kuni soat"),
    ("news-255", 3, ['uz'], ", Узбекистан", ", Oʻzbekiston"),
    ("news-466", 3, ['uz'], ", Узбекистан", ", Oʻzbekiston"),
    ("department-29", 60, ['uz'], "мультимедия taqdimotlari", "multimedia taqdimotlari"),
    ("news-143", 2, ['uz'], "Батафсил маълумот учун - Диагностика маркази", "Batafsil maʻlumot uchun - Diagnostika markazi"),
    ("news-155", 6, ['uz'], "Модул телеграмм канал:", "Modul telegramm kanal:"),
    ("news-155", 7, ['uz'], "Ишонч телефонлари", "Ishonch telefonlari"),
]

print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    done = 0
    with transaction.atomic():
        for pk, row in backup["blocks"].items():
            block = ContentBlock.objects.get(pk=int(pk))
            if block.data == row["new"]:
                block.data = row["old"]
                block.save(update_fields=["data"])
                Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
                done += 1
            else:
                print("skipped block %s: it was edited after this script, left as it is" % pk)
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d blocks restored. (backup kept under a new name)" % done)
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)


def replace_in_payload(block_type, payload, old, new):
    """Replace old by new in the text of one language payload; return how many times old was found."""
    if block_type in ("paragraph", "heading"):
        n = payload["text"].count(old)
        payload["text"] = payload["text"].replace(old, new)
        return n
    if block_type == "table":
        n = 0
        for key in ("headers",):
            for i, cell in enumerate(payload[key]):
                n += cell.count(old)
                payload[key][i] = cell.replace(old, new)
        for r in payload["rows"]:
            for i, cell in enumerate(r):
                n += cell.count(old)
                r[i] = cell.replace(old, new)
        return n
    raise SystemExit("STOP: unexpected block type %s" % block_type)


plan = {}
count = 0
for slug, order, langs, old, new in EDITS:
    qs = ContentBlock.objects.filter(page__slug=slug, order=order)
    if qs.count() != 1:
        raise SystemExit("STOP: expected exactly one block %s#%s, found %d." % (slug, order, qs.count()))
    block = qs.get()
    row = plan.setdefault(block.pk, {"page": slug, "order": order, "old": copy.deepcopy(block.data), "new": copy.deepcopy(block.data)})
    for lang in langs:
        found = replace_in_payload(block.block_type, row["new"][lang], old, new)
        if found != 1:
            raise SystemExit("STOP: block %s#%s (%s): expected exactly one %r, found %d (already fixed or edited in the admin?)." % (slug, order, lang, old, found))
        count += 1
        print("%s #%s [%s]  %s  ->  %s" % (slug, order, lang, old, new))

print("\n%d edits in %d blocks." % (count, len(plan)))
if MODE == "dry":
    print("DRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
json.dump({"created_at": datetime.now().isoformat(), "blocks": {str(pk): r for pk, r in plan.items()}}, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("backup saved:", BACKUP_FILE)
with transaction.atomic():
    for pk, r in plan.items():
        block = ContentBlock.objects.get(pk=pk)
        block.data = r["new"]
        block.save(update_fields=["data"])
        Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
print("DONE: %d edits in %d blocks. To put everything back: MODE=undo with the same command." % (count, len(plan)))
print("(the site shows it within about 10 minutes at most)")
