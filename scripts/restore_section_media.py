"""Restore missing local media from an audit or all PDFs in the CMS document library."""
import argparse
from functools import cache
import json
import os
from pathlib import Path
import shutil
import ssl
import sys
import tempfile
from urllib.parse import quote
from urllib.request import urlopen

from PIL import Image

PUBLIC_ORIGIN = "https://fermi.uz"


@cache
def https_context():
    context = ssl.create_default_context()
    system_bundle = Path("/etc/ssl/cert.pem")
    if ssl.get_default_verify_paths().cafile is None and system_bundle.is_file():
        context.load_verify_locations(cafile=str(system_bundle))
    return context


def args():
    parser = argparse.ArgumentParser(description=__doc__)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument("audit", nargs="?", type=Path)
    selection.add_argument("--all-pdfs", action="store_true", help="Read public PDF paths from the Django document library")
    selection.add_argument("--news-images", metavar="CATEGORY", help="Restore covers and image blocks for a published news category")
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--source-media", type=Path, help="Directory containing the backup's uploads/ tree")
    source.add_argument("--public", action="store_true", help="Read exact /media/ paths from the public site")
    parser.add_argument("--apply", action="store_true", help="Write verified files into the local media/ directory")
    return parser.parse_args()


def validate(path, kind):
    if kind == "image":
        with Image.open(path) as image:
            image.verify()
    elif kind == "document":
        with path.open("rb") as handle:
            if not handle.read(5).startswith(b"%PDF-"):
                raise ValueError("expected a PDF")


def copy_file(source_root, relative, temp, kind):
    if source_root:
        source_path = (source_root / relative).resolve()
        if not source_path.is_relative_to(source_root) or not source_path.is_file():
            raise ValueError("file is missing from the source media directory")
        with source_path.open("rb") as handle:
            shutil.copyfileobj(handle, temp)
    else:
        url = f"{PUBLIC_ORIGIN}/media/{quote(relative.as_posix(), safe='/')}"
        with urlopen(url, timeout=12, context=https_context()) as response:
            if response.geturl() != url:
                raise ValueError("the public URL redirected")
            shutil.copyfileobj(response, temp)
    temp.flush()
    validate(Path(temp.name), kind)


def setup_django():
    import django

    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    django.setup()


def cms_pdf_assets():
    setup_django()
    from apps.media_lib.models import Document
    from apps.media_lib.private import is_private_path
    from django.conf import settings

    paths = Document.objects.filter(file__iendswith=".pdf").order_by("file").values_list("file", flat=True).distinct()
    assets = [
        {"file": path, "kind": "document", "status": "missing_file"}
        for path in paths.iterator()
        if not is_private_path(path)
    ]
    return Path(settings.MEDIA_ROOT).resolve(), assets


def news_image_assets(category):
    setup_django()
    from django.conf import settings

    from apps.content.models import ContentBlock
    from apps.media_lib.models import Image as CmsImage
    from apps.media_lib.private import is_private_path
    from apps.news.models import NewsPost

    posts = NewsPost.objects.published().filter(category__slug=category)
    if not posts.exists():
        raise SystemExit(f"No published news found for {category}.")
    image_ids = set(posts.exclude(cover_id=None).values_list("cover_id", flat=True))
    blocks = ContentBlock.objects.filter(
        page_id__in=posts.order_by().values("page_id"), block_type__in=("image", "gallery")
    )
    for block in blocks.iterator():
        for payload in block.data.values():
            items = payload.get("items", []) if block.block_type == "gallery" else [payload]
            image_ids.update(item["image_id"] for item in items if item.get("image_id"))
    paths = CmsImage.objects.filter(pk__in=image_ids).order_by("file").values_list("file", flat=True).distinct()
    assets = [
        {"file": path, "kind": "image", "status": "missing_file"}
        for path in paths.iterator()
        if not is_private_path(path)
    ]
    return Path(settings.MEDIA_ROOT).resolve(), assets


def main():
    options = args()
    if options.all_pdfs:
        root, assets = cms_pdf_assets()
    elif options.news_images:
        root, assets = news_image_assets(options.news_images)
    else:
        audit = json.loads(options.audit.read_text(encoding="utf-8"))
        if audit.get("section_id") != 1827 or not isinstance(audit.get("media"), list):
            raise SystemExit("Expected the Institut haqida media audit export.")
        root = (Path(__file__).resolve().parents[1] / "media").resolve()
        assets = audit["media"]

    source_root = options.source_media.resolve() if options.source_media else None
    if options.apply:
        root.mkdir(parents=True, exist_ok=True)
    missing = 0
    present = restored = planned = 0
    for asset in assets:
        if asset["status"] != "missing_file" or not asset["file"]:
            continue
        kind = asset["kind"]
        relative = Path(asset["file"])
        target = (root / relative).resolve()
        if relative.is_absolute() or ".." in relative.parts or not target.is_relative_to(root):
            raise SystemExit(f"Unsafe media path: {relative}")
        if target.is_file():
            present += 1
            if not options.all_pdfs:
                print(f"PRESENT {relative}")
            continue
        if not options.apply:
            print(f"WOULD RESTORE {relative}")
            planned += 1
            continue
        try:
            with tempfile.NamedTemporaryFile(dir=root) as temp:
                copy_file(source_root, relative, temp, kind)
                target.parent.mkdir(parents=True, exist_ok=True)
                # Install only if the path is still free; never overwrite an existing file.
                os.link(temp.name, target)
            print(f"RESTORED {relative}")
            restored += 1
        except FileExistsError:
            print(f"PRESENT {relative}")
            present += 1
        except (OSError, ValueError, SyntaxError) as error:
            missing += 1
            print(f"MISSING {relative}: {error}")
    if options.all_pdfs:
        print(f"PDFs: {present} present, {restored} restored, {planned} planned, {missing} unavailable")
    if missing:
        raise SystemExit(f"{missing} media files could not be restored.")


if __name__ == "__main__":
    main()
