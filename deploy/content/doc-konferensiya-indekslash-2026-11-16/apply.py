# Publishes the guide "Konferensiya jurnali va ilmiy to'plamlarini xalqaro bazalarda indekslash" on the page "Jurnal xaqida"
# (menu: FJSTI Ilmiy jurnali -> Jurnal xaqida) as two document cards at the end of the page:
#   1. the PDF copy (open in the browser + download), made from the .docx by make_pdf.py (same colours and tables)
#   2. the original Word file (download, editable)
# Nothing else on the page is touched. The cards are shared by the three languages; the guide is in Uzbek, which the
# Russian / English captions say.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/doc-konferensiya-indekslash-2026-11-16/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/doc-konferensiya-indekslash-2026-11-16/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/doc-konferensiya-indekslash-2026-11-16/apply.py   (deletes what apply made)
#
# dry (default) only shows; apply stops if the cards are already there, so a second run changes nothing.
import os
import shutil

from django.conf import settings
from django.db import transaction

from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document

MODE = os.environ.get("MODE", "dry")
PAGE_SLUG = "jurnal-xaqida"
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "doc-konferensiya-indekslash-2026-11-16")
SUBDIR = "uploads/documents/2026/11"
PDF = "konferensiya-jurnalini-indekslash-qollanma.pdf"
DOCX = "konferensiya-jurnalini-indekslash-qollanma.docx"
CAPTIONS = {
    PDF: {
        "uz": "Konferensiya jurnali va ilmiy toʻplamlarini xalqaro bazalarda indekslash boʻyicha qoʻllanma (PDF)",
        "ru": "Руководство по индексации журнала конференции и научных сборников в международных базах (PDF, на узбекском языке)",
        "en": "Guide to indexing a conference journal and collections of papers in international databases (PDF, in Uzbek)",
    },
    DOCX: {
        "uz": "Konferensiya jurnali va ilmiy toʻplamlarini xalqaro bazalarda indekslash boʻyicha qoʻllanma (Word)",
        "ru": "Руководство по индексации журнала конференции и научных сборников в международных базах (Word, на узбекском языке)",
        "en": "Guide to indexing a conference journal and collections of papers in international databases (Word, in Uzbek)",
    },
}
ORDER = [PDF, DOCX]


def hand_to_www_data(paths):
    if os.geteuid() != 0:  # the site runs as www-data; never leave root-owned media behind
        return
    import grp
    import pwd

    uid, gid = pwd.getpwnam("www-data").pw_uid, grp.getgrnam("www-data").gr_gid
    for path in paths:
        os.chown(path, uid, gid)


print("MODE:", MODE)
page = Page.objects.filter(slug=PAGE_SLUG).first()
if page is None:
    raise SystemExit("STOP: page '%s' not found. Nothing was modified." % PAGE_SLUG)
stored = {name: "%s/%s" % (SUBDIR, name) for name in ORDER}
documents = list(Document.objects.filter(file__in=list(stored.values())))
blocks = [b for b in ContentBlock.objects.filter(page=page, block_type="document") if b.data["uz"].get("document_id") in {d.id for d in documents}]

if MODE == "remove":
    if not documents and not blocks:
        raise SystemExit("Nothing to remove: the cards are not there.")
    with transaction.atomic():
        for block in blocks:
            block.delete()
        for document in documents:
            document.delete()
    for name in ORDER:
        path = os.path.join(settings.MEDIA_ROOT, stored[name])
        if os.path.isfile(path):
            os.remove(path)
    print("REMOVED %d card(s), %d document row(s) and the files (the rest of the page was not touched)." % (len(blocks), len(documents)))
else:
    missing = [n for n in ORDER if not os.path.isfile(os.path.join(SRC_DIR, n))]
    if missing:
        raise SystemExit("STOP: files missing (git pull first?): %s. Nothing was modified." % ", ".join(missing))
    if documents or blocks:
        raise SystemExit("STOP: the guide is already on the page (%d card(s)). Nothing was modified." % len(blocks))
    last = ContentBlock.objects.filter(page=page).order_by("-order").values_list("order", flat=True).first() or 0
    print("Page '%s' (id %s) has %d block(s); the cards go to the end:" % (page.slug, page.id, ContentBlock.objects.filter(page=page).count()))
    for i, name in enumerate(ORDER, 1):
        print("  block order %d: %s  (%d KB)\n    uz: %s" % (last + i, stored[name], os.path.getsize(os.path.join(SRC_DIR, name)) // 1024, CAPTIONS[name]["uz"]))
    if MODE == "apply":
        os.makedirs(os.path.join(settings.MEDIA_ROOT, SUBDIR), exist_ok=True)
        written = []
        try:
            with transaction.atomic():
                for i, name in enumerate(ORDER, 1):
                    dest = os.path.join(settings.MEDIA_ROOT, stored[name])
                    shutil.copyfile(os.path.join(SRC_DIR, name), dest)
                    written.append(dest)
                    document = Document(file=stored[name], title="")
                    document.save()
                    block = ContentBlock(
                        page=page,
                        order=last + i,
                        block_type="document",
                        data={lang: {"style": "card", "document_id": document.id, "caption": CAPTIONS[name][lang]} for lang in ("uz", "ru", "en")},
                    )
                    block.full_clean()
                    block.save()
        except Exception:
            for path in written:
                if os.path.isfile(path):
                    os.remove(path)
            raise
        hand_to_www_data(written)
        print("APPLIED: 2 cards added. Undo: MODE=remove.")
    else:
        print("(dry run: nothing written. Use MODE=apply.)")
