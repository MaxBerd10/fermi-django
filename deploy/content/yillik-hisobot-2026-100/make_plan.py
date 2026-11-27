"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-100/make_plan.py"""
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote

SLUG = "mutaxassisliklar-boyicha-testlar-toplami"
LANGS = ("uz", "ru", "en")
blocks = json.loads(subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/" % SLUG], capture_output=True, text=True, check=True).stdout)["blocks"]
entries = []
for b in blocks:
    if b["block_type"] == "image":
        entries.append({"order": b["order"], "kind": "picture", "file_tail": unquote(b["data"]["uz"]["image"]["file"]).rsplit("/", 1)[-1], "image_id": b["data"]["uz"]["image_id"]})
    elif b["block_type"] == "paragraph":
        text = b["data"]["uz"]["text"]
        link = re.fullmatch(r"\[([^\]]+)\]\((https://fermi\.uz/media/([^)]+\.pdf))\)\s*\((uzb|rus)\)", text)
        if link:
            assert all(b["data"][lang]["text"] == text for lang in LANGS)  # the same line in the three languages
            entries.append({"order": b["order"], "kind": "pdf", "text": text, "media_path": unquote(link.group(3)), "caption": "%s (%s)" % (link.group(1), link.group(4))})
        else:
            assert "](" not in text, text
            entries.append({"order": b["order"], "kind": "heading", "text": {lang: b["data"][lang]["text"] for lang in LANGS}})
            print("plain line that becomes a heading:", entries[-1])
# only the picture, the link lines and the one department line are touched; headings and the 19 cards stay as they are
Path("deploy/content/yillik-hisobot-2026-100/plan.json").write_text(json.dumps({"slug": SLUG, "entries": entries}, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "entries:", sum(e["kind"] == "pdf" for e in entries), "link lines")
