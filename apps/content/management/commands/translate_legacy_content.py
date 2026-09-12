"""
Exports every ContentBlock/StaffMember field that's still a uz-fallback
copy (see ContentBlock.needs_translation / StaffMember.needs_translation)
for real translation, and applies translations back once done.

There's no machine-translation API wired into this project, and this is
real institutional content -- so the translation step itself is done by
Claude directly (reading an --export file, writing an --apply file with
real ru/en text), not by this command. This command only handles the
mechanical parts: finding what needs translating, and writing verified
translations back into the database.

Usage:
    python manage.py translate_legacy_content --export batch.json --limit 150 --offset 0
    # ... translate batch.json's entries into a second file, e.g. batch_out.json ...
    python manage.py translate_legacy_content --apply batch_out.json
"""
from __future__ import annotations

import json

from django.core.management.base import BaseCommand, CommandError

from apps.content.models import (
    ContentBlock,
    _ENGLISH_SOURCE_BLOCK_IDS,
    _PROPER_NOUN_BLOCK_IDS,
    _is_language_invariant,
    _is_ru_source_text,
)
from apps.departments.models import StaffMember

_BLOCK_TEXT_FIELDS = {
    "heading": ["text"],
    "paragraph": ["text"],
    "staff_card": ["full_name"],
}
_STAFF_FIELDS = ["full_name", "title", "bio"]

# These blocks are stanzas of a real, still-in-copyright Zulfiya poem quoted
# inside one news post. Reproducing a translation of the full poem would
# violate the copyright policy (at most one short quote, under 15 words, per
# response) -- so they're permanently excluded here instead of reappearing in
# every export batch as "still needs translation".
_COPYRIGHT_EXCLUDED_BLOCK_IDS = {18084, *range(18086, 18103)}


def _missing_langs(block_id: int, uz_value, lang_value_of) -> list[str]:
    if block_id in _PROPER_NOUN_BLOCK_IDS:
        return []
    missing = []
    for lang in ("ru", "en"):
        if lang_value_of(lang) != uz_value:
            continue
        if lang == "ru" and isinstance(uz_value, str) and _is_ru_source_text(uz_value):
            continue
        if lang == "en" and block_id in _ENGLISH_SOURCE_BLOCK_IDS:
            continue
        missing.append(lang)
    return missing


def _block_entries(block: ContentBlock):
    if block.id in _COPYRIGHT_EXCLUDED_BLOCK_IDS:
        return
    if block.block_type in _BLOCK_TEXT_FIELDS:
        for field in _BLOCK_TEXT_FIELDS[block.block_type]:
            uz_value = block.data.get("uz", {}).get(field, "")
            if uz_value and _is_language_invariant(uz_value):
                continue
            missing = _missing_langs(
                block.id, uz_value, lambda lang: block.data.get(lang, {}).get(field)
            )
            if missing and uz_value:
                yield field, uz_value, missing
    elif block.block_type == "list":
        uz_items = block.data.get("uz", {}).get("items", [])
        missing = _missing_langs(
            block.id, uz_items, lambda lang: block.data.get(lang, {}).get("items")
        )
        if missing and uz_items:
            yield "items", uz_items, missing


def _staff_entries(staff: StaffMember):
    for field in _STAFF_FIELDS:
        uz_value = getattr(staff, f"{field}_uz")
        missing = [lang for lang in ("ru", "en") if getattr(staff, f"{field}_{lang}") == uz_value]
        if missing and uz_value:
            yield field, uz_value, missing


class Command(BaseCommand):
    help = "Export ContentBlock/StaffMember fields needing real translation, or apply translations back."

    def add_arguments(self, parser):
        parser.add_argument("--export", help="Write a JSON batch of untranslated entries to this path.")
        parser.add_argument("--apply", help="Read a JSON file of {key: {lang: text}} and write it back.")
        parser.add_argument("--limit", type=int, default=150, help="Max entries per --export batch.")
        parser.add_argument("--offset", type=int, default=0, help="Skip this many entries first (for paging).")
        parser.add_argument(
            "--scope",
            choices=["all", "departments", "faculties", "news"],
            default="all",
            help="Restrict --export to blocks belonging to one content type's pages.",
        )

    def handle(self, *args, **options):
        if options["export"]:
            self._export(options["export"], options["limit"], options["offset"], options["scope"])
        elif options["apply"]:
            self._apply(options["apply"])
        else:
            raise CommandError("Pass --export <path> or --apply <path>.")

    # -- export ------------------------------------------------------------

    def _scoped_block_queryset(self, scope: str):
        qs = ContentBlock.objects.select_related("page").order_by("page_id", "order")
        if scope == "departments":
            qs = qs.filter(page__department__isnull=False)
        elif scope == "faculties":
            qs = qs.filter(page__faculty__isnull=False)
        elif scope == "news":
            qs = qs.filter(page__news_post__isnull=False)
        return qs

    def _export(self, path: str, limit: int, offset: int, scope: str) -> None:
        entries = []

        for block in self._scoped_block_queryset(scope).iterator():
            for field, uz_value, missing in _block_entries(block):
                entries.append(
                    {
                        "key": f"block:{block.id}:{field}",
                        "kind": "block",
                        "id": block.id,
                        "field": field,
                        "uz": uz_value,
                        "missing": missing,
                    }
                )

        if scope in ("all", "departments", "faculties"):
            for staff in StaffMember.objects.order_by("id").iterator():
                for field, uz_value, missing in _staff_entries(staff):
                    entries.append(
                        {
                            "key": f"staff:{staff.id}:{field}",
                            "kind": "staff",
                            "id": staff.id,
                            "field": field,
                            "uz": uz_value,
                            "missing": missing,
                        }
                    )

        total = len(entries)
        batch = entries[offset : offset + limit]
        with open(path, "w", encoding="utf-8") as f:
            json.dump(batch, f, ensure_ascii=False, indent=2)

        self.stdout.write(
            self.style.SUCCESS(
                f"Wrote {len(batch)} entries (offset {offset} of {total} total matching scope={scope}) to {path}"
            )
        )

    # -- apply ---------------------------------------------------------

    def _apply(self, path: str) -> None:
        with open(path, encoding="utf-8") as f:
            translations = json.load(f)

        updated_blocks = updated_staff = 0
        for key, langs in translations.items():
            kind, obj_id, field = key.split(":", 2)
            obj_id = int(obj_id)
            if kind == "block":
                block = ContentBlock.objects.get(pk=obj_id)
                for lang, value in langs.items():
                    block.data[lang][field] = value
                block.full_clean()
                block.save()
                updated_blocks += 1
            elif kind == "staff":
                staff = StaffMember.objects.get(pk=obj_id)
                for lang, value in langs.items():
                    setattr(staff, f"{field}_{lang}", value)
                staff.full_clean()
                staff.save()
                updated_staff += 1
            else:
                raise CommandError(f"Unknown kind in key {key!r}")

        self.stdout.write(self.style.SUCCESS(f"Applied translations to {updated_blocks} block(s), {updated_staff} staff."))
