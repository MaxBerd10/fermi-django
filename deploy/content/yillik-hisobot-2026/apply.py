# The site's figures brought in line with the institute's annual report 2026 (FJSTI_Yillik_hisobot_2026_yangi.pdf).
# Only the figures that the report states are changed; every other number, the layout, files and links stay as they are.
#
#   1. Site counter (home page hero "talabalar", band, /institut): students 6238 -> 7950, professor_teachers 275 -> 494,
#      book_fund 0 -> 17193 (not shown on the public pages yet).
#   2. Home page figure cards "Raqamlar" and "Nega bizni tanlashadi": 92% -> 91% (graduate employment), 20+ -> 305+ (clinical
#      partners), 15+ -> 38 (foreign partner universities), 275+ -> 494 (professors).
#   3. Page "Institut haqida" (uz, ru and en text): 274 -> 494 teaching staff with the report's breakdown (DSc 40, PhD 201,
#      others 253), 24 -> 29 departments, "more than 30" -> 38 foreign partner universities, the "main indicators" sentence
#      (7 950+ students, 10 programmes, 13 master's specialties, 32 doctoral, 45 residency), library fund 37 935 -> 1 810
#      titles / 17 193 copies.
#
# NOT changed here (decisions open): the number of faculties (the report says 5 and does not name the fifth), the 30 department
# records the home page counts by itself, "Tibbiy yo'nalishlar 50+" and "100%" on the home page (no matching figure in the report).
#
# SAFE BY DESIGN: dry (default) writes nothing and shows before/after for every change; every replacement must find its text
# EXACTLY the expected number of times (otherwise the script stops before writing anything); apply first saves the old values
# to a backup file (a second apply is refused) and writes everything in one transaction; undo puts the old values back from
# that backup, byte for byte.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026/apply.py
import json
import os
import re
from datetime import datetime

from django.db import transaction

from apps.content.models import ContentBlock, Page
from apps.site_settings.models import HomeItem, SiteCounter

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026.json")
SLUG = "institut-xaqida"
T = "ʻ"  # the site's apostrophe

COUNTER = {"students": (6238, 7950), "professor_teachers": (275, 494), "book_fund": (0, 17193)}

# (section, label field, label text, old value, new value)
HOME_ITEMS = [
    (HomeItem.FACT, "title_uz", "Bitiruvchilar bandligi", "92%", "91%"),
    (HomeItem.FACT, "title_uz", "Klinik hamkorlik", "20+", "305+"),
    (HomeItem.FACT, "title_uz", "Xalqaro hamkor", "15+", "38"),
    (HomeItem.WHY, "subtitle_uz", "Professorlar", "275+", "494"),
    (HomeItem.WHY, "subtitle_uz", "Klinik baza", "20+", "305+"),
    (HomeItem.WHY, "subtitle_uz", "Hamkorlar", "15+", "38"),
]


def divs(lines):
    wrap = '<div><span style="font-size:16px"><span style="font-family:verdana,geneva,sans-serif">%s</span></span></div>'
    return "\r\n\r\n".join(wrap % line for line in lines)


# the six <div> lines of the staff breakdown (first "Professor - 3" .. last "21"), replaced by the report's three lines
LIST_RE = {
    "uz": r"<div>(?:(?!</div>).)*?- Professor - 3 nafar.*?- Fan nomzodi &ndash; 21&nbsp;nafar</span></span></div>",
    "ru": r"<div>(?:(?!</div>).)*?Профессор - 3&nbsp;.*?Кандидат наук - 21&nbsp;</span></span></div>",
    "en": r"<div>(?:(?!</div>).)*?Professor - 3&nbsp;.*?Candidate of Sciences-21&nbsp;</span></span></div>",
}
LIST_NEW = {
    "uz": divs(["- Fan doktorlari (DSc) - 40 nafar", "- PhD, fan nomzodlari - 201 nafar", "- Boshqa professor-o%sqituvchilar - 253 nafar" % T]),
    "ru": divs(["Доктора наук (DSc) - 40&nbsp;", "PhD, кандидаты наук - 201&nbsp;", "Прочий профессорско-преподавательский состав - 253"]),
    "en": divs(["Doctors of Science (DSc) - 40&nbsp;", "PhD, candidates of sciences - 201&nbsp;", "Other teaching staff - 253"]),
}
# (old, new), each must occur exactly once in that language's HTML
TEXT = {
    "uz": [
        ("institutida 274&nbsp;nafar professor o%sqituvchilar faoliyat" % T, "institutida 494&nbsp;nafar professor-o%sqituvchilar faoliyat" % T),
        ("mavjud bo%slgan 24 ta kafedra" % T, "mavjud bo%slgan 29 ta kafedra" % T),
        ("dunyoning 30 dan ortiq oliy ta%slim muassasalari bilan" % T, "dunyoning 38 ta xorijiy oliy ta%slim muassasasi bilan" % T),
        (
            "2644 ta talaba 11 ta bakalavriat yo%snalishida va qo%sshma ta%slim dasturida, 23 ta magistratura mutaxassisligida va klinik ordinatura mutaxassisligida 184 nafar resident o%sqiydi." % (T, T, T, T),
            "jami 7950 dan ortiq talaba; 10 ta ta%slim yo%snalishi; 13 ta magistratura mutaxassisligi; 32 doktorantura; 45 ordinatura." % (T, T),
        ),
        ("uning fondi 37 935 dan ortiq bosma nashrni o%sz ichiga oladi" % T, "uning fondi 1810 nomdagi 17 193 nusxa nashrni o%sz ichiga oladi" % T),
    ],
    "ru": [
        ("работают 274 профессора, из них:", "работают 494 профессора-преподавателя, из них:"),
        ("функционируют 24 кафедры", "функционируют 29 кафедр"),
        ("более чем 30 высшими образовательными учреждениями мира", "38 зарубежными высшими образовательными учреждениями"),
        (
            "2644 студента обучаются по 11 направлениям бакалавриата и совместной образовательной программе, 184 - по 23 специальностям магистратуры и клинической ординатуры.",
            "всего более 7950 студентов; 10 направлений обучения; 13 специальностей магистратуры; докторантура - 32; ординатура - 45.",
        ),
        ("более 37 935 печатных изданий", "1810 наименований печатных изданий (17 193 экземпляра)"),
    ],
    "en": [
        ("employs 274 professors, of whom:", "employs 494 faculty members, of whom:"),
        ("there are 24 departments", "there are 29 departments"),
        ("more than 30 higher educational institutions in the world", "38 foreign higher educational institutions"),
        (
            "2644 students study in 11 areas of undergraduate studies and a joint educational program, while 184 students study in 23 specialties of master&#39;s and clinical residency.",
            "more than 7,950 students in total; 10 education programmes; 13 master&#39;s specialties; doctoral studies: 32; residency: 45.",
        ),
        ("includes more than 37,935 print media", "includes 17,193 copies of print media in 1,810 titles"),
    ],
}


