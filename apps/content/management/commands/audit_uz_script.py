"""Read-only: where does Cyrillic text sit in an Uzbek (`uz`) slot?

Reports every `*_uz` text column and every ContentBlock `uz` payload that contains Cyrillic, split into
"Uzbek Cyrillic" (has one of the letters ў қ ғ ҳ -- certainly Uzbek typed in Cyrillic) and "other Cyrillic"
(may well be Russian prose that legacy data put in the uz slot on purpose -- see apps/content/models.py).
Changes nothing. Output is ASCII-escaped so it can be pasted anywhere.

    .venv/bin/python manage.py audit_uz_script
"""
from collections import Counter

from django.apps import apps
from django.core.management.base import BaseCommand
from django.db import models

from apps.admin_api.uz_script import has_cyrillic
from apps.content.models import ContentBlock

UZBEK_ONLY_LETTERS = set("ўқғҳЎҚҒҲ")  # ў қ ғ ҳ and capitals


def _kind(text: str) -> str:
    return "uzbek-cyrillic" if UZBEK_ONLY_LETTERS & set(text) else "other-cyrillic"


def _strings(value):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from _strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from _strings(child)


class Command(BaseCommand):
    help = "Read-only report of Cyrillic text stored in Uzbek (uz) fields."

    def handle(self, *args, **options):
        total = Counter()
        for model in apps.get_models():
            fields = [f.name for f in model._meta.get_fields()
                      if isinstance(f, (models.CharField, models.TextField)) and f.name.endswith("_uz")]
            for name in fields:
                counts, samples = Counter(), []
                for pk, text in model.objects.exclude(**{name: ""}).values_list("pk", name):
                    if text and has_cyrillic(text):
                        kind = _kind(text)
                        counts[kind] += 1
                        if len(samples) < 3:
                            samples.append((pk, kind))
                if counts:
                    total.update(counts)
                    self.stdout.write(f"{model._meta.label}.{name}: {dict(counts)} e.g. {samples}")

        counts, samples = Counter(), []
        for block in ContentBlock.objects.only("id", "page_id", "block_type", "data").iterator():
            text = " ".join(_strings((block.data or {}).get("uz")))
            if text and has_cyrillic(text):
                kind = _kind(text)
                counts[kind] += 1
                if len(samples) < 5:
                    samples.append((block.id, block.page_id, block.block_type, kind))
        total.update(counts)
        self.stdout.write(f"ContentBlock.data[uz]: {dict(counts)} e.g. {samples}")
        self.stdout.write(f"TOTAL: {dict(total)}")
