# meyoriy-hujjatlar: Resolution of the Cabinet of Ministers of the Republic of Uzbekistan No. 769 of 27 September 2017 "On measures to further
# improve the training of medical personnel" with Annexes 1, 2, 2a, 2b, 2v (the Regulation on sending graduates to mandatory work
# placement and the structure of curricula). The Uzbek text of the page is the one on the site; the Russian and English text of the page was
# broken: about 70 blocks were still in Uzbek, and many Russian/English blocks held the text of another block (the old-site import shifted
# them), the tables were in Uzbek.
#   RUSSIAN  = the OFFICIAL text of the resolution on lex.uz (https://lex.uz/ru/docs/3367367), put block by block against the Uzbek blocks
#              (the Uzbek and Russian lex.uz paragraphs follow the same order; checked: every block has the same numbers as the Uzbek block,
#              except 3 months/"three months" and the places listed in the notes below).
#   ENGLISH  = lex.uz has NO official English text (its "Eng" tab is only the interface), so the English text is a HAND TRANSLATION of the
#              official Russian text - NOT official. Terms follow the rest of the site (General Medicine, Pediatrics, mandatory work placement).
# Hand-made (not copied from lex.uz) Russian: block #72 (lex.uz has only "Unofficial translation, see the Uzbek text" there; the note is made
# like the other notes of the page), #140 (list of the legislation-database numbers), #108/#109 (the Uzbek banner is cut in two blocks, the
# Russian banner is cut at the same place: "ANNEX 2b" / "to the Resolution..."), the titles #88, #100, #110, #119 ("Учебные планы ...", the
# lex.uz wording "учебных планов ..." belongs to the word "СТРУКТУРА" which in Uzbek stands in the next block), and the pair #20/#21 (in
# Uzbek "...to'g'risida" + "nizom", in Russian "Положение" + "о порядке ...").
# Typos seen in the Uzbek text (NOT changed here, only reported): block #4 "26" should be "2b"; block #38 "(20-band" should be "(6-band";
# block #96 "510900" should be "5510900". The Russian and English text use the right values.
# The new text is in plan.json (field "set"; for the 4 tables "headers"/"rows"), next to a fingerprint (sha256) of the current uz and
# target-language payload.
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if it exists, is a heading/paragraph/table and the current uz and
# target-language payload still have the fingerprints from plan.json (a block edited in the admin since is SKIPPED and listed);
# apply saves the old payload to a backup file (a second apply is refused) and writes in one transaction; undo puts the old payload
# back, but only where the block still holds exactly what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-30/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-30/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-30/apply.py
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
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-30.json")
PLAN_FILE = os.environ.get("PLAN_FILE", "deploy/content/yillik-hisobot-2026-30/plan.json")
EXPECTED = 208


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
