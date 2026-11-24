# Pages for applicants: "hujjat-turlari" (documents for the 2025/2026 clinical residency admission) and the grant distribution pages
# "grantlar-taqsimoti" (bachelor, 2nd and 3rd year) and "grant-taqsimoti" (master). 28 texts:
#   hujjat-turlari  the Russian and English text was Uzbek (with a wrong apostrophe) or belonged to another line: the list of documents (table),
#                   its headings, the sentences about file names, the platform address, the confirmation letter and the contact line are
#                   translated; Russian #1 still held the deadline of 2021 ("до 10 сентября 2021 года") instead of the heading of this
#                   announcement (the phone numbers it also held are in block #9)
#   grantlar-taqsimoti, grant-taqsimoti  headings #1/#3 and the note #6 were left in Uzbek in ru/en -> translated; the English tables of
#                   grantlar-taqsimoti get the standard programme names ("Medical practice" -> "General Medicine", "Pediatric work" ->
#                   "Pediatrics", "Medical and preventive work" -> "Medical Prevention") and, in block #4, the same header as block #2
#                   instead of a repeated header row with the typo "Russia n"
# No number is changed: every number of the tables is the one of the Uzbek table of the same block (checked when the plan was made).
# The new payloads are in plan.json (field "set"), next to a fingerprint (sha256) of the current uz and target-language payload.
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if it exists, is a heading/paragraph/table and the current uz and
# target-language payload still have the fingerprints from plan.json (a block edited in the admin since is SKIPPED and listed);
# apply saves the old payload to a backup file (a second apply is refused) and writes in one transaction; undo puts the old payload
# back, but only where the block still holds exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-26/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-26/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-26/apply.py
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
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-26.json")
PLAN_FILE = os.environ.get("PLAN_FILE", "deploy/content/yillik-hisobot-2026-26/plan.json")
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
            if "text" in p:
                return p["text"][:100]
            return "table: " + " | ".join(h[:30] for h in p["headers"][:3]) + " || " + " / ".join(" ".join(c[:25] for c in row[:4]) for row in p["rows"][:2]) + " ..."
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
