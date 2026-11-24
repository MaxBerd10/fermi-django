# Old news (news-215, news-446, news-325, news-330, news-178): the Russian and/or English text of 28 blocks belongs to ANOTHER line of the
# same list than the Uzbek text, or is a garbled machine translation:
#   news-215  admission quotas: Russian lines "очная / заочная / вечерняя форма" and the Russian chain #11-#17 are shifted by one block
#             (e.g. the Uzbek "kunduzgi ... 77 477" is shown as "заочная ... 26 095"); English #6, #8 hold other lines
#   news-446 and news-325 (documents for the rector's scholarship): "Maʻlumotnoma - obyektivka" was translated as "Референс - это линза" /
#             "Reference is a lens"; English items #8, #9, #11 hold items 9, 10, 11 of the list next to Uzbek items 4, 5, 7; Russian #9 repeats item 4
#   news-446 #18  the English text repeated another paragraph instead of the list of nominations
#   news-330  English documents list #4, #5 held items of another list (passport, medical certificate) instead of application and diploma
#   news-178  Russian #3 held the translation of the last list item (500 women...) instead of the maternity-benefit sentence; English #6 held
#             the translation of the 2,100 contracts line instead of the master's-contracts line
# Each of the 28 texts is the translation of the Uzbek text of the SAME block (numbers and names copied from the Uzbek text; where the
# correct translation already existed one block away, its wording is reused).
# The new text is in plan.json (field "set"), next to a fingerprint (sha256) of the current uz and target-language payload.
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if it exists, is a heading/paragraph/table and the current uz and
# target-language payload still have the fingerprints from plan.json (a block edited in the admin since is SKIPPED and listed);
# apply saves the old payload to a backup file (a second apply is refused) and writes in one transaction; undo puts the old payload
# back, but only where the block still holds exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-25/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-25/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-25/apply.py
import copy
import hashlib
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.models import ContentBlock, Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-25.json")
PLAN_FILE = os.environ.get("PLAN_FILE", "deploy/content/yillik-hisobot-2026-25/plan.json")
EXPECTED = 28


def sha(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False).encode("utf8")).hexdigest()


print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    done = skipped = 0
    with transaction.atomic():
        for pk, row in backup["blocks"].items():
            block = ContentBlock.objects.get(pk=int(pk))
            changed = False
            for lang, item in row["langs"].items():
                if block.data.get(lang) == item["new"]:
                    block.data[lang] = item["old"]
                    changed = True
                    done += 1
                else:
                    skipped += 1
                    print("skipped %s #%s [%s]: edited after this script, left as it is" % (row["page"], row["order"], lang))
            if changed:
                block.save(update_fields=["data"])
                Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d texts restored, %d skipped. (backup kept under a new name)" % (done, skipped))
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

plan = json.load(open(PLAN_FILE, encoding="utf8"))
if len(plan) != EXPECTED:
    raise SystemExit("STOP: plan.json has %d entries, expected %d." % (len(plan), EXPECTED))

changes = {}  # block pk -> {page, order, langs: {lang: {old, new}}}
skipped = []
for item in plan:
    slug, order, lang = item["slug"], item["order"], item["lang"]
    qs = ContentBlock.objects.filter(page__slug=slug, order=order)
    if qs.count() != 1:
        skipped.append((slug, order, lang, "block not found"))
        continue
    block = qs.get()
    if block.block_type not in ("heading", "paragraph", "table"):
        skipped.append((slug, order, lang, "not a heading/paragraph/table"))
        continue
    if sha(block.data["uz"]) != item["sha_uz"] or sha(block.data[lang]) != item["sha_lang"]:
        skipped.append((slug, order, lang, "text changed since the check"))
        continue
    new_payload = copy.deepcopy(block.data[lang])
    new_payload.update(copy.deepcopy(item["set"]))
    row = changes.setdefault(block.pk, {"page": slug, "order": order, "langs": {}})
    row["langs"][lang] = {"old": copy.deepcopy(block.data[lang]), "new": new_payload}

pairs = sum(len(r["langs"]) for r in changes.values())
for pk, r in sorted(changes.items(), key=lambda kv: (kv[1]["page"], kv[1]["order"])):
    for lang, item in r["langs"].items():
        def show(p):
            return (p["text"][:100] if "text" in p else "table: " + " | ".join(p["headers"]) + " || " + " / ".join(row[1] + " " + row[2] + " " + row[3] for row in p["rows"][:2]) + " ...")
        print("%s #%s [%s]\n   NOW  : %s\n   AFTER: %s" % (r["page"], r["order"], lang, show(item["old"]), show(item["new"])))
print("\n%d texts in %d blocks would get the new translation; %d skipped." % (pairs, len(changes), len(skipped)))
for s in skipped:
    print("SKIPPED %s #%s [%s]: %s" % s)

if MODE == "dry":
    print("DRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

if pairs == 0:
    raise SystemExit("STOP: nothing to change.")
os.makedirs(BACKUP_DIR, exist_ok=True)
json.dump({"created_at": datetime.now().isoformat(), "blocks": {str(pk): r for pk, r in changes.items()}}, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("backup saved:", BACKUP_FILE)
with transaction.atomic():
    for pk, r in changes.items():
        block = ContentBlock.objects.get(pk=pk)
        for lang, item in r["langs"].items():
            block.data[lang] = item["new"]
        block.save(update_fields=["data"])
        Page.objects.filter(pk=block.page_id).update(updated_at=timezone.now())
print("DONE: %d texts in %d blocks. To put everything back: MODE=undo with the same command." % (pairs, len(changes)))
print("(the site shows it within about 10 minutes at most)")
