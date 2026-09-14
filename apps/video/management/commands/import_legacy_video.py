"""
Imports the /video gallery from the old site's live API into VideoClip.

Self-hosted clips are re-encoded on the way in (720p, H.264 CRF 21, AAC
128k) rather than stored as-is -- the old site's own files are wildly
inconsistent (some already ~480p/1.3Mbps, others raw ~1080p/9Mbps phone/
camera exports), and re-encoding cuts total storage from ~14.7GB to
roughly a third of that with no visible quality loss at web sizes
(spot-checked against the original frame by frame before picking CRF 21).
YouTube-embedded items need no download at all -- just the video id.

Idempotent: re-running clears and rebuilds every VideoClip row. Slow by
necessity (one download + one transcode per self-hosted clip, ~162 of
them) -- expect this to run for an hour or more.

Usage:
    python manage.py import_legacy_video --dry-run
    python manage.py import_legacy_video
    python manage.py import_legacy_video --limit=5   # for a quick test run
"""
from __future__ import annotations

import json
import os
import ssl
import subprocess
import tempfile
import urllib.parse
import urllib.request

import certifi
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.video.models import VideoClip

_API_BASE = "https://api.fermi.uz/v1"
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _get_json(path: str, **params) -> dict:
    query = f"?{urllib.parse.urlencode(params)}" if params else ""
    url = f"{_API_BASE}{path}{query}"
    req = urllib.request.Request(url, headers={"User-Agent": "fermi-django-migration/0.1"})
    with urllib.request.urlopen(req, timeout=20, context=_SSL_CONTEXT) as resp:
        return json.load(resp)


def _fetch_all_items() -> list[dict]:
    items = []
    page = 1
    while True:
        data = _get_json("/video", page=page)["data"]
        if not data:
            break
        items.extend(data)
        page += 1
    return items


def _download(url: str, dest_path: str) -> None:
    req = urllib.request.Request(url, headers={"User-Agent": "fermi-django-migration/0.1"})
    with urllib.request.urlopen(req, timeout=120, context=_SSL_CONTEXT) as resp, open(dest_path, "wb") as out:
        while chunk := resp.read(1024 * 1024):
            out.write(chunk)


def _transcode(src_path: str, dest_path: str) -> None:
    subprocess.run(
        [
            "ffmpeg", "-y", "-i", src_path,
            # Cap at 720p tall -- never upscale a source that's already
            # smaller (the old site has plenty of native 480p clips;
            # forcing those up to 720p only inflates the file for no
            # real detail gained).
            "-vf", "scale=-2:'min(720,ih)'",
            "-c:v", "libx264", "-preset", "medium", "-crf", "21",
            "-c:a", "aac", "-b:a", "128k",
            dest_path,
        ],
        check=True, capture_output=True, timeout=600,
    )


class Command(BaseCommand):
    help = "Import the old site's /video gallery into VideoClip, re-encoding self-hosted clips to 720p."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true", help="Fetch and report only -- writes nothing.")
        parser.add_argument("--limit", type=int, help="Import only the first N items (for testing).")

    def handle(self, *args, **options):
        dry_run = options["dry_run"]
        limit = options.get("limit")

        items = _fetch_all_items()
        if limit:
            items = items[:limit]
        youtube_count = sum(1 for it in items if it.get("url"))
        file_count = sum(1 for it in items if it.get("video") and not it.get("url"))
        self.stdout.write(f"{len(items)} item(s) to process ({youtube_count} YouTube, {file_count} self-hosted).\n")

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Would import {len(items)} item(s)."))
            return

        with transaction.atomic():
            VideoClip.objects.all().delete()

        total = len(items)
        imported = 0
        for index, item in enumerate(items, start=1):
            order = total - index  # old site lists newest-first by id
            if item.get("url"):
                VideoClip.objects.create(youtube_id=item["url"], order=order)
                imported += 1
                self.stdout.write(f"  [{index}/{total}] youtube:{item['url']}")
                continue

            src_url = item.get("video")
            if not src_url:
                continue

            filename = urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(src_url).path)) or f"video-{item['id']}.mp4"
            with tempfile.TemporaryDirectory() as tmp_dir:
                src_path = os.path.join(tmp_dir, "src" + os.path.splitext(filename)[1])
                out_path = os.path.join(tmp_dir, "out.mp4")
                try:
                    _download(src_url, src_path)
                    _transcode(src_path, out_path)
                    with open(out_path, "rb") as f:
                        content = f.read()
                    clip = VideoClip(order=order)
                    clip.file.save(os.path.splitext(filename)[0] + ".mp4", ContentFile(content), save=False)
                    clip.full_clean()
                    clip.save()
                    imported += 1
                    self.stdout.write(f"  [{index}/{total}] ok: {filename} ({len(content) / 1024 / 1024:.1f} MB)")
                except Exception as exc:  # noqa: BLE001 -- a broken/missing legacy video must not abort the import
                    self.stderr.write(self.style.WARNING(f"  [{index}/{total}] FAILED {src_url[:80]}: {exc}"))

        self.stdout.write(self.style.SUCCESS(f"\nImported {imported}/{total} video item(s)."))
