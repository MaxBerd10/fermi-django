# Adds "Ochiq tanlovlar" (RU "Открытые конкурсы", EN "Open contests") as the FIRST entry under the "Tanlovlar" menu item,
# above "Tanlovlar arxivi". Until now that menu item opened a drop-down with only the archive in it: the page with the
# open contests (/news/0/tanlovlar, also what the home-page "Ochiq tanlovlar" shelf links to) had no entry of its own.
# Nothing else changes: the home-page shelf, the contest pages and the archive stay as they are; when a contest is closed
# it is moved to the archive in the admin panel as before.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry    .venv/bin/python manage.py shell < deploy/content/menu-ochiq-tanlovlar-2026-11-17/apply.py
#   MODE=apply  .venv/bin/python manage.py shell < deploy/content/menu-ochiq-tanlovlar-2026-11-17/apply.py
#   MODE=remove .venv/bin/python manage.py shell < deploy/content/menu-ochiq-tanlovlar-2026-11-17/apply.py   (deletes only this entry)
#
# dry (default) only shows; a second apply changes nothing.
import os

from apps.menu.models import MenuItem

MODE = os.environ.get("MODE", "dry")
URL = "/news/0/tanlovlar"
LABELS = {"uz": "Ochiq tanlovlar", "ru": "Открытые конкурсы", "en": "Open contests"}

print("MODE:", MODE)
parent = MenuItem.objects.filter(url=URL, parent__isnull=True).first()
if parent is None:
    raise SystemExit("STOP: the top-level menu item with url %s was not found. Nothing was modified." % URL)
children = list(parent.children.order_by("order", "id"))
print("Menu item '%s' (id %s) has now %d entr%s:" % (parent.label_uz, parent.pk, len(children), "y" if len(children) == 1 else "ies"))
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
    first = min([c.order for c in children], default=1)
    order = first - 1 if first > 0 else 0
    print("New entry goes first (order %s): %s / %s / %s  ->  %s" % (order, LABELS["uz"], LABELS["ru"], LABELS["en"], URL))
    if MODE == "apply":
        if order == first:  # no free slot before the first entry (it is at order 0): move the others down by one, keeping their order
            for c in reversed(children):
                c.order += 1
                c.save(update_fields=["order"])
        MenuItem.objects.create(parent=parent, label_uz=LABELS["uz"], label_ru=LABELS["ru"], label_en=LABELS["en"], url=URL, order=order)
        print("APPLIED. Undo: MODE=remove.")
    else:
        print("(dry run: nothing written. Use MODE=apply.)")
