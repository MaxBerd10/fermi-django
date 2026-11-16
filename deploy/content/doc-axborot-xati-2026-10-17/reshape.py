# Follow-up to apply.py: the first version put ONE card on the "Xalqaro konferensiyalar" page that showed each site
# language its own PDF. This turns it into THREE separate cards, always visible, in the order Russian - English -
# Uzbek, each captioned with its language (the same on every language version of the page). The three PDFs and their
# Document rows stay as they are; only the card block(s) change.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/doc-axborot-xati-2026-10-17/reshape.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/doc-axborot-xati-2026-10-17/reshape.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/doc-axborot-xati-2026-10-17/reshape.py   (back to the single card)
#
# (MODE=remove of apply.py still deletes whichever cards exist, one or three, together with the PDFs.)
import os

from django.db import transaction

from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Document

MODE = os.environ.get("MODE", "dry")
PAGE_SLUG = "ilmiy-konferensiyalar"
SUBDIR = "uploads/documents/2026/11"
LANGS = ("uz", "ru", "en")
FILES = {lang: "%s/axborot-xati-2026-10-17-%s.pdf" % (SUBDIR, lang) for lang in LANGS}
ORDER = ("ru", "en", "uz")  # the order of the three cards
CARD_CAPTION = {
    "uz": "Oʻzbekcha — Axborot xati: «Sogʻlom ovqatlanishning aholi salomatligidagi oʻrni» xalqaro ilmiy-amaliy konferensiyasi, 2026-yil 17-oktabr (PDF)",
    "ru": "Русский — Информационное письмо: международная научно-практическая конференция «Роль здорового питания в здоровье населения», 17 октября 2026 года (PDF)",
    "en": "English — Information letter: international scientific and practical conference “The Role of Healthy Nutrition in Population Health”, 17 October 2026 (PDF)",
}
# the single card of the first version (for undo)
OLD_CAPTION = {
    "uz": "Axborot xati: «Sogʻlom ovqatlanishning aholi salomatligidagi oʻrni» xalqaro ilmiy-amaliy konferensiyasi, 2026-yil 17-oktabr (PDF)",
    "ru": "Информационное письмо: международная научно-практическая конференция «Роль здорового питания в здоровье населения», 17 октября 2026 года (PDF)",
    "en": "Information letter: international scientific and practical conference “The Role of Healthy Nutrition in Population Health”, 17 October 2026 (PDF)",
}

print("MODE:", MODE)
page = Page.objects.filter(slug=PAGE_SLUG).first()
if page is None:
    raise SystemExit("STOP: page '%s' not found. Nothing was modified." % PAGE_SLUG)
doc = {lang: Document.objects.filter(file=FILES[lang]).first() for lang in LANGS}
if not all(doc.values()):
    raise SystemExit("STOP: the three PDFs are not on the site yet (run apply.py first). Nothing was modified.")
ids = {d.id: lang for lang, d in doc.items()}
mine = [b for b in ContentBlock.objects.filter(page=page, block_type="document").order_by("order") if set(b.data[l].get("document_id") for l in LANGS) & set(ids)]
single = [b for b in mine if len({b.data[l]["document_id"] for l in LANGS}) > 1]  # one card, a different PDF per language
three = [b for b in mine if len({b.data[l]["document_id"] for l in LANGS}) == 1]  # a card showing one PDF in every language
print("cards of the letter now: %d single (per-language) / %d separate" % (len(single), len(three)))


def card(order, data):
    block = ContentBlock(page=page, order=order, block_type="document", data=data)
    block.full_clean()
    block.save()


if MODE == "undo":
    if len(three) != 3 or single:
        raise SystemExit("STOP: expected the three separate cards, found %d (and %d single). Nothing was modified." % (len(three), len(single)))
    first = min(b.order for b in three)
    with transaction.atomic():
        for b in three:
            b.delete()
        card(first, {lang: {"style": "card", "document_id": doc[lang].id, "caption": OLD_CAPTION[lang]} for lang in LANGS})
    print("UNDONE: back to one card (order %d) that shows each language its own PDF." % first)
else:
    if len(single) != 1 or three:
        raise SystemExit("STOP: expected exactly one single card and no separate ones, found %d and %d. Nothing was modified." % (len(single), len(three)))
    first = single[0].order
    following = list(ContentBlock.objects.filter(page=page, order__gt=first).order_by("-order"))
    print("The card at order %d becomes 3 cards at orders %d, %d, %d (%d block(s) after it move down by 2):" % (first, first, first + 1, first + 2, len(following)))
    for i, lang in enumerate(ORDER):
        print("  order %d: %s\n      %s" % (first + i, FILES[lang], CARD_CAPTION[lang]))
    if MODE == "apply":
        with transaction.atomic():
            for b in following:  # make room (highest first: the order is unique per page)
                b.order += 2
                b.save(update_fields=["order"])
            single[0].delete()
            for i, lang in enumerate(ORDER):
                card(first + i, {l: {"style": "card", "document_id": doc[lang].id, "caption": CARD_CAPTION[lang]} for l in LANGS})
        print("APPLIED. Undo: MODE=undo.")
    else:
        print("(dry run: nothing written. Use MODE=apply.)")
