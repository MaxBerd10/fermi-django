"""Read-only preflight: run with manage.py shell < this file."""
import json
import os
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

from django.conf import settings

from apps.content.migration_tools import sha
from apps.content.models import ContentBlock
from apps.media_lib.models import Image

ROOT = Path("deploy/content")
sys.path.insert(0, str(ROOT.resolve()))
from _html_to_blocks import LANGS, build  # noqa: E402


prepared = {}
for script in (36, 37, 38):
    path = ROOT / f"yillik-hisobot-2026-{script}" / "plan.json"
    for entry in json.loads(path.read_text(encoding="utf-8")):
        prepared.setdefault(entry["slug"], {})[entry["lang"]] = entry["set"]["html"]


def image_id(src):
    path = unquote(urlsplit(src).path)
    media_path = urlsplit(settings.MEDIA_URL).path
    if not media_path or not path.startswith(media_path):
        return None
    ids = list(Image.objects.filter(file=path.removeprefix(media_path)).values_list("pk", flat=True)[:2])
    return ids[0] if len(ids) == 1 else None


def inspect_page(slug):
    block = ContentBlock.objects.get(page__slug=slug, block_type="raw_html")
    html = {
        lang: prepared.get(slug, {}).get(lang) or (block.data.get(lang) or {}).get("html")
        for lang in LANGS
    }
    if missing := [lang for lang, value in html.items() if not value]:
        raise ValueError(f"Missing source: {', '.join(missing)}.")
    typed = build(html, resolve_image=image_id)
    fingerprint = sha(block.data)
    print(f"{slug}: {len(typed)} typed blocks; source #{block.order} SHA {fingerprint}")
    return {"slug": slug, "order": block.order, "source_sha": fingerprint, "blocks": typed}


failed = False
entries = []
for slug in (*prepared, "ichki-tartib-qoidalar"):
    try:
        entries.append(inspect_page(slug))
    except (ValueError, ContentBlock.DoesNotExist, ContentBlock.MultipleObjectsReturned) as error:
        failed = True
        print(f"{slug}: REVIEW REQUIRED: {error}")
if failed:
    raise SystemExit(1)
if output := os.environ.get("PLAN_OUTPUT"):
    with Path(output).open("x", encoding="utf-8") as handle:
        json.dump(entries, handle, ensure_ascii=False, indent=2)
        handle.write("\n")
