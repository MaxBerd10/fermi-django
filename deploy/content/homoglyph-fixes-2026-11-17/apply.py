# Mixed-script words in the Russian and English texts of the site (found by the 2026-11-16 audit): a Latin letter typed
# inside a Cyrillic word ("ИCТОРИЯ" with a Latin C, "Aпелляционная" with a Latin A, "ПAТOГEНEТИЧECКИE" ...) or a
# Cyrillic letter inside a Latin word ("Тechnical", "Оlympiad", "Сentre" with a Cyrillic Т, О, С). They look right to the
# eye, but the letters are different characters: searching, copying and a screen reader all break on them.
#
# WHAT IT FIXES, AND ONLY THAT
#   * a word whose letters come from BOTH alphabets, where every letter of the minority alphabet has an identical-looking
#     twin in the majority alphabet (A B C E H K M O P T X Y a c e o p x y): the twins are swapped for the majority's letter.
#     The majority is decided by letter count (a tie is never touched).
#   * a short list of words checked by hand (HAND), where the minority letters have no twin (Гуругram -> Гуруграм).
#   * everything else that mixes alphabets is only LISTED as "needs a human" and is not changed (typos, web addresses).
#   * tags, attributes, entities (&nbsp;), addresses and the Uzbek text are never touched; only the ru and en fields are read.
#
# SAFE BY DESIGN: dry (default) writes nothing and prints every word before/after plus the list left for a human; apply
# first saves the old values to a backup file (a second apply is refused), changes everything in one transaction;
# undo puts the old values back from that backup, byte for byte.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/homoglyph-fixes-2026-11-17/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/homoglyph-fixes-2026-11-17/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/homoglyph-fixes-2026-11-17/apply.py
import json
import os
import re
from datetime import datetime

from django.apps import apps
from django.db import models, transaction

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "homoglyph-fixes-2026-11-17.json")
LANGS = ("ru", "en")

LAT = re.compile("[A-Za-z]")
CYR = re.compile("[А-Яа-яЁё]")
WORD = re.compile("[A-Za-zА-Яа-яЁё]+")
# text outside tags and entities is the only thing that is read: split keeps <...> and &...; as separate pieces
PROTECTED = re.compile(r"(<[^>]*>|&#?\w+;)")

# identical-looking twins (Latin letter -> Cyrillic letter, and back)
LAT_TO_CYR = dict(zip("ABCEHKMOPTXYaceopxy", "АВСЕНКМОРТХУасеорху"))
CYR_TO_LAT = {c: l for l, c in LAT_TO_CYR.items()}
# words checked by hand whose minority letters have no twin
HAND = {"Гуругram": "Гуруграм", "Дosimов": "Досимов", "\u0412epartments": "Departments"}  # last one: a menu label, Cyrillic B + "epartments"
# mixed words that are typos on top of the mix: fixing only the letters would leave a wrong word, so a human decides
TYPOS = {"болеpнии", "Cасе", "данaных"}

# fields that identify something and are never text
SKIP_KEYS = {"slug", "style", "url", "src", "href", "file", "path", "document_id", "image_id", "id", "type", "icon", "color"}


def fix_word(word, context_cyrillic=None):
    """-> (new_word, reason). new_word is None when the word is mixed but must not be touched automatically.
    context_cyrillic: whether the text around the word is mostly Cyrillic; it decides a word with the same number of
    letters from both alphabets."""
    if word in HAND:
        return HAND[word], "checked by hand"
    if word in TYPOS:
        return None, "a typo as well as a mixed alphabet"
    lat = len(LAT.findall(word))
    cyr = len(CYR.findall(word))
    if not lat or not cyr:
        return word, ""
    if lat == cyr:  # a tie: the alphabet of the surrounding text decides
        if context_cyrillic is None:
            return None, "same number of letters from both alphabets"
        cyr, lat = (cyr + 1, lat) if context_cyrillic else (cyr, lat + 1)
    if cyr > lat:  # Cyrillic word with stray Latin letters
        if all(ch in LAT_TO_CYR for ch in LAT.findall(word)):
            return "".join(LAT_TO_CYR.get(ch, ch) for ch in word), "Latin look-alikes -> Cyrillic"
        return None, "a Latin letter without a Cyrillic twin"
    if all(ch in CYR_TO_LAT for ch in CYR.findall(word)):  # Latin word with stray Cyrillic letters
        return "".join(CYR_TO_LAT.get(ch, ch) for ch in word), "Cyrillic look-alikes -> Latin"
    return None, "a Cyrillic letter without a Latin twin"


