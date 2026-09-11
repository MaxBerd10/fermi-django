"""
Flattens HTML into plain text for content that's simple prose/lists rather
than the deeply-nested, staff-bio-mixed-in structure department pages have
(see html_extract.py for that harder case) -- used for faculty leader bios,
where the old API already hands back structured JSON and only individual
fields (activity, biography) are still raw HTML.
"""
from __future__ import annotations

from bs4 import BeautifulSoup


def html_to_plain_text(html: str | None) -> str:
    if not html or not html.strip():
        return ""
    html = html.replace("&nbsp;", " ").replace("\xa0", " ")
    soup = BeautifulSoup(html, "lxml")
    lines = [" ".join(line.split()) for line in soup.get_text("\n").split("\n")]
    return " ".join(line for line in lines if line)
