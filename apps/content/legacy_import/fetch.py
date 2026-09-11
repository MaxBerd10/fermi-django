"""
Pulls department data straight from the OLD site's own public API
(https://api.fermi.uz/v1/departments) instead of a raw MySQL export --
it already serves exactly content_uz/ru/en per department (via ?lang=),
already filtered to published/active rows, so there's no need to touch the
production database directly or shuttle a JSON dump through the terminal.
Read-only: this module never writes anything back to api.fermi.uz.
"""
from __future__ import annotations

import json
import ssl
import time
import urllib.request
from dataclasses import dataclass

import certifi

API_BASE = "https://api.fermi.uz/v1"
LANGS = ("uz", "ru", "en")
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _get_json(path: str, lang: str) -> dict:
    url = f"{API_BASE}{path}?lang={lang}"
    req = urllib.request.Request(url, headers={"User-Agent": "fermi-django-migration/0.1"})
    with urllib.request.urlopen(req, timeout=20, context=_SSL_CONTEXT) as resp:
        return json.load(resp)


@dataclass
class LegacyDepartment:
    id: int
    slug: str
    title: dict  # {"uz": ..., "ru": ..., "en": ...}
    content: dict  # {"uz": <html>, "ru": <html>, "en": <html>}
    logo_url: str | None


def fetch_department_slugs() -> list[str]:
    body = _get_json("/departments", "uz")
    return [row["slug"] for row in body["data"]]


def fetch_department(slug: str) -> LegacyDepartment:
    title, content = {}, {}
    dept_id = None
    logo_url = None
    for lang in LANGS:
        body = _get_json(f"/departments/{slug}", lang)
        data = body["data"]
        dept_id = data["id"]
        title[lang] = data.get("title") or ""
        content[lang] = data.get("content") or ""
        logo_url = logo_url or data.get("img")
        time.sleep(0.1)  # be polite to the production API
    return LegacyDepartment(id=dept_id, slug=slug, title=title, content=content, logo_url=logo_url)


def fetch_all_departments() -> list[LegacyDepartment]:
    slugs = fetch_department_slugs()
    return [fetch_department(slug) for slug in slugs]
