# Adds "So'x modeli" (RU "Модель «Сох»", EN "So'x model") as the LAST entry in the drop-down of "FJSTI Ilmiy jurnali"
# (Institut -> FJSTI Ilmiy jurnali), after "JCPM-2025 arxiv". It opens the site page /sox-modeli (the institute's 2026
# report on the So'x district: a short introduction and the PDF). Nothing else in the menu changes.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/menu-sox-modeli-2026-11-18/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/menu-sox-modeli-2026-11-18/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/menu-sox-modeli-2026-11-18/apply.py   (deletes only this entry)
#
# dry (default) only shows; a second apply changes nothing.
import os

from apps.menu.models import MenuItem

MODE = os.environ.get("MODE", "dry")
URL = "/sox-modeli"
PARENT_LABEL = "FJSTI Ilmiy jurnali"
LABELS = {"uz": "Soʻx modeli", "ru": "Модель «Сох»", "en": "Soʻx model"}

print("MODE:", MODE)
candidates = list(MenuItem.objects.filter(label_uz__iexact=PARENT_LABEL, parent__isnull=False))
if len(candidates) != 1:
    raise SystemExit("STOP: expected exactly one menu item '%s', found %d. Nothing was modified." % (PARENT_LABEL, len(candidates)))
parent = candidates[0]
print("Parent: '%s' (id %s) under '%s'" % (parent.label_uz, parent.pk, parent.parent.label_uz if parent.parent else "-"))
children = list(parent.children.order_by("order", "id"))
print("It has now %d entr%s:" % (len(children), "y" if len(children) == 1 else "ies"))
for c in children:
    print("   order %s  id %s  %s  ->  %s" % (c.order, c.pk, c.label_uz, c.url))
mine = [c for c in children if c.url == URL]

if MODE == "remove":
    if not mine:
        raise SystemExit("Nothing to remove: the entry is not there.")
    for c in mine:
        c.delete()
    print("REMOVED %d entry (the rest of the menu was not touched)." % len(mine))
else:
    if mine:
        raise SystemExit("STOP: the entry '%s' is already there. Nothing was modified." % mine[0].label_uz)
    order = max([c.order for c in children], default=-1) + 1
    print("New entry goes last (order %s): %s / %s / %s  ->  %s" % (order, LABELS["uz"], LABELS["ru"], LABELS["en"], URL))
    if MODE == "apply":
        MenuItem.objects.create(parent=parent, label_uz=LABELS["uz"], label_ru=LABELS["ru"], label_en=LABELS["en"], url=URL, order=order)
        print("APPLIED. Undo: MODE=remove.")
    else:
        print("(dry run: nothing written. Use MODE=apply.)")
