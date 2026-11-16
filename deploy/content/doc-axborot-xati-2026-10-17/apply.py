# Publishes the information letter of the international scientific-practical conference "The role of healthy nutrition
# in public health" (held 17 October 2026) on the page "Xalqaro konferensiyalar" (menu: Institut konferensiyalari ->
# Xalqaro konferensiyalar) as ONE document card at the end of the page. The original PDF has the letter in three
# languages (pages 1-2 Uzbek, 3-4 Russian, 5-6 English); it is cut into three PDFs and each language version of the
# page shows its own PDF (the card holds a different document per language, one caption per language).
# The letter is dated: the conference (17.10.2026) and the abstract deadline (15.10.2026) are in the past, so the card
# is an archive record and the caption carries the conference date.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/doc-axborot-xati-2026-10-17/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/doc-axborot-xati-2026-10-17/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/doc-axborot-xati-2026-10-17/apply.py   (deletes what apply made)
#
# dry (default) only shows; apply stops if the card is already there, so a second run changes nothing.
import os
import shutil

from django.conf import settings
from django.db import transaction

from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document

MODE = os.environ.get("MODE", "dry")
PAGE_SLUG = "ilmiy-konferensiyalar"
SRC_DIR = os.path.join(settings.BASE_DIR, "deploy", "content", "doc-axborot-xati-2026-10-17")
SUBDIR = "uploads/documents/2026/11"
LANGS = ("uz", "ru", "en")
FILES = {lang: "axborot-xati-2026-10-17-%s.pdf" % lang for lang in LANGS}
CAPTIONS = {
    "uz": "Axborot xati: «Sogʻlom ovqatlanishning aholi salomatligidagi oʻrni» xalqaro ilmiy-amaliy konferensiyasi, 2026-yil 17-oktabr (PDF)",
    "ru": "Информационное письмо: международная научно-практическая конференция «Роль здорового питания в здоровье населения», 17 октября 2026 года (PDF)",
    "en": "Information letter: international scientific and practical conference “The Role of Healthy Nutrition in Population Health”, 17 October 2026 (PDF)",
}


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
stored = {lang: "%s/%s" % (SUBDIR, FILES[lang]) for lang in LANGS}
documents = list(Document.objects.filter(file__in=list(stored.values())))
ids = {d.id for d in documents}
blocks = [b for b in ContentBlock.objects.filter(page=page, block_type="document") if ids & {b.data[lang].get("document_id") for lang in LANGS}]

if MODE == "remove":
    if not documents and not blocks:
        raise SystemExit("Nothing to remove: the card is not there.")
    with transaction.atomic():
        for block in blocks:
            block.delete()
        for document in documents:
            document.delete()
    for lang in LANGS:
        path = os.path.join(settings.MEDIA_ROOT, stored[lang])
        if os.path.isfile(path):
            os.remove(path)
    print("REMOVED %d card(s), %d document row(s) and the files (the rest of the page was not touched)." % (len(blocks), len(documents)))
else:
    missing = [n for n in FILES.values() if not os.path.isfile(os.path.join(SRC_DIR, n))]
    if missing:
        raise SystemExit("STOP: files missing (git pull first?): %s. Nothing was modified." % ", ".join(missing))
    if documents or blocks:
        raise SystemExit("STOP: the letter is already on the page. Nothing was modified.")
    last = ContentBlock.objects.filter(page=page).order_by("-order").values_list("order", flat=True).first() or 0
    print("Page '%s' (id %s) has %d block(s); one card goes to the end (order %d):" % (page.slug, page.id, ContentBlock.objects.filter(page=page).count(), last + 1))
    for lang in LANGS:
        print("  %s: %s  (%d KB)\n      %s" % (lang, stored[lang], os.path.getsize(os.path.join(SRC_DIR, FILES[lang])) // 1024, CAPTIONS[lang]))
    if MODE == "apply":
        os.makedirs(os.path.join(settings.MEDIA_ROOT, SUBDIR), exist_ok=True)
        written = []
        try:
            with transaction.atomic():
                doc_id = {}
                for lang in LANGS:
                    dest = os.path.join(settings.MEDIA_ROOT, stored[lang])
                    shutil.copyfile(os.path.join(SRC_DIR, FILES[lang]), dest)
                    written.append(dest)
                    document = Document(file=stored[lang], title="")
                    document.save()
                    doc_id[lang] = document.id
                block = ContentBlock(
                    page=page,
                    order=last + 1,
                    block_type="document",
                    data={lang: {"style": "card", "document_id": doc_id[lang], "caption": CAPTIONS[lang]} for lang in LANGS},
                )
                block.full_clean()
                block.save()
        except Exception:
            for path in written:
                if os.path.isfile(path):
                    os.remove(path)
            raise
        hand_to_www_data(written)
        print("APPLIED: 1 card (3 language PDFs) added. Undo: MODE=remove.")
    else:
        print("(dry run: nothing written. Use MODE=apply.)")
