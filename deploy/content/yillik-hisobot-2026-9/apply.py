# Three short sentences of the annual report (pages 38, 39 and 42) that were missing on the page "Ilmiy va innovatsion faoliyat":
#   1. new paragraph after the research-figures table (report p.38): participation in grants/programmes grows, young researchers,
#      intellectual property registration
#   2. the doctoral forecast (345 by 2028) now says what it is based on (report p.39)
#   3. the Gulf Medical University internship line now also names the experience gained: QAA, QS, THE, simulation centre (p.42)
# Uzbek text is from the report; Russian and English are my translations. Nothing else on the page changes.
#
# SAFE BY DESIGN: dry (default) writes nothing; apply saves the old data (and the new block) to a backup file (a second apply is
# refused) and writes in one transaction; undo removes the new paragraph and restores the two blocks (anything edited in the
# admin since apply is skipped and listed).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-9/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-9/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-9/apply.py
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.block_schemas import validate_block_data
from apps.content.models import ContentBlock, Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-9.json")
SLUG = "ilmiy-va-innovatsion-faoliyat"
U = chr(0x2BB)  # the Uzbek apostrophe of the site

NEW_PARAGRAPH = {
    "uz": {"text": "Xalqaro grantlar va mahalliy ilmiy dasturlardagi ishtirok kengaymoqda; yosh tadqiqotchilarni jalb etish va intellektual mulkni rasmiylashtirish sur@ati sezilarli o@sdi.".replace("@", U)},
    "ru": {"text": "Расширяется участие в международных грантах и местных научных программах; темпы привлечения молодых исследователей и оформления интеллектуальной собственности заметно выросли."},
    "en": {"text": "Participation in international grants and local research programmes is expanding; the pace of attracting young researchers and registering intellectual property has grown noticeably."},
}
# (block order now, language, old end of the text, new end of the text); for the list block the item index is given as well
FORECAST = {
    "uz": ("Prognoz: 2028-yilgacha 345 nafar.", "Prognoz: 2028-yilgacha 345 nafar; u ilmiy rahbarlik salohiyatini kengaytirish va yangi ixtisosliklar bo@yicha doktorantura o@rinlarini ochish rejalariga asoslangan.".replace("@", U)),
    "ru": ("Прогноз: до 345 человек к 2028 году.", "Прогноз: до 345 человек к 2028 году; он основан на планах расширения научно-руководящего потенциала и открытия мест докторантуры по новым специальностям."),
    "en": ("Forecast: 345 by 2028.", "Forecast: 345 by 2028, based on plans to expand supervisory capacity and open doctoral places in new specialities."),
}
GULF = {
    "uz": ("(2025-yil 19-noyabr — 5-dekabr)", "(2025-yil 19-noyabr — 5-dekabr); QAA, QS, THE va simulyatsiya markazi tajribasi"),
    "ru": ("(19 ноября — 5 декабря 2025 г.)", "(19 ноября — 5 декабря 2025 г.); опыт QAA, QS, THE и симуляционного центра"),
    "en": ("(19 November – 5 December 2025)", "(19 November – 5 December 2025); experience of QAA, QS, THE and the simulation centre"),
}
ANCHOR_TABLE_ORDER, ANCHOR_HEADING = 4, "Doktorantura va tayanch doktorantura"


def same(a, b):
    return json.dumps(a, sort_keys=True, ensure_ascii=False) == json.dumps(b, sort_keys=True, ensure_ascii=False)


print("MODE:", MODE)
page = Page.objects.filter(slug=SLUG).first()
if page is None:
    raise SystemExit("STOP: page %s not found." % SLUG)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    notes = []
    with transaction.atomic():
        new_block = ContentBlock.objects.filter(pk=backup["new_block"]["pk"]).first()
        if new_block is not None and same(new_block.data, backup["new_block"]["data"]):
            order = new_block.order
            new_block.delete()
            for b in page.blocks.filter(order__gt=order).order_by("order"):
                b.order -= 1
                b.save(update_fields=["order"])
        else:
            notes.append("the new paragraph was edited or removed: left as it is (and the other blocks keep their order)")
        for rec in backup["edited"]:
            b = ContentBlock.objects.filter(pk=rec["pk"]).first()
            if b is None or not same(b.data, rec["new"]):
                notes.append("block %s was edited since apply: skipped" % rec["pk"])
                continue
            b.data = rec["old"]
            b.save(update_fields=["data"])
        Page.objects.filter(pk=page.pk).update(updated_at=timezone.now())
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE. Notes:", notes or "none", "(backup kept under a new name)")
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

