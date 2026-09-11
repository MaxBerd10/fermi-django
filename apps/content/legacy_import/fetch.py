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
import urllib.parse
import urllib.request
from dataclasses import dataclass

import certifi

API_BASE = "https://api.fermi.uz/v1"
LANGS = ("uz", "ru", "en")
_SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())


def _get_json(path: str, lang: str) -> dict:
    # Some slugs contain non-ASCII characters (Uzbek Latin uses U+02BB, not
    # a plain apostrophe -- e.g. "oʻzbekiston") that urllib won't encode on
    # its own, and the request fails outright trying to send them raw.
    url = f"{API_BASE}{urllib.parse.quote(path, safe='/?=&')}?lang={lang}"
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


@dataclass
class LegacyFaculty:
    id: int
    slug: str
    title: dict
    content: dict
    logo_url: str | None
    # Each leader already carries a stable numeric id from the old site, so
    # matching them across languages doesn't need the department staff's
    # photo-filename heuristic -- see merge_faculty_leaders().
    leaders_by_lang: dict[str, list[dict]]


def fetch_faculty_slugs() -> list[str]:
    body = _get_json("/faculty", "uz")
    return [row["slug"] for row in body["data"]]


def fetch_faculty(slug: str) -> LegacyFaculty:
    title, content, leaders_by_lang = {}, {}, {}
    faculty_id = None
    logo_url = None
    for lang in LANGS:
        body = _get_json(f"/faculty/{slug}", lang)
        data = body["data"]
        faculty_id = data["id"]
        title[lang] = data.get("title") or ""
        content[lang] = data.get("content") or ""
        logo_url = logo_url or data.get("img")
        leaders_by_lang[lang] = data.get("leaders") or []
        time.sleep(0.1)  # be polite to the production API
    return LegacyFaculty(
        id=faculty_id, slug=slug, title=title, content=content, logo_url=logo_url, leaders_by_lang=leaders_by_lang
    )


def fetch_all_faculties() -> list[LegacyFaculty]:
    slugs = fetch_faculty_slugs()
    return [fetch_faculty(slug) for slug in slugs]


def fetch_news_page(page: int, lang: str) -> dict:
    """One page of the news list -- returns the raw {"data": [...], "meta": {...}} body."""
    return _get_json(f"/news?page={page}", lang)


def fetch_news_slugs(limit: int | None = None) -> list[str]:
    """All (or the `limit` most recent) news slugs, newest first, paging
    through the list endpoint until either `limit` is reached or the API
    stops returning rows."""
    slugs: list[str] = []
    page = 1
    while limit is None or len(slugs) < limit:
        body = fetch_news_page(page, "uz")
        rows = body["data"]
        if not rows:
            break
        slugs.extend(row["slug"] for row in rows)
        page += 1
        time.sleep(0.1)
    return slugs[:limit] if limit else slugs


@dataclass
class LegacyNewsPost:
    id: int
    slug: str
    title: dict
    content: dict
    cover_url: str | None
    published_at: str | None


def fetch_news_post(slug: str) -> LegacyNewsPost:
    title, content = {}, {}
    post_id = None
    cover_url = None
    published_at = None
    for lang in LANGS:
        body = _get_json(f"/news/{slug}", lang)
        data = body["data"]
        post_id = data["id"]
        title[lang] = data.get("title") or ""
        content[lang] = data.get("content") or ""
        cover_url = cover_url or data.get("img")
        published_at = published_at or data.get("date") or data.get("published_at")
        time.sleep(0.1)
    return LegacyNewsPost(
        id=post_id, slug=slug, title=title, content=content, cover_url=cover_url, published_at=published_at
    )
