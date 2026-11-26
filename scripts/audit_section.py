"""Read-only audit of menu sections (default: Institut haqida): python manage.py shell < scripts/audit_section.py
Several sections: SECTION_IDS=1827,1857,1864 python manage.py shell < scripts/audit_section.py"""
import json
import os
import re
from collections import Counter
from pathlib import Path
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup
from django.core.exceptions import ValidationError

from apps.content.models import Page
from apps.departments.models import Department
from apps.media_lib.models import Document, Image, Video
from apps.menu.models import MenuItem

LANGS = ("uz", "ru", "en")
SECTION_IDS = [int(part) for part in os.environ.get("SECTION_IDS", "1827").split(",")]
MEDIA = {"image": (Image, "image_id"), "document": (Document, "document_id"), "video": (Video, "video_id")}
PROSE = {
    "heading": ("text",), "paragraph": ("text",), "staff_card": ("full_name", "title"),
    "list": ("items",), "table": ("headers", "rows"), "image": ("alt",),
    "document": ("caption",), "video": ("caption",), "gallery": ("items",),
}
LINK = re.compile(r"(?:https?://[^\s<>]+|(?<![\w/])/(?:blog|departments)/[^\s<>]+)")
YEAR = re.compile(r"(?<!\d)(?:19|20)\d{2}(?!\d)")
issues = Counter()
media_inventory = {}


def issue(kind, location, detail):
    issues[kind] += 1
    print(f"{kind.upper():12} {location}: {detail}")


def layout_shape(kind, data):
    if kind == "heading":
        return data.get("level", 2)
    if kind in {"list", "gallery"}:
        return len(data.get("items") or []), data.get("style")
    if kind == "table":
        return len(data.get("headers") or []), tuple(len(row) for row in data.get("rows") or [])
    return data.get("style")


def local_page(url):
    path = urlsplit(url).path.strip("/").split("/")
    if len(path) != 3 or path[0] not in {"blog", "departments"}:
        return None
    route, _, slug = path
    slug = unquote(slug)
    slug = re.sub(r"^(?:institut-yol|yo-l|yol)-xaritasi-2026$", "institut-yol-xaritasi-2025", slug)
    if route == "departments":
        department = Department.objects.filter(slug=slug).select_related("page").first()
        return department.page if department else None
    return Page.objects.filter(slug=slug).first()


def check_media(kind, data, location):
    if kind == "gallery":
        for index, item in enumerate(data.get("items") or [], 1):
            check_media("image", item, f"{location} gallery item {index}")
    if kind in MEDIA:
        model, field = MEDIA[kind]
        asset_id = data.get(field)
        key = (kind, asset_id)
        if key not in media_inventory:
            # Reading the field without instantiating Image avoids Django trying
            # to derive dimensions from a missing file on older media rows.
            files = list(model.objects.filter(pk=asset_id).values_list("file", flat=True))
            filename = files[0] if files else None
            if not files:
                status = "missing_row"
            elif not filename:
                status = "missing_file_name"
            elif not model._meta.get_field("file").storage.exists(filename):
                status = "missing_file"
            else:
                status = "available"
            media_inventory[key] = {
                "kind": kind, "id": asset_id, "file": filename, "status": status, "references": [],
            }
        record = media_inventory[key]
        record["references"].append(location)
        if record["status"] != "available":
            suffix = f" ({record['file']})" if record["file"] else ""
            issue("media", location, f"{record['status']} {field}={asset_id}{suffix}")


def text_units(value, field):
    if isinstance(value, str) and value.strip():
        yield field, value.strip()
    elif isinstance(value, list):
        for index, item in enumerate(value, 1):
            yield from text_units(item, f"{field}[{index}]")
    elif isinstance(value, dict) and "alt" in value:
        yield from text_units(value["alt"], f"{field}.alt")


def check_link(url, location):
    url = re.split(r"[()\]]", url)[0]  # the rest is text glued to the link, not part of it
    try:
        parts = urlsplit(url.rstrip(".,;:"))
        host = parts.hostname
    except ValueError:  # an address that is not an address (a broken link in the old text)
        issue("link", location, f"not a valid address: {url[:70]}")
        return
    if host not in (None, "fermi.uz", "www.fermi.uz"):
        return
    if parts.path.startswith(("/blog/", "/departments/")) and not local_page(parts.geturl()):
        issue("link", location, f"no CMS target for {parts.path}")


