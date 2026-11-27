"""Builds plan.json from the LIVE site's API (read-only, needs the network) and the two review files:
    python3 deploy/content/yillik-hisobot-2026-96/make_plan.py
The old text of every correction is the whole current line of the live block; the apply replaces it only where it is found exactly once."""
import json
import subprocess
from pathlib import Path

HERE = Path("deploy/content/yillik-hisobot-2026-96")
# findings NOT taken over: the Ministry's order of 6 April 2026 (the uz sentence names no document) and the two garbled uz sentences (kind 'needs-source' / 'uz-source')
SKIP = {"pages": {12, 13, 15, 16}, "news": set()}


def get(url):
    return json.loads(subprocess.run(["curl", "-s", "--max-time", "90", url], capture_output=True, text=True, check=True).stdout)


def pieces(part):
    return list(part["items"]) if isinstance(part.get("items"), list) else [part["text"]] if "text" in part else [part["caption"]]


entries = []
for kind, name in (("pages", "findings_pages.json"), ("news", "findings_news.json")):
    for index, f in enumerate(json.loads((HERE / name).read_text(encoding="utf8"))):
        if index in SKIP[kind] or not f["fix"]:
            continue
        slug = f["page"]
        if kind == "pages":
            blocks = get("https://fermi.uz/api/v1/pages/%s/" % slug)["blocks"]
            where = {"page": slug}
        else:
            if f["block"] in ("T", "E"):
                raise SystemExit("a title/excerpt finding is not expected: %r" % f)
            blocks = get("https://fermi.uz/api/v1/news/%s/" % slug)["page"]["blocks"]
            where = {"news": slug}
        block = next(b for b in blocks if b["order"] == int(f["block"]))
        current = pieces(block["data"][f["lang"]])[f.get("item") or 0]
        assert current.startswith(f["current"][:60].rstrip(".")[:60]) or f["current"][:40] in current, (slug, f["block"], f["lang"])
        entries.append({**where, "order": int(f["block"]), "lang": f["lang"], "anchor": pieces(block["data"]["uz"])[0][:30], "old": current, "new": f["fix"]})
(HERE / "plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections in", len({(e.get("page") or e.get("news"), e["order"]) for e in entries}), "blocks")