def fix_text(text, found, skipped):
    """Fixes the words in the text outside tags/entities; records (old, new) in `found`, unfixable ones in `skipped`."""
    out = []
    for piece in PROTECTED.split(text):
        if not piece or PROTECTED.fullmatch(piece):
            out.append(piece)
            continue

        around_cyrillic = len(CYR.findall(piece)) > len(LAT.findall(piece))

        def sub(m):
            word = m.group(0)
            new, reason = fix_word(word, around_cyrillic)
            if new is None:
                skipped.append((word, reason, piece[max(0, m.start() - 20): m.end() + 20].replace("\n", " ")))
                return word
            if new != word:
                found.append((word, new))
            return new

        out.append(WORD.sub(sub, piece))
    return "".join(out)


def walk(value, path, found, skipped, changes):
    """Recurses through a JSON value; records (path, old, new) for every string that changes."""
    if isinstance(value, str):
        new = fix_text(value, found, skipped)
        if new != value:
            changes.append((path, value, new))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            walk(item, path + [i], found, skipped, changes)
    elif isinstance(value, dict):
        for k, v in value.items():
            if k not in SKIP_KEYS:
                walk(v, path + [k], found, skipped, changes)


def set_path(data, path, value):
    node = data
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value


def text_fields(model):
    return [
        f.name
        for f in model._meta.get_fields()
        if isinstance(f, (models.CharField, models.TextField)) and re.search(r"_(ru|en)$", f.name) and f.name not in SKIP_KEYS
    ]


print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    with transaction.atomic():
        for entry in backup["entries"]:
            model = apps.get_model(entry["model"])
            obj = model.objects.get(pk=entry["pk"])
            if entry["kind"] == "field":
                setattr(obj, entry["field"], entry["old"])
                obj.save(update_fields=[entry["field"]])
            else:
                set_path(obj.data, entry["path"], entry["old"])
                obj.save(update_fields=["data"])
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: %d value(s) are back as they were. (the backup file was kept under a new name)" % len(backup["entries"]))
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

plan = []  # (kind, model label, obj, field-or-path, old, new, label)
skipped = []
for model in apps.get_models():
    label = model._meta.label
    fields = text_fields(model)
    has_data = any(f.name == "data" and isinstance(f, models.JSONField) for f in model._meta.get_fields()) and label == "content.ContentBlock"
    if not fields and not has_data:
        continue
    for obj in model.objects.all().iterator():
        name = "%s #%s" % (label, obj.pk)
        for field in fields:
            old = getattr(obj, field) or ""
            found, sk, ch = [], [], []
            new = fix_text(old, found, sk)
            skipped += [(name + "." + field,) + s for s in sk]
            if new != old:
                plan.append(("field", label, obj, field, old, new, name + "." + field, found))
        if has_data:
            for lang in LANGS:
                payload = (obj.data or {}).get(lang)
                if payload is None:
                    continue
                found, sk, ch = [], [], []
                walk(payload, [], found, sk, ch)
                skipped += [("%s (page %s) [%s]" % (name, obj.page.slug, lang),) + s for s in sk]
                for path, old, new in ch:
                    plan.append(("data", label, obj, [lang] + path, old, new, "%s (page %s) [%s]" % (name, obj.page.slug, lang), found))

# ---- show
shown = set()
for kind, label, obj, where, old, new, name, found in plan:
    print("\n%s" % name)
    for a, b in found:
        print("   - %s   ->   %s" % (a, b))
    shown.add(name)
print("\n%d value(s) in %d place(s) would change; %d word(s) are fixed." % (len(plan), len(shown), sum(len(p[7]) for p in plan)))
if skipped:
    print("\nLEFT FOR A HUMAN (mixed alphabets but not a plain look-alike mix; NOT changed): %d" % len(skipped))
    for where, word, reason, context in skipped:
        print("   %s: %r  (%s)  ...%s..." % (where, word, reason, context))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
entries = []
for kind, label, obj, where, old, new, name, found in plan:
    if kind == "field":
        entries.append({"kind": "field", "model": label, "pk": obj.pk, "field": where, "old": old})
    else:
        entries.append({"kind": "data", "model": label, "pk": obj.pk, "path": where, "old": old})
json.dump({"created": datetime.now().isoformat(), "entries": entries}, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
with transaction.atomic():
    touched = {}
    for kind, label, obj, where, old, new, name, found in plan:
        if kind == "field":
            setattr(obj, where, new)
            touched.setdefault((label, obj.pk), (obj, set()))[1].add(where)
        else:
            set_path(obj.data, where, new)
            touched.setdefault((label, obj.pk), (obj, set()))[1].add("data")
    for (label, pk), (obj, fields) in touched.items():
        obj.save(update_fields=sorted(fields))
print("DONE: %d value(s) changed. To put everything back: MODE=undo with the same command." % len(plan))
print("(the site shows it within about 10 minutes at most)")