def show(text, limit=170):
    text = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text)).strip()
    return text if len(text) <= limit else text[: limit - 1] + "…"


print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    with transaction.atomic():
        counter = SiteCounter.get_solo()
        for field, old in backup["counter"].items():
            setattr(counter, field, old)
        counter.save()
        for pk, old in backup["items"].items():
            item = HomeItem.objects.get(pk=int(pk))
            item.value = old
            item.save(update_fields=["value"])
        block = ContentBlock.objects.get(pk=backup["block_id"])
        for lang, old_html in backup["html"].items():
            block.data[lang]["html"] = old_html
        block.save(update_fields=["data"])
        block.page.save()
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: the counter, the home figures and the Institut haqida text are back as they were. (backup kept under a new name)")
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

# ---- plan everything first; nothing is written until every check has passed
counter = SiteCounter.get_solo()
plan_counter = {}
for field, (old, new) in COUNTER.items():
    if getattr(counter, field) != old:
        raise SystemExit("STOP: counter %s is %r, expected %r (already changed?). Nothing was changed." % (field, getattr(counter, field), old))
    plan_counter[field] = new

plan_items = []
for section, label_field, label, old, new in HOME_ITEMS:
    rows = list(HomeItem.objects.filter(section=section, value=old, **{label_field: label}))
    if len(rows) != 1:
        raise SystemExit("STOP: expected exactly one %s card '%s' with value %r, found %d. Nothing was changed." % (section, label, old, len(rows)))
    plan_items.append((rows[0], old, new, label))

page = Page.objects.filter(slug=SLUG).first()
if page is None:
    raise SystemExit("STOP: page '%s' not found. Nothing was changed." % SLUG)
blocks = list(page.blocks.filter(block_type="raw_html").order_by("order"))
if len(blocks) != 1:
    raise SystemExit("STOP: page '%s' has %d text (raw_html) blocks, expected exactly 1. Nothing was changed." % (SLUG, len(blocks)))
block = blocks[0]
old_html, new_html, shown = {}, {}, {}
for lang in ("uz", "ru", "en"):
    html = (block.data.get(lang) or {}).get("html") or ""
    if not html:
        raise SystemExit("STOP: the %s text of the page is empty. Nothing was changed." % lang)
    old_html[lang] = html
    pairs = []
    matches = re.findall(LIST_RE[lang], html, flags=re.S)
    if len(matches) != 1:
        raise SystemExit("STOP: [%s] the staff breakdown block occurs %d times, expected 1. Nothing was changed." % (lang, len(matches)))
    html = html.replace(matches[0], LIST_NEW[lang])
    pairs.append((matches[0], LIST_NEW[lang]))
    for old, new in TEXT[lang]:
        found = html.count(old)
        if found != 1:
            raise SystemExit("STOP: [%s] the text %r occurs %d times, expected 1 (already changed or edited?). Nothing was changed." % (lang, show(old, 70), found))
        html = html.replace(old, new)
        pairs.append((old, new))
    new_html[lang] = html
    shown[lang] = pairs

# ---- show before / after
print("\n[site counter]")
for field, (old, new) in COUNTER.items():
    print("   %s: %s  ->  %s" % (field, old, new))
print("\n[home page figure cards]")
for item, old, new, label in plan_items:
    print("   %s / %s: %s  ->  %s" % (item.section, label, old, new))
for lang in ("uz", "ru", "en"):
    print("\n[page %s, %s text] %d changes" % (SLUG, lang, len(shown[lang])))
    for old, new in shown[lang]:
        print("   - %s" % show(old))
        print("   + %s" % show(new))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

# ---- apply: back up first, then one transaction
os.makedirs(BACKUP_DIR, exist_ok=True)
backup = {
    "created": datetime.now().isoformat(),
    "counter": {field: old for field, (old, new) in COUNTER.items()},
    "items": {str(item.pk): old for item, old, new, label in plan_items},
    "block_id": block.pk,
    "html": old_html,
}
json.dump(backup, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    for field, new in plan_counter.items():
        setattr(counter, field, new)
    counter.save()
    for item, old, new, label in plan_items:
        item.value = new
        item.save(update_fields=["value"])
    for lang, html in new_html.items():
        block.data[lang]["html"] = html
    block.save(update_fields=["data"])
    page.save()
print("DONE: counter, %d home figure cards and the 3-language text of the page changed. To put everything back: MODE=undo with the same command." % len(plan_items))
print("(the site shows it within about 10 minutes at most)")
