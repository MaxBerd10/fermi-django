# 17-goals-of-un-policies: three of the policy documents (Reducing Inequalities, Protection of the Seas and Aquatic Spaces, Sustainable Production and Consumption) were
# never loaded as documents when the page was migrated: they stand between the fourteen document cards as plain link lines with the English title. Each line becomes a
# document card like the other fourteen (style "attachment": the buttons "Brauzerda ochish" / "Yuklab olish"). The file is ALREADY in the media folder
# (migrated/img/17 GOALS/...pdf), but its name is longer than a Document file name may be (100 characters), so the Document row gets a COPY of it with a short name under
# uploads/documents/<year>/<month>/ (as every other document of the site); the old file stays where it is. The card captions: uz and ru are translations of the English
# title of the PDF, en is that title itself (proposed to and accepted by the user). RUN AFTER scripts 39-90.
#
# SAFE BY DESIGN: dry (default) writes nothing; a line is changed only if it still is exactly the line of plan.json AND the file is in the media folder, otherwise it is
# SKIPPED and the apply is cancelled as a whole; apply is one transaction with a backup (a second apply is refused); undo puts the old lines back, only where the new card is
# still what this script wrote, and removes the Document rows it made (the copied files stay in uploads/documents: harmless, a few hundred KB).
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-91/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-91/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-91/apply.py
import json
import os

from django.conf import settings

from apps.content.migration_tools import fingerprint_ok, make_document, replace_blocks, run_modes, sha
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document

NAME = "yillik-hisobot-2026-91"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))
LANGS = ("uz", "ru", "en")


def build(apply):
    rows = {"entries": []}
    skipped = []
    for entry in PLAN:
        page = Page.objects.filter(slug=entry["slug"]).first()
        block = page.blocks.filter(order=entry["order"]).first() if page else None
        if block is None or block.block_type != "paragraph" or not fingerprint_ok(block, entry["fp"]):
            skipped.append((entry["slug"], entry["order"], "the line is not the one of the plan (missing or edited since)"))
            continue
        if not os.path.isfile(os.path.join(str(settings.MEDIA_ROOT), entry["media_path"])):
            skipped.append((entry["slug"], entry["order"], "the file %s is not in the media folder" % entry["media_path"]))
            continue
        print("%s #%d: link line -> document card %r" % (entry["slug"], entry["order"], entry["captions"]["uz"]))
        if not apply:
            continue
        old = {"block_type": block.block_type, "data": block.data}
        document = make_document(os.path.join(str(settings.MEDIA_ROOT), entry["media_path"]), title=entry["captions"]["uz"])
        created = True
        data = {lang: {"style": "attachment", "caption": entry["captions"][lang], "document_id": document.pk} for lang in LANGS}
        (pk,) = replace_blocks(page, entry["order"], 1, [{"block_type": "document", "data": data}])
        rows["entries"].append({"slug": entry["slug"], "order": entry["order"], "old": old, "new_pk": pk, "new_fp": sha(ContentBlock.objects.get(pk=pk).data),
                                "document_pk": document.pk, "document_created": created})
    for slug, order, why in skipped:
        print("SKIPPED %s #%d: %s" % (slug, order, why))
    print("\n%d change(s), %d skipped." % (len(PLAN) - len(skipped), len(skipped)))
    if apply and skipped:
        raise SystemExit("STOP: some lines were skipped, nothing was written (the transaction is cancelled).")
    return rows


def undo(rows):
    restored = left = 0
    for entry in reversed(rows["entries"]):
        block = ContentBlock.objects.filter(pk=entry["new_pk"]).first()
        if block is None or sha(block.data) != entry["new_fp"]:
            left += 1
            print("left %s #%d: the card was edited or removed since" % (entry["slug"], entry["order"]))
            continue
        replace_blocks(Page.objects.get(slug=entry["slug"]), entry["order"], 1, [entry["old"]])
        if entry["document_created"]:
            Document.objects.filter(pk=entry["document_pk"]).delete()  # the row only: deleting a row does not delete the file
        restored += 1
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
