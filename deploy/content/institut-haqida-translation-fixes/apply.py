"""Fix the reviewed history and USMLE translations. Default mode: dry."""
import json
from pathlib import Path

from apps.content.migration_tools import run_modes, sha
from apps.content.models import ContentBlock, Page

NAME = "institut-haqida-translation-fixes"
PLAN = Path("deploy/content") / NAME / "plan.json"


def build(apply):
    targets = []
    for entry in json.loads(PLAN.read_text(encoding="utf-8")):
        query = ContentBlock.objects.select_for_update() if apply else ContentBlock.objects
        block = query.filter(page__slug=entry["slug"], order=entry["order"]).first()
        if not block or block.block_type != entry["block_type"] or sha(block.data) != entry["source_sha"]:
            raise SystemExit(f"STOP: {entry['slug']} #{entry['order']} differs from the reviewed export.")
        data = None
        if (changes := entry["text"]) is not None:
            data = {lang: {**payload, **({"text": changes[lang]} if lang in changes else {})}
                    for lang, payload in block.data.items()}
            ContentBlock(page_id=block.page_id, order=block.order, block_type=block.block_type, data=data).clean()
        print(f"{entry['slug']} #{entry['order']}: {', '.join(changes) if changes else 'remove Wikipedia navigation line'}")
        targets.append((entry, block, data))

    entries = []
    if apply:
        for entry, block, data in targets:
            entries.append({**entry, "before": block.data, "after_sha": sha(data) if data is not None else None})
            if data is None:
                block.delete()
            else:
                block.data = data
                block.save(update_fields=["data"])
    return {"entries": entries}


def undo(rows):
    targets = []
    for entry in rows["entries"]:
        page = Page.objects.get(slug=entry["slug"])
        block = page.blocks.select_for_update().filter(order=entry["order"]).first()
        if entry["after_sha"] is None:
            if block:
                raise SystemExit(f"STOP: {page.slug} #{entry['order']} is occupied.")
        elif not block or block.block_type != entry["block_type"] or sha(block.data) != entry["after_sha"]:
            raise SystemExit(f"STOP: {page.slug} #{entry['order']} changed after apply.")
        targets.append((entry, page, block))
    for entry, page, block in targets:
        if block is None:
            page.blocks.create(order=entry["order"], block_type=entry["block_type"], data=entry["before"])
        else:
            block.data = entry["before"]
            block.save(update_fields=["data"])


run_modes(NAME, build, undo)
