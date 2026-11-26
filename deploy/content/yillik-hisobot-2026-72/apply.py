# One typo of the menu: the Russian label of "Tibbiy taʻlimga tadqiq etilgan ilmiy tadqiqot ishlari" (menu item 1998) says "Нучно-исследовательские" instead of
# "Научно-исследовательские". The frontend had been patching it on screen (pages/blog/page.tsx); the data is fixed here and the patch removed.
#
# SAFE BY DESIGN: dry (default) writes nothing; the label is changed only if it still is exactly the old text (edited in the admin since -> SKIPPED); apply is one
# transaction with a backup (a second apply is refused); undo puts the old text back, only if the label still is the new text.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-72/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-72/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-72/apply.py
from apps.content.migration_tools import run_modes
from apps.menu.models import MenuItem

NAME = "yillik-hisobot-2026-72"
ITEM_ID = 1998
OLD = "Нучно-исследовательские работы в медицинском образовании "
NEW = "Научно-исследовательские работы в медицинском образовании "


def build(apply):
    item = MenuItem.objects.filter(pk=ITEM_ID).first()
    if item is None or item.label_ru != OLD:
        print("SKIPPED menu item %d: its Russian label is not the one of the plan (missing or edited since)" % ITEM_ID)
        return {"changed": False}
    print("menu item %d: %r -> %r" % (ITEM_ID, item.label_ru[:30], NEW[:30]))
    if apply:
        MenuItem.objects.filter(pk=ITEM_ID).update(label_ru=NEW)
    return {"changed": True}


def undo(rows):
    if not rows.get("changed"):
        print("nothing was changed by the apply")
        return
    done = MenuItem.objects.filter(pk=ITEM_ID, label_ru=NEW).update(label_ru=OLD)
    print("restored %d, left %d." % (done, 1 - done))


run_modes(NAME, build, undo)
