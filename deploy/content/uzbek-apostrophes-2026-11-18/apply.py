# One apostrophe for the whole Uzbek text of the site.
#
# Uzbek Latin writes oʻ gʻ (and the hamza in taʼlim, maʼlumot) with ONE mark. The site's own convention is ʻ
# (U+02BB, "okina"): the pages already rewrite every other mark to it when they SHOW a menu label or a CMS text (see
# frontend/src/lib/normalizeCmsText.ts), but the database keeps whatever was typed or pasted: ' ‘ ’ ʼ ` ´ side by side
# (the live menu alone had 58 x ‘, 36 x `, 27 x ', 14 x ’, 4 x ʻ). So search, the admin panel, exports and everything that
# does not go through that rewrite still see the mixture. This script writes the one mark into the database itself.
#
# WHAT IT CHANGES, AND ONLY THAT
#   * in the UZBEK fields only (every *_uz field of every model, and the "uz" side of the page blocks): a mark that stands
#     BETWEEN TWO LETTERS ("ko'rish", "Hay‘ati", "ta’lim", "Farg`ona", "bo&#39;lim") becomes ʻ.
#   * a word written in capitals (TO'G'RI, O'ZBEKISTON) is converted too.
#   * NOT touched: tags and their attributes, web addresses, marks that are not between two letters (quotation marks,
#     a closing ' after a letter), the English possessive / contractions inside Uzbek text (Cushing's, don't), mixed-case
#     names (O'Brien). What looks like one of these is only LISTED ("left for a human").
#   * the Russian and English fields are never read.
#
# SAFE BY DESIGN: dry (default) writes nothing and prints every word before/after; apply first saves the old values to a
# backup file (a second apply is refused) and changes everything in one transaction; undo puts the old values back from
# that backup, byte for byte.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/uzbek-apostrophes-2026-11-18/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/uzbek-apostrophes-2026-11-18/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/uzbek-apostrophes-2026-11-18/apply.py
import json
import os
import re
from collections import Counter
from datetime import datetime

from django.apps import apps
from django.db import models, transaction

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "uzbek-apostrophes-2026-11-18.json")
TARGET = "ʻ"  # ʻ

LETTER = r"[^\W\d_]"
# every way a mark is written: the characters, and the HTML entities of the straight / curly ones
MARK = r"(?:['‘’ʼ`´ʻ]|&#0*39;|&#x0*27;|&apos;|&lsquo;|&rsquo;|&#0*821[67];)"
TOKEN = re.compile(r"%s+(?:%s%s+)+" % (LETTER, MARK, LETTER))
SPLIT_MARK = re.compile("(%s)" % MARK)
TAG = re.compile(r"(<[^>]*>)")
URL_BEFORE = re.compile(r"(https?://|www\.)\S*$")
# English endings that follow a straight apostrophe: Cushing's, don't, we're, I've, we'll, I'd, I'm
ENGLISH_END = {"s", "t", "re", "ve", "ll", "d", "m"}
# fields that identify something and are never text
SKIP_KEYS = {"slug", "style", "url", "src", "href", "file", "path", "document_id", "image_id", "id", "type", "icon", "color"}


def fix_token(token, left):
    """token: letters and marks, with at least one mark between two letters. Returns the new token; every mark that was
    deliberately kept appears in `left` as (token, reason)."""
    parts = SPLIT_MARK.split(token)  # [word, mark, word, mark, word ...]
    letters = "".join(parts[0::2])
    caps = len(letters) >= 2 and letters.isupper()
    for i in range(1, len(parts), 2):
        mark, before, after = parts[i], parts[i - 1], parts[i + 1]
        if mark == TARGET:
            continue
        is_last = i == len(parts) - 2
        if is_last and after.lower() in ENGLISH_END and not caps:
            left.append((token, "English possessive or contraction"))
            continue
        if not caps and before[-1:].isupper() and after[:1].isupper():
            left.append((token, "a mixed-case name"))
            continue
        parts[i] = TARGET
    return "".join(parts)


def fix_text(text, found, left):
    """Rewrites the marks between letters in the text outside tags; records (old, new) in `found`."""
    out = []
    for piece in TAG.split(text):
        if not piece or TAG.fullmatch(piece):
            out.append(piece)
            continue

        def sub(m):
            if URL_BEFORE.search(piece[max(0, m.start() - 200): m.start()]):
                return m.group(0)
            new = fix_token(m.group(0), left)
            if new != m.group(0):
                found.append((m.group(0), new))
            return new

        out.append(TOKEN.sub(sub, piece))
    return "".join(out)


def walk(value, path, found, left, changes):
    """Recurses through a JSON value; records (path, old, new) for every string that changes."""
    if isinstance(value, str):
        new = fix_text(value, found, left)
        if new != value:
            changes.append((path, value, new))
    elif isinstance(value, list):
        for i, item in enumerate(value):
            walk(item, path + [i], found, left, changes)
    elif isinstance(value, dict):
        for k, v in value.items():
            if k not in SKIP_KEYS:
                walk(v, path + [k], found, left, changes)


def set_path(data, path, value):
    node = data
    for key in path[:-1]:
        node = node[key]
    node[path[-1]] = value


def uz_fields(model):
    return [f.name for f in model._meta.get_fields() if isinstance(f, (models.CharField, models.TextField)) and f.name.endswith("_uz")]


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

plan = []  # (kind, model label, obj, field-or-path, old, new, name, found)
left_all = []
by_model = Counter()
for model in apps.get_models():
    label = model._meta.label
    fields = uz_fields(model)
    has_blocks = label == "content.ContentBlock"
    if not fields and not has_blocks:
        continue
    for obj in model.objects.all().iterator():
        name = "%s #%s" % (label, obj.pk)
        for field in fields:
            old = getattr(obj, field) or ""
            found, left = [], []
            new = fix_text(old, found, left)
            left_all += [(name + "." + field,) + x for x in left]
            if new != old:
                plan.append(("field", label, obj, field, old, new, name + "." + field, found))
                by_model[label + "." + field] += 1
        if has_blocks:
            payload = (obj.data or {}).get("uz")
            if payload is not None:
                found, left, ch = [], [], []
                walk(payload, [], found, left, ch)
                where = "%s (page %s) [uz]" % (name, getattr(obj.page, "slug", "?"))
                left_all += [(where,) + x for x in left]
                for path, old, new in ch:
                    plan.append(("data", label, obj, ["uz"] + path, old, new, where, found))
                    by_model[label + ".data[uz]"] += 1

# ---- show
words = Counter()
for kind, label, obj, where, old, new, name, found in plan:
    for a, b in found:
        words[(a, b)] += 1
print()
for (a, b), n in sorted(words.items(), key=lambda kv: (-kv[1], kv[0])):
    print("   %5d x  %s   ->   %s" % (n, a, b))
print("\nWHERE (values that change):")
for k, n in by_model.most_common():
    print("   %5d  %s" % (n, k))
print("\n%d value(s) in %d place(s) would change; %d mark(s) are rewritten." % (len(plan), len({p[6] for p in plan}), sum(len(p[7]) for p in plan)))
if left_all:
    print("\nLEFT AS THEY ARE (looks like English or a name, NOT changed): %d" % len(left_all))
    for where, token, reason in left_all[:60]:
        print("   %s: %r  (%s)" % (where, token, reason))
    if len(left_all) > 60:
        print("   ... and %d more" % (len(left_all) - 60))

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