def compare_text(source, translated, lang, location):
    for field, text in translated.items():
        original = source.get(field, "")
        if not original:
            continue
        where = f"{location} {field}"
        if len(text) >= 45 and text == original:
            issue("review", where, "long text identical to UZ")
        if Counter(YEAR.findall(original)) != Counter(YEAR.findall(text)):
            issue("review", where, "year references differ from UZ")
        prose = LINK.sub("", text)
        cyrillic = len(re.findall(r"[А-Яа-яЁёЎўҚқҒғҲҳ]", prose))
        letters = sum(char.isalpha() for char in prose)
        if letters >= 45 and ((lang == "ru" and cyrillic == 0) or (lang == "en" and cyrillic > letters / 2)):
            issue("review", where, "script does not match the expected language")


def audit_page(page):
    blocks = list(page.blocks.all())
    if not blocks:
        issue("empty", page.slug, "page has no blocks")
    for block in blocks:
        where = f"{page.slug} #{block.order}"
        kind = block.block_type
        if kind == "raw_html":
            issue("legacy", where, "raw_html still present")
        try:
            block.clean()
        except ValidationError as error:
            issue("validation", where, "; ".join(error.messages))
            continue
        if any(not isinstance(block.data.get(lang), dict) for lang in LANGS):
            issue("language", where, "missing localized payload")
            continue
        uz = block.data["uz"]
        fields = PROSE.get(kind, ())
        source = dict(unit for field in fields for unit in text_units(uz.get(field), field))
        for lang in LANGS:
            data = block.data[lang]
            location = f"{where} {lang}"
            check_media(kind, data, location)
            text = dict(unit for field in fields for unit in text_units(data.get(field), field))
            links = {link for value in text.values() for link in LINK.findall(value)}
            if kind == "raw_html":
                html = BeautifulSoup(data.get("html", ""), "html.parser")
                links.update(anchor["href"] for anchor in html.find_all("a", href=True))
            for link in sorted(links):
                check_link(link, location)
            if lang == "uz":
                continue
            if layout_shape(kind, data) != layout_shape(kind, uz):
                issue("structure", location, "structure differs from UZ")
            compare_text(source, text, lang, location)


seen = set()
export_path = os.environ.get("AUDIT_EXPORT")
export = {"section_ids": SECTION_IDS, "menu": [], "pages": []}
pending = [child for section_id in SECTION_IDS for child in MenuItem.objects.get(pk=section_id).children.all()]
while pending:
    item = pending.pop(0)
    pending.extend(item.children.all())
    if not item.url:
        continue
    for lang in LANGS:
        if not getattr(item, f"label_{lang}").strip():
            issue("menu", f"#{item.pk} {lang}", "missing label")
    page = local_page(item.url)
    if export_path:
        export["menu"].append({
            "id": item.pk,
            "parent_id": item.parent_id,
            "url": item.url,
            "labels": {lang: getattr(item, f"label_{lang}") for lang in LANGS},
            "page_slug": page.slug if page else None,
        })
    if not page:
        issue("route", f"#{item.pk}", f"no CMS page for {item.url}")
        continue
    if page.pk not in seen:
        seen.add(page.pk)
        audit_page(page)
        if export_path:
            export["pages"].append({
                "slug": page.slug,
                "blocks": list(page.blocks.order_by("order").values("id", "order", "block_type", "data")),
            })
if export_path:
    export["findings"] = dict(issues)
    export["media"] = list(media_inventory.values())
    with Path(export_path).open("x", encoding="utf-8") as handle:
        json.dump(export, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
    print(f"Section exported: {export_path}")
print(f"Distinct media references: {dict(Counter(record['status'] for record in media_inventory.values()))}")
print(f"Reviewed {len(seen)} distinct pages for UZ/RU/EN. Findings: {dict(issues)}")
if len(seen) != 25 or issues:
    raise SystemExit(1)
