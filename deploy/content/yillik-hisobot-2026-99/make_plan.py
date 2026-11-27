"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-99/make_plan.py"""
import json
import re
import subprocess
from pathlib import Path

SLUG = "study-in-uzbekistan"
blocks = json.loads(subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/" % SLUG], capture_output=True, text=True, check=True).stdout)["blocks"]
entries = []
for b in blocks:
    for lang in ("uz", "ru", "en"):
        part = b["data"].get(lang, {})
        pieces = list(part["items"]) if isinstance(part.get("items"), list) else [part["text"]] if "text" in part else []
        for piece in pieces:
            for m in re.finditer(r"\[([^\]]+)\]\(/uz\)", piece):
                entries.append({"slug": SLUG, "order": b["order"], "lang": lang, "anchor": (b["data"]["uz"].get("text") or "")[:30], "old": m.group(0), "new": "[%s](/)" % m.group(1)})
Path("deploy/content/yillik-hisobot-2026-99/plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections:", [(e["order"], e["lang"], e["old"]) for e in entries])
