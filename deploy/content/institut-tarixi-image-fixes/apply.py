"""Align the history page's localized images with the reviewed captions."""
from django.conf import settings

from apps.content.migration_tools import run_modes, sha
from apps.content.models import ContentBlock
from apps.media_lib.models import Image

NAME = "institut-tarixi-image-fixes"
SLUG = "department-42"
# Order: (Uzbek, Russian, English) source image IDs. The reviewed Uzbek
# image matches the biography or section at each of these positions.
SOURCE_IMAGES = {
    8: (5568, 5682, 5568),
    31: (5686, 5687, 5687),
    34: (5687, 5688, 5688),
    37: (5688, 5689, 5689),
    41: (5689, 5690, 5691),
    44: (5690, 5691, 5690),
    48: (5691, 5692, 5691),
}
LANGUAGES = ("uz", "ru", "en")


def build(apply):
    query = ContentBlock.objects.select_for_update() if apply else ContentBlock.objects
    blocks = {
        block.order: block
        for block in query.filter(page__slug=SLUG, order__in=SOURCE_IMAGES)
    }
    images = Image.objects.in_bulk(source[0] for source in SOURCE_IMAGES.values())
    entries = []
    for order, source in SOURCE_IMAGES.items():
        block = blocks.get(order)
        if block is None or block.block_type != "image":
            raise SystemExit(f"STOP: {SLUG} #{order} is missing or is not an image.")
        current = tuple(block.data.get(lang, {}).get("image_id") for lang in LANGUAGES)
        target = source[0]
        if current == (target,) * len(LANGUAGES):
            continue
        if current != source:
            raise SystemExit(f"STOP: {SLUG} #{order} image IDs differ from the reviewed export.")
        image = images.get(target)
        if not image or not image.file or not image.file.storage.exists(image.file.name):
            raise SystemExit(f"STOP: image {target} is unavailable in {settings.MEDIA_ROOT}.")
        corrected = {lang: {**payload, "image_id": target} for lang, payload in block.data.items()}
        ContentBlock(block_type="image", data=corrected).clean()
        print(f"{SLUG} #{order}: {current} -> {target}")
        entries.append({"id": block.pk, "before": block.data, "after_sha": sha(corrected)})
        if apply:
            block.data = corrected
            block.save(update_fields=["data"])
    return {"entries": entries}


def undo(rows):
    for entry in rows["entries"]:
        block = ContentBlock.objects.select_for_update().filter(pk=entry["id"], page__slug=SLUG).first()
        if block is None or block.block_type != "image" or sha(block.data) != entry["after_sha"]:
            raise SystemExit(f"STOP: block {entry['id']} changed after apply.")
        block.data = entry["before"]
        block.save(update_fields=["data"])


run_modes(NAME, build, undo)