blocks = list(page.blocks.all())
by_order = {b.order: b for b in blocks}

# anchors: the research-figures table, then the heading of the doctoral section right after it
table, heading = by_order.get(ANCHOR_TABLE_ORDER), by_order.get(ANCHOR_TABLE_ORDER + 1)
if not (table and table.block_type == "table" and heading and heading.block_type == "heading" and heading.data["uz"]["text"] == ANCHOR_HEADING):
    raise SystemExit("STOP: the research-figures table / doctoral heading are not where expected. Nothing was changed.")

edited = []  # (block, old, new)


def find_one(predicate, what):
    found = [b for b in blocks if predicate(b)]
    if len(found) != 1:
        raise SystemExit("STOP: expected exactly one %s, found %d. Nothing was changed." % (what, len(found)))
    return found[0]


para = find_one(lambda b: b.block_type == "paragraph" and FORECAST["uz"][0] in b.data["uz"]["text"], "doctoral forecast paragraph")
new = json.loads(json.dumps(para.data))
for lang, (old_end, new_end) in FORECAST.items():
    t = new[lang]["text"]
    if t.count(old_end) != 1 or not t.endswith(old_end):
        raise SystemExit("STOP: [%s] the forecast sentence is not as expected (already changed or edited?). Nothing was changed." % lang)
    new[lang]["text"] = t[: -len(old_end)] + new_end
edited.append((para, para.data, new))

lst = find_one(lambda b: b.block_type == "list" and any(GULF["uz"][0] in i for i in b.data["uz"]["items"]), "internships list")
new = json.loads(json.dumps(lst.data))
for lang, (old_end, new_end) in GULF.items():
    items = new[lang]["items"]
    idx = [i for i, s in enumerate(items) if s.endswith(old_end) and "Gulf Medical" in s]
    if len(idx) != 1:
        raise SystemExit("STOP: [%s] the Gulf Medical University line is not as expected. Nothing was changed." % lang)
    items[idx[0]] = items[idx[0]][: -len(old_end)] + new_end
edited.append((lst, lst.data, new))

for b, old, nw in edited:
    validate_block_data(b.block_type, nw)
validate_block_data("paragraph", NEW_PARAGRAPH)

print("\n1. new paragraph after the figures table (becomes block #%d, later blocks move down by one):" % (ANCHOR_TABLE_ORDER + 1))
for lang in ("uz", "ru", "en"):
    print("   %s: %s" % (lang, NEW_PARAGRAPH[lang]["text"]))
print("\n2. forecast paragraph (block #%d):" % para.order)
for lang in ("uz", "ru", "en"):
    print("   %s: ...%s" % (lang, edited[0][2][lang]["text"][-170:]))
print("\n3. internships list (block #%d), the Gulf line:" % lst.order)
for lang in ("uz", "ru", "en"):
    print("   %s: %s" % (lang, [s for s in edited[1][2][lang]["items"] if "Gulf" in s][0]))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
with transaction.atomic():
    for b, old, nw in edited:
        b.data = nw
        b.save(update_fields=["data"])
    for b in sorted([x for x in blocks if x.order > ANCHOR_TABLE_ORDER], key=lambda x: -x.order):
        b.order += 1
        b.save(update_fields=["order"])
    created = ContentBlock.objects.create(page=page, order=ANCHOR_TABLE_ORDER + 1, block_type="paragraph", data=NEW_PARAGRAPH)
    Page.objects.filter(pk=page.pk).update(updated_at=timezone.now())
backup = {"created_at": datetime.now().isoformat(), "new_block": {"pk": created.pk, "data": NEW_PARAGRAPH},
          "edited": [{"pk": b.pk, "old": old, "new": nw} for b, old, nw in edited]}
json.dump(backup, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
print("DONE: 1 paragraph added, 2 blocks extended. To put everything back: MODE=undo with the same command.")
print("(the site shows it within about 10 minutes at most)")
