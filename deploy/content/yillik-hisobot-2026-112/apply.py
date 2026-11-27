# One menu label: the English label of 'Kam taʻminlangan talabalar uchun yaratilgan imkoniyatlar' (menu item 2022) was the Uzbek text (Claude's wording, to be read by the staff).
# RUN AFTER scripts 39-111.
#
# SAFE BY DESIGN: dry (default) writes nothing; a field is changed only if it still holds EXACTLY the old text plan.json was made from, otherwise the whole apply is cancelled (nothing is
# written); apply is one transaction with a backup (a second apply is refused); undo puts the old texts back, only where the field still holds what this script wrote.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-112/apply.py
#   MODE=apply sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-112/apply.py
#   MODE=undo  sudo -E -u www-data .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-112/apply.py
import json
import os

from django.apps import apps

from apps.content.migration_tools import run_modes

NAME = "yillik-hisobot-2026-112"
PLAN = json.load(open(os.environ.get("PLAN_FILE", f"deploy/content/{NAME}/plan.json"), encoding="utf8"))


def row_of(op):
    return apps.get_model(op["model"]).objects.filter(pk=op["pk"]).first()


def build(apply):
    skipped = []
    done = []
    for op in PLAN:
        obj = row_of(op)
        if obj is None:
            skipped.append((op, "the row does not exist"))
            continue
        current = getattr(obj, op["field"])
        if current != op["old"]:
            skipped.append((op, "it holds %r, not the old text of the plan (edited since?)" % current[:60]))
            continue
        print("%-34s #%-3s %-16s %r -> %r" % (op["model"], op["pk"], op["field"], op["old"][:34], op["new"][:44]))
        if apply:
            setattr(obj, op["field"], op["new"])
            obj.save(update_fields=[op["field"]])
            done.append(op)
    for op, why in skipped:
        print("SKIPPED %s #%s %s: %s" % (op["model"], op["pk"], op["field"], why))
    print("\n%d change(s), %d skipped." % (len(PLAN) - len(skipped), len(skipped)))
    if apply and skipped:
        raise SystemExit("STOP: some fields were skipped, nothing was written (the transaction is cancelled).")
    return {"ops": done}


def undo(rows):
    restored = left = 0
    for op in reversed(rows["ops"]):
        obj = row_of(op)
        if obj is None or getattr(obj, op["field"]) != op["new"]:
            left += 1
            print("left %s #%s %s: edited or removed since" % (op["model"], op["pk"], op["field"]))
            continue
        setattr(obj, op["field"], op["old"])
        obj.save(update_fields=[op["field"]])
        restored += 1
    print("restored %d, left %d." % (restored, left))


run_modes(NAME, build, undo)
