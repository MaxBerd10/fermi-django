"""Review dry output, then supply EXPECTED_SOURCE_SHA for apply."""
import json
import os
from pathlib import Path
from urllib.parse import urlsplit

from apps.content.migration_tools import run_modes, sha
from apps.menu.models import MenuItem

NAME = "yillik-hisobot-2026-44"
SECTION_ID = 1827
FIELDS = ("label_uz", "label_ru", "label_en")
# The same page is also listed under "Meʼyoriy hujjatlar" (menu item 1881, /blog/1879/kredit-modul-nizomi): it gets the same corrected labels.
# Other entries with this slug (e.g. "Kredit modul tizimi" under 2023) are a different menu name and stay.
EXTRA_ITEMS = {1881: "kredit-modul-nizomi"}


def snapshot(item):
    return {"id": item.pk, "parent_id": item.parent_id, "url": item.url,
            "label_uz": item.label_uz, "label_ru": item.label_ru, "label_en": item.label_en}


def build(apply):
    plan = json.loads((Path("deploy/content") / NAME / "plan.json").read_text(encoding="utf-8"))
    query = MenuItem.objects.select_for_update() if apply else MenuItem.objects
    section = query.get(pk=SECTION_ID)
    items = list(query.filter(parent_id=SECTION_ID).order_by("pk"))
    targets = {}
    for item in items:
        slug = urlsplit(item.url).path.rstrip("/").rsplit("/", 1)[-1]
        if slug in plan:
            if slug in targets:
                raise SystemExit(f"STOP: duplicate in the Institut haqida menu: {slug}.")
            targets[slug] = item

    for pk, slug in EXTRA_ITEMS.items():
        extra = query.filter(pk=pk).first()
        if extra is None or urlsplit(extra.url).path.rstrip("/").rsplit("/", 1)[-1] != slug:
            raise SystemExit(f"STOP: menu item {pk} is not the page {slug} any more.")
        targets[f"{slug}@{pk}"] = extra
        plan[f"{slug}@{pk}"] = plan[slug]

    if missing := set(plan) - set(targets):
        raise SystemExit(f"STOP: missing from the Institut haqida menu: {', '.join(sorted(missing))}.")
    targets["section"] = section
    plan["section"] = plan["institut-xaqida"]
    before = {slug: snapshot(item) for slug, item in targets.items()}
    fingerprint = sha(before)
    for slug, item in targets.items():
        for lang, label in plan[slug].items():
            print(f"#{item.pk} {lang}: {getattr(item, f'label_{lang}')} -> {label}")
    print(f"EXPECTED_SOURCE_SHA={fingerprint}")
    if not apply:
        return {}
    if os.environ.get("EXPECTED_SOURCE_SHA") != fingerprint:
        raise SystemExit("STOP: menu differs from the reviewed dry run.")

    after = {}
    for slug, item in targets.items():
        fields = []
        for lang, label in plan[slug].items():
            field = f"label_{lang}"
            setattr(item, field, label)
            fields.append(field)
        item.save(update_fields=fields)
        after[slug] = snapshot(item)
    return {"before": before, "after": after}


def undo(rows):
    current = {}
    for slug, expected in rows["after"].items():
        item = MenuItem.objects.select_for_update().get(pk=expected["id"])
        if snapshot(item) != expected:
            raise SystemExit(f"STOP: {slug} menu item changed after apply. Backup retained.")
        current[slug] = item
    for slug, item in current.items():
        for field in FIELDS:
            setattr(item, field, rows["before"][slug][field])
        item.save(update_fields=FIELDS)
    print("Restored previous labels in the section.")


run_modes(NAME, build, undo)
