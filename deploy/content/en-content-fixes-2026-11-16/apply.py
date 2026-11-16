# English-version content fixes found by the 2026-11-16 audit. Only the ENGLISH text of a few pages (and one news title) is
# touched; the Uzbek and Russian text, files, links and layout stay exactly as they are.
#
#   1. Four short pages whose English text was a copy of the Uzbek/Russian original get a real English text:
#      institut-gazetasi-arxivi-2021, test-markazi-semestr-grafigi, kongress-2022-2024, taraqqiyot-strategiyasi.
#   2. Four official documents (a decree, a regulation, a classifier, a statistics report) are NOT machine-translated: their
#      English page keeps the original text and gets one clear note on top saying so (a wrong translation of an admission rule
#      could mislead an applicant): qabul-nizomi, prezident-farmon-va-qarorlari,
#      oliy-talim-yonalishlari-va-mutaxassisliklari-klassifikatori, fuqarolar-murojaatlari-statistikasi.
#   3. News id 1729: its Russian and English title had a Cyrillic "O" inside the Latin word "Onlayn".
#
# SAFE BY DESIGN
#   * dry (default) writes nothing and prints a before/after for every change.
#   * every replacement must find its text EXACTLY the expected number of times, otherwise the script stops before writing.
#   * apply first saves the old values to a backup file; a second apply is refused (the backup exists); the page is never
#     left half-changed (one database transaction).
#   * undo puts the old values back from that backup, byte for byte.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/en-content-fixes-2026-11-16/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/en-content-fixes-2026-11-16/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/en-content-fixes-2026-11-16/apply.py
import html as htmllib
import json
import os
import re
from datetime import datetime

from django.db import transaction

from apps.content.models import ContentBlock, Page
from apps.news.models import NewsPost

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "en-content-fixes-2026-11-16.json")

NOTE_RU = (
    "<p><em>This is an official document published in its original language (Russian). The Uzbek text is available on the "
    "Uzbek version of this page. No official English translation is available.</em></p>\n"
)
NOTE_UZ = (
    "<p><em>This is an official document published in its original language (Uzbek). "
    "No official English translation is available.</em></p>\n"
)

# slug -> list of (old text exactly as it is in the English HTML, new text, how many times it must occur)
TRANSLATIONS = {
    "institut-gazetasi-arxivi-2021": [
        ("Farg&lsquo;ona jamoat salomatligi tibbiyot institutining ijtimoiy-tibbiy gazetasi 28.09.2021",
         "Social and medical newspaper of the Fergana Medical Institute of Public Health, 28.09.2021", 1),
        ("Farg&lsquo;ona jamoat salomatligi tibbiyot institutining ijtimoiy-tibbiy gazetasi 29.10.2021",
         "Social and medical newspaper of the Fergana Medical Institute of Public Health, 29.10.2021", 1),
    ],
    "test-markazi-semestr-grafigi": [
        ("2024-2025 o&lsquo;quv yili Pediatriya fakulteti Yakuniy nazorat jadvali",
         "2024-2025 academic year, Faculty of Pediatrics: final assessment schedule", 1),
        ("2024-2025 o&lsquo;quv yili Pediatriya fakulteti Stomatologiya yo&lsquo;nalishi I va II kurslar uchun Yakuniy nazorat jadvali",
         "2024-2025 academic year, Faculty of Pediatrics: final assessment schedule for 1st and 2nd year students of the Dentistry programme", 1),
        ("2024-2025 o&lsquo;quv yili Pediatriya fakulteti Pediatriya yo&lsquo;nalishi I va II kurslar uchun Yakuniy nazorat jadvali",
         "2024-2025 academic year, Faculty of Pediatrics: final assessment schedule for 1st and 2nd year students of the Pediatrics programme", 1),
        ("2024-2025 o&lsquo;quv yili Pediatriya fakulteti Farmatsiya yo&lsquo;nalishi I va II kurslar uchun Yakuniy nazorat jadvali",
         "2024-2025 academic year, Faculty of Pediatrics: final assessment schedule for 1st and 2nd year students of the Pharmacy programme", 1),
        ("2024-2025 o&lsquo;quv yili Xalqaro fakultet&nbsp;&nbsp;Yakuniy nazorat jadvali",
         "2024-2025 academic year, International Faculty: final assessment schedule", 1),
    ],
    "kongress-2022-2024": [
        ("Нажмите, чтобы скачать", "Click to download ", 2),
        ("Инф_письмо_конференции_6 мая_2022г", "Conference information letter, 6 May 2022", 1),
        ("Прогорамма конференция", "Conference programme", 1),
    ],
    "taraqqiyot-strategiyasi": [
        ("<strong>O&lsquo;ZBEKISTON RESPUBLIKASI PREZIDENTINING</strong>", "<strong>DECREE</strong>", 1),
        ("<strong>FARMONI</strong>", "<strong>OF THE PRESIDENT OF THE REPUBLIC OF UZBEKISTAN</strong>", 1),
        ("2022 &mdash; 2026-YILLARGA MO&lsquo;LJALLANGAN YANGI O&lsquo;ZBEKISTONNING TARAQQIYOT STRATEGIYASI TO&lsquo;G&lsquo;RISIDA",
         "ON THE DEVELOPMENT STRATEGY OF NEW UZBEKISTAN FOR 2022&ndash;2026", 1),
        ("Yuklab olish uchun bosing &gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&nbsp;", "Click to download &gt;&gt;&gt;&gt;&gt;&gt;&gt;&gt;&nbsp;", 1),
        ("O&lsquo;zbekiston Respublikasi Prezidentining Farmoni, 28.01.2022 yildagi PF-60-son",
         "Decree of the President of the Republic of Uzbekistan No. PF-60 of 28.01.2022 (PDF, in Uzbek)", 1),
    ],
}
NOTES = {
    "qabul-nizomi": NOTE_RU,
    "prezident-farmon-va-qarorlari": NOTE_RU,
    "oliy-talim-yonalishlari-va-mutaxassisliklari-klassifikatori": NOTE_RU,
    "fuqarolar-murojaatlari-statistikasi": NOTE_UZ,
}
NEWS_TITLES = {  # id -> {field: (expected old value, new value)}
    1729: {"title_ru": ("Оnlayn konferensiya", "Онлайн-конференция"), "title_en": ("Оnlayn konferensiya", "Online conference")},
}


