# Department pages: in 149 image blocks the Russian (97) or English (99) image is a DIFFERENT picture than the Uzbek one of the same block
# (the old site's ru/en pages had a different block order; the import put them side by side by position, so e.g. department-42 #31 shows
# Isakov in uz but Botirov in ru/en, next to the text of the Uzbek person). In these blocks the ru/en image is replaced by a COPY of the
# Uzbek image payload (same picture as uz, which matches the Uzbek text). Pairs whose files are byte-identical (31) are not touched.
# The list of blocks is in plan.json (same folder): page slug, block order, language and the image ids that are expected right now.
# Nothing is deleted from the site: image files stay where they are and the old image choice is saved in the backup.
#
# SAFE BY DESIGN: dry (default) writes nothing; a block is changed only if its page/order exists, is an image block and the current uz and
# ru/en image ids are still the ones in plan.json (a block edited in the admin since is SKIPPED and listed); apply saves the old payload of
# every changed language to a backup file (a second apply is refused) and writes in one transaction; undo puts the old payload back, but
# only where the block still holds exactly the copy this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-17/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-17/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-17/apply.py
import copy
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-17.json")
PLAN_FILE = os.environ.get("PLAN_FILE", "deploy/content/yillik-hisobot-2026-17/plan.json")
EXPECTED = 196

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
    print("UNDONE: %d images restored, %d skipped. (backup kept under a new name)" % (done, skipped))
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
    if block.block_type != "image":
        skipped.append((slug, order, lang, "not an image block"))
        continue
    if block.data["uz"].get("image_id") != item["id_uz"] or block.data[lang].get("image_id") != item["id_lang"]:
        skipped.append((slug, order, lang, "image changed since the check"))
        continue
    if not Image.objects.filter(pk=item["id_uz"]).exists():
        skipped.append((slug, order, lang, "uz image %s does not exist" % item["id_uz"]))
        continue
    row = changes.setdefault(block.pk, {"page": slug, "order": order, "langs": {}})
    row["langs"][lang] = {"old": copy.deepcopy(block.data[lang]), "new": copy.deepcopy(block.data["uz"])}

pairs = sum(len(r["langs"]) for r in changes.values())
names = {i.pk: i.file.name.rsplit("/", 1)[-1] for i in Image.objects.filter(pk__in={x["id_uz"] for x in plan} | {x["id_lang"] for x in plan})}
for pk, r in sorted(changes.items(), key=lambda kv: (kv[1]["page"], kv[1]["order"])):
    for lang, item in r["langs"].items():
        print("%s #%s [%s]  NOW: %s  ->  AFTER (uz copy): %s" % (r["page"], r["order"], lang, names.get(item["old"].get("image_id")), names.get(item["new"].get("image_id"))))
print("\n%d images in %d blocks would be replaced by the Uzbek image; %d skipped." % (pairs, len(changes), len(skipped)))
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
print("DONE: %d images in %d blocks. To put everything back: MODE=undo with the same command." % (pairs, len(changes)))
print("(the site shows it within about 10 minutes at most)")
