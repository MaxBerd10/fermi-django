# Text fixes on the page "kongress-2022-2024" (menu: Kongress -> Kongress dasturi), found by the 2026-11-16 audit. Only the
# captions of the two download links are touched; the files, links, pictures and videos stay exactly as they are.
#
#   * Uzbek: the page showed Russian captions ("Нажмите, чтобы скачать", "Инф_письмо_конференции_6 мая_2022г",
#     "Прогорамма конференция"). They become Uzbek and say which language the files are in: the information letter is Russian,
#     the programme (22 pages) is Uzbek in Cyrillic script.
#   * Russian: the typo "Прогорамма конференция" -> "Программа конференции".
#   * English: "Conference programme" gets "(in Uzbek, Cyrillic script)".
#
# SAFE BY DESIGN: dry (default) writes nothing and shows before/after; every replacement must find its text exactly the
# expected number of times, otherwise the script stops before writing; apply saves the old texts to a backup file first
# (a second apply is refused) and changes everything in one transaction; undo puts the old texts back byte for byte.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/kongress-text-fixes-2026-11-16/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/kongress-text-fixes-2026-11-16/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/kongress-text-fixes-2026-11-16/apply.py
import html as htmllib
import json
import os
import re
from datetime import datetime

from django.db import transaction

from apps.content.models import Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "kongress-text-fixes-2026-11-16.json")
SLUG = "kongress-2022-2024"

# language -> list of (old text exactly as it is in that language's HTML, new text, how many times it must occur)
EDITS = {
    "uz": [
        ("Нажмите, чтобы скачать", "Yuklab olish uchun bosing ", 2),
        ("Инф_письмо_конференции_6 мая_2022г", "Konferensiya axborot xati, 2022-yil 6-may (rus tilida)", 1),
        ("Прогорамма конференция", "Konferensiya dasturi, 2022-yil 6-may (kirill alifbosida)", 1),
    ],
    "ru": [
        ("Прогорамма конференция", "Программа конференции", 1),
    ],
    "en": [
        ("Conference programme", "Conference programme (in Uzbek, Cyrillic script)", 1),
    ],
}


def show(text, limit=150):
    text = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", text))).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


page = Page.objects.filter(slug=SLUG).first()
if page is None:
    raise SystemExit("STOP: page '%s' not found. Nothing was changed." % SLUG)
blocks = list(page.blocks.filter(block_type="raw_html").order_by("order"))
if len(blocks) != 1:
    raise SystemExit("STOP: the page has %d text (raw_html) blocks, expected exactly 1. Nothing was changed." % len(blocks))
block = blocks[0]
print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    with transaction.atomic():
        for lang, old_html in backup["html"].items():
            block.data[lang]["html"] = old_html
        block.save(update_fields=["data"])
        page.save()
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: the three language texts are back as they were. (the backup file was kept under a new name)")
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

old_all, new_all = {}, {}
for lang, pairs in EDITS.items():
    old_html = (block.data.get(lang) or {}).get("html") or ""
    new_html = old_html
    print("\n[%s]" % lang)
    for old, new, count in pairs:
        found = new_html.count(old)
        if found != count:
            raise SystemExit("STOP: [%s] the text %r occurs %d times, expected %d (already changed or edited?). Nothing was changed." % (lang, show(old, 60), found, count))
        new_html = new_html.replace(old, new)
        print("   - %s  (x%d)\n   + %s" % (show(old), count, show(new)))
    old_all[lang], new_all[lang] = old_html, new_html

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
json.dump({"created": datetime.now().isoformat(), "block_id": block.pk, "html": old_all}, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    for lang, new_html in new_all.items():
        block.data[lang]["html"] = new_html
    block.save(update_fields=["data"])
    page.save()
print("DONE. To put everything back: MODE=undo with the same command.")
print("(the site shows it within about 10 minutes at most)")