def show(text, limit=150):
    text = re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", text))).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


def en_block(slug):
    page = Page.objects.filter(slug=slug).first()
    if page is None:
        raise SystemExit("STOP: page '%s' not found. Nothing was changed." % slug)
    blocks = list(page.blocks.filter(block_type="raw_html").order_by("order"))
    if len(blocks) != 1:
        raise SystemExit("STOP: page '%s' has %d text (raw_html) blocks, expected exactly 1. Nothing was changed." % (slug, len(blocks)))
    block = blocks[0]
    return page, block, (block.data.get("en") or {}).get("html") or ""


print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    with transaction.atomic():
        for slug, saved in backup["pages"].items():
            block = ContentBlock.objects.get(pk=saved["block_id"])
            block.data["en"]["html"] = saved["en_html"]
            block.save(update_fields=["data"])
            block.page.save()
            print("restored English text of page:", slug)
        for pk, saved in backup["news"].items():
            post = NewsPost.objects.get(pk=int(pk))
            for field, value in saved.items():
                setattr(post, field, value)
            post.save(update_fields=list(saved))
            print("restored news %s: %s" % (pk, ", ".join("%s=%r" % kv for kv in saved.items())))
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: everything is back as it was. (the backup file was kept under a new name)")
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

# ---- plan everything first; nothing is written until every check has passed
plan_pages = {}   # slug -> (block, old_html, new_html, [(old, new)] shown to the user)
for slug, pairs in TRANSLATIONS.items():
    page, block, old_html = en_block(slug)
    new_html, shown = old_html, []
    for old, new, count in pairs:
        found = new_html.count(old)
        if found != count:
            raise SystemExit("STOP: in page '%s' the text %r occurs %d times, expected %d (already changed or edited?). Nothing was changed." % (slug, show(old, 60), found, count))
        new_html = new_html.replace(old, new)
        shown.append((old, new))
    plan_pages[slug] = (block, old_html, new_html, shown)
for slug, note in NOTES.items():
    page, block, old_html = en_block(slug)
    if old_html.lstrip().startswith(note.strip()[:60]):
        raise SystemExit("STOP: page '%s' already has the note. Nothing was changed." % slug)
    plan_pages[slug] = (block, old_html, note + old_html, [("(top of the page)", note)])
plan_news = {}
for pk, fields in NEWS_TITLES.items():
    post = NewsPost.objects.filter(pk=pk).first()
    if post is None:
        raise SystemExit("STOP: news %d not found. Nothing was changed." % pk)
    for field, (old, new) in fields.items():
        if getattr(post, field) != old:
            raise SystemExit("STOP: news %d %s is %r, expected %r. Nothing was changed." % (pk, field, getattr(post, field), old))
    plan_news[pk] = (post, fields)

# ---- show before / after
for slug, (block, old_html, new_html, shown) in plan_pages.items():
    kind = "note on top" if slug in NOTES else "English text"
    print("\n[page %s] %s (%d change%s)" % (slug, kind, len(shown), "" if len(shown) == 1 else "s"))
    for old, new in shown:
        print("   - %s" % show(old))
        print("   + %s" % show(new))
for pk, (post, fields) in plan_news.items():
    print("\n[news %d] %s" % (pk, post.title_uz))
    for field, (old, new) in fields.items():
        print("   %s: %r  ->  %r" % (field, old, new))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. %d pages and %d news title(s) would change. Run again with MODE=apply." % (len(plan_pages), len(plan_news)))
    raise SystemExit(0)

# ---- apply: back up first, then one transaction
os.makedirs(BACKUP_DIR, exist_ok=True)
backup = {
    "created": datetime.now().isoformat(),
    "pages": {slug: {"block_id": block.pk, "en_html": old_html} for slug, (block, old_html, _, _) in plan_pages.items()},
    "news": {str(pk): {field: getattr(post, field) for field in fields} for pk, (post, fields) in plan_news.items()},
}
json.dump(backup, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    for slug, (block, old_html, new_html, _) in plan_pages.items():
        block.data["en"]["html"] = new_html
        block.save(update_fields=["data"])
        block.page.save()
    for pk, (post, fields) in plan_news.items():
        for field, (old, new) in fields.items():
            setattr(post, field, new)
        post.save(update_fields=list(fields))
print("DONE: %d pages and %d news title(s) changed. To put everything back: MODE=undo with the same command." % (len(plan_pages), len(plan_news)))
print("(the site shows it within about 10 minutes at most)")
