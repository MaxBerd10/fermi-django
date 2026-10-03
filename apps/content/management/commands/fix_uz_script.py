"""Repairs Cyrillic that already sits in Uzbek (`uz`) slots -- the one-off companion of the admin API's
automatic Latin conversion (apps/admin_api/uz_script.py). DRY RUN by default; nothing is written
without --apply.

Per text (see uz_script.repair):
  uzbek  Cyrillic Uzbek (has ў қ ғ ҳ)        -> converted to Latin
  mixed  Latin with Cyrillic slips in a word -> only those words repaired ("Хorijiy" -> "Xorijiy")
  leave  anything still Cyrillic (Russian prose put in uz on purpose, or too short to tell) -> untouched

Writes use queryset.update(), so no model save() side effects. Output is ASCII-escaped.

    .venv/bin/python manage.py fix_uz_script            # report only
    .venv/bin/python manage.py fix_uz_script --apply
"""
from collections import Counter

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models, transaction

from apps.admin_api.uz_script import has_cyrillic, repair
from apps.content.models import ContentBlock


def _repair_json(value, tally):
    if isinstance(value, str):
        new, kind = repair(value)
        tally[kind] += 1
        return new
    if isinstance(value, dict):
        return {key: _repair_json(child, tally) for key, child in value.items()}
    if isinstance(value, list):
        return [_repair_json(child, tally) for child in value]
    return value


class Command(BaseCommand):
    help = "Repair Cyrillic in Uzbek slots (dry run unless --apply)."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true", help="write the changes")

    def handle(self, *args, apply=False, **options):
        total, left = Counter(), []
        with transaction.atomic():
            for model in apps.get_models():
                fields = [f for f in model._meta.get_fields()
                          if isinstance(f, (models.CharField, models.TextField)) and f.name.endswith("_uz")]
                for field in fields:
                    name = field.name
                    for pk, text in model.objects.exclude(**{name: ""}).values_list("pk", name):
                        if not text or not has_cyrillic(text):
                            continue
                        new, kind = repair(text)
                        total[kind] += 1
                        if kind == "leave":
                            left.append((model._meta.label, name, pk))
                        elif field.max_length and len(new) > field.max_length:
                            # Latin spelling is longer than Cyrillic: would not fit the column
                            total["too-long-skipped"] += 1
                            left.append((model._meta.label, name, pk))
                        elif apply and new != text:
                            model.objects.filter(pk=pk).update(**{name: new})

            for block in ContentBlock.objects.only("id", "data").iterator():
                payload = (block.data or {}).get("uz")
                if payload is None:
                    continue
                tally = Counter()
                new_payload = _repair_json(payload, tally)
                tally.pop("clean", None)
                if not tally:
                    continue
                total.update(tally)
                if tally.get("leave"):
                    left.append(("ContentBlock", "data[uz]", block.id))
                if apply and new_payload != payload:
                    ContentBlock.objects.filter(pk=block.pk).update(data={**block.data, "uz": new_payload})
            if not apply:
                transaction.set_rollback(True)

        total.pop("clean", None)
        self.stdout.write(f"{'APPLIED' if apply else 'DRY RUN (nothing written)'}: {dict(total)}")
        self.stdout.write(f"left for a human (still Cyrillic): {len(left)}; first 12: {left[:12]}")
