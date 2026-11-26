"""Move the reviewed Thumbay and To'maris presentation fixes into CMS data."""
import json
from pathlib import Path

from django.core.files import File

from apps.content.migration_tools import replace_blocks, run_modes
from apps.content.models import ContentBlock, Page
from apps.media_lib.models import Image
from apps.news.models import NewsPost

NAME = "news-cms-cleanup"
THUMBAY = "thumbay-fergana-college-of-medical-sciences"
TOMARIS = "tomaris-izdoshlari-sport-musobaqasi"
PHOTO = Path("frontend/public/images/thumbay-university-campus.webp")
TRANSLATIONS = json.loads((Path("deploy/content") / NAME / "translations.json").read_text())
LANGUAGES = ("uz", "ru", "en")
REMOVED_HEADINGS = (
    "$1 million investment",
    "International cooperation",
    "The cooperation between the Fergana Medical Institute of Public Health and the Gulf Medical University",
)


def normalized(value):
    return value.strip().replace("\u200b", "").strip().translate(str.maketrans("ʻʼ‘’", "''''")).casefold()


def thumbay_rows(rows):
    translated = []
    for row in rows:
        kind = row["block_type"]
        data = row["data"]
        if kind in ("heading", "paragraph"):
            removed = REMOVED_HEADINGS if kind == "heading" else ("Apply Now",)
            recognized = {normalized(text) for key in removed for text in (key, TRANSLATIONS[key])}
            if normalized(data["uz"]["text"]) in recognized:
                continue
            text = data["uz"]["text"]
            data = {**data, "uz": {**data["uz"], "text": TRANSLATIONS.get(text.replace("\u200b", "").strip(), text)}}
        elif kind == "list":
            items = [TRANSLATIONS.get(item.strip(), item) for item in data["uz"]["items"]]
            data = {**data, "uz": {**data["uz"], "items": items}}
        translated.append({**row, "data": data})

    result = []
    seen = {}
    for row in translated:
        if row["block_type"] == "list" and result and result[-1]["block_type"] == "heading":
            heading = result[-1]
            key = normalized(heading["data"]["uz"]["text"])
            items = {normalized(item) for item in row["data"]["uz"]["items"]}
            if key in seen and items and items <= seen[key]:
                result.pop()
                continue
            seen[key] = items
        result.append(row)
    return result


def snapshot(page):
    return list(page.blocks.order_by("order").values("id", "order", "block_type", "data"))


def build(apply):
    page_query = Page.objects.select_for_update() if apply else Page.objects
    page = page_query.get(slug=THUMBAY)
    post = NewsPost.objects.select_for_update().get(slug=TOMARIS) if apply else NewsPost.objects.get(slug=TOMARIS)
    before = snapshot(page)
    if not before or not PHOTO.is_file():
        raise SystemExit("Thumbay blocks or campus image are missing.")
    poster = post.page.blocks.filter(block_type="image").first()
    if not poster:
        raise SystemExit("To'maris has no standalone poster block. Review the CMS article first.")
    poster_ids = {lang: poster.data.get(lang, {}).get("image_id") for lang in LANGUAGES}
    poster_id = poster_ids["uz"]
    image = Image.objects.filter(pk=poster_id).first() if poster_id else None
    if not image or not image.file:
        raise SystemExit(f"To'maris Uzbek poster is missing. Inline image IDs: {poster_ids}")
    updated = thumbay_rows(before)
    print(f"Thumbay: {len(before)} → {len(updated) + 1} blocks including campus photo")
    print(f"To'maris: inline image IDs {poster_ids}")
    print(f"To'maris: cover {post.cover_id} → Uzbek inline poster {poster_id} ({image.file.name})")
    if not apply:
        return {}
    image = Image(alt_text="Gulf Medical University")
    with PHOTO.open("rb") as handle:
        image.file.save(PHOTO.name, File(handle), save=True)
    # Preserve IDs on existing blocks and insert the campus image before them.
    kept = {row["id"] for row in updated}
    page.blocks.exclude(id__in=kept).delete()
    for row in updated:
        page.blocks.filter(id=row["id"]).update(data=row["data"])
    replace_blocks(page, before[0]["order"], 0, [{
        "block_type": "image",
        "data": {lang: {"image_id": image.pk, "alt": image.alt_text} for lang in LANGUAGES},
    }])
    cover_before = post.cover_id
    post.cover_id = poster_id
    post.save(update_fields=["cover"])
    return {"before": before, "after": snapshot(page), "cover_before": cover_before, "cover_after": poster_id}


def undo(rows):
    page = Page.objects.select_for_update().get(slug=THUMBAY)
    post = NewsPost.objects.select_for_update().get(slug=TOMARIS)
    if snapshot(page) != rows["after"] or post.cover_id != rows["cover_after"]:
        raise SystemExit("CMS content changed after apply. Backup retained.")
    page.blocks.all().delete()
    ContentBlock.objects.bulk_create(ContentBlock(page=page, **row) for row in rows["before"])
    post.cover_id = rows["cover_before"]
    post.save(update_fields=["cover"])


run_modes(NAME, build, undo)
