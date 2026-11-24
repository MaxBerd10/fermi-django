# News 237 and 326 (admission announcements for foreign citizens, 2022 and 2023): the UZBEK field of 9 blocks holds the Russian text of the
# announcement, so the Uzbek page showed Russian. Here the Uzbek field gets a real Uzbek translation (written by hand, with the single
# apostrophe U+02BB; the Russian and English fields already hold the Russian original and its English translation and stay as they are).
# One more fix in the same pages: news-326 #2 English held the translation of block #5 (document submission online); it now says what
# the Uzbek/Russian text of #2 says (admission for foreign citizens to the master's programme in 2023/2024).
# Links, e-mail addresses, phone numbers and bot names inside the texts are copied unchanged.
# The new text is in plan.json (field "text"), next to a fingerprint (sha256) of the current uz and target-language payload of the block.
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if it exists, is a heading/paragraph and the current uz and target
# payload still have the fingerprints from plan.json (a block edited in the admin since is SKIPPED and listed); only the "text" of that
# language changes; apply saves the old payload to a backup file (a second apply is refused) and writes in one transaction; undo puts the
# old payload back, but only where the block still holds exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-21/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-21/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-21/apply.py
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
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-21.json")
PLAN_FILE = os.environ.get("PLAN_FILE", "deploy/content/yillik-hisobot-2026-21/plan.json")
EXPECTED = 10


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
    if block.block_type not in ("heading", "paragraph"):
        skipped.append((slug, order, lang, "not a heading/paragraph"))
        continue
    if sha(block.data["uz"]) != item["sha_uz"] or sha(block.data[lang]) != item["sha_lang"]:
        skipped.append((slug, order, lang, "text changed since the check"))
        continue
    new_payload = copy.deepcopy(block.data[lang])
    new_payload["text"] = item["text"]
    row = changes.setdefault(block.pk, {"page": slug, "order": order, "langs": {}})
    row["langs"][lang] = {"old": copy.deepcopy(block.data[lang]), "new": new_payload}

pairs = sum(len(r["langs"]) for r in changes.values())
for pk, r in sorted(changes.items(), key=lambda kv: (kv[1]["page"], kv[1]["order"])):
    for lang, item in r["langs"].items():
        print("%s #%s [%s]\n   NOW  : %s\n   AFTER: %s" % (r["page"], r["order"], lang, item["old"]["text"][:90], item["new"]["text"][:90]))
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
