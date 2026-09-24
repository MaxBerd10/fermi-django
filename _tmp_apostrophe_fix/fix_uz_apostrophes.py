"""One-off data-correction script: replaces the plain straight apostrophe
(U+0027) with the canonical Uzbek modifier letter turned comma (U+02BB,
'ʻ') wherever it appears between two letters in *uz*-language text --
i.e. the oʻ/gʻ digraph pattern ("bo'lib" -> "boʻlib", "Farg'ona" ->
"Fargʻona"). Scoped to the exact same regex verified against 15 real
samples (zero false positives -- every hit was a genuine digraph, never
an abbreviation/number/other use) before this ran. ru/en fields and
non-uz block data are never touched.

Run with:
    set -a; source /etc/fermi-django.env; set +a   # production only
    .venv/bin/python fix_uz_apostrophes.py [--apply]

Without --apply, only reports counts/samples -- no writes.
"""
import os
import re
import sys

sys.path.insert(0, "/Users/maxberd/Desktop/fermi-django")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from apps.content.models import ContentBlock
from apps.departments.models import StaffMember

APPLY = "--apply" in sys.argv

UZ_APOSTROPHE_WORD_RE = re.compile(r"(?<=[a-zA-Z])'(?=[a-zA-Z])")


def fix_text(text: str) -> str:
    return UZ_APOSTROPHE_WORD_RE.sub("ʻ", text)


def fix_staff():
    changed = 0
    for s in StaffMember.objects.all():
        dirty = False
        for field in ("full_name_uz", "title_uz", "bio_uz", "activity_uz", "reception_days_uz"):
            val = getattr(s, field, "") or ""
            fixed = fix_text(val)
            if fixed != val:
                dirty = True
                if APPLY:
                    setattr(s, field, fixed)
                else:
                    print(f"  StaffMember #{s.id} {field}: {val!r} -> {fixed!r}")
        if dirty:
            changed += 1
            if APPLY:
                s.save()
    print(f"StaffMember: {changed} records {'updated' if APPLY else 'would be updated'}")


def fix_blocks():
    changed = 0
    for b in ContentBlock.objects.filter(block_type__in=["heading", "paragraph", "list", "staff_card"]).iterator():
        uz = b.data.get("uz", {})
        dirty = False
        if "text" in uz:
            fixed = fix_text(uz["text"])
            if fixed != uz["text"]:
                dirty = True
                uz["text"] = fixed
        if "items" in uz:
            fixed_items = [fix_text(item) for item in uz["items"]]
            if fixed_items != uz["items"]:
                dirty = True
                uz["items"] = fixed_items
        if "full_name" in uz:
            fixed = fix_text(uz["full_name"])
            if fixed != uz["full_name"]:
                dirty = True
                uz["full_name"] = fixed
        if "title" in uz and isinstance(uz.get("title"), str):
            fixed = fix_text(uz["title"])
            if fixed != uz["title"]:
                dirty = True
                uz["title"] = fixed
        if dirty:
            changed += 1
            if APPLY:
                b.data["uz"] = uz
                b.save(update_fields=["data"])
    print(f"ContentBlock: {changed} blocks {'updated' if APPLY else 'would be updated'}")


if __name__ == "__main__":
    print("Mode:", "APPLY (writing changes)" if APPLY else "DRY RUN (no writes)")
    fix_staff()
    fix_blocks()
