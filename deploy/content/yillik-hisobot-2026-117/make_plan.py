"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-117/make_plan.py

davlat-dasturlari #30, "1997 yil - Inson manfaatlari yili": its only link is http://dd.gov.uz/uz/pages/1997, a page of the old portal that answers 404 (the years 1998-2016 were moved to lex.uz
by the front end's address repair, 1997 has no known lex.uz address), so the line was a dead link in a grey tile with a DD.GOV.UZ badge. The line is removed on the user's word ("remove it").
Later blocks move up by one. The op replaces the one block at `order` by nothing ("old": what it is now)."""
import json
import subprocess
import time
from pathlib import Path

SLUG = "davlat-dasturlari"
for _ in range(5):
    text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/?v=117" % SLUG], capture_output=True, text=True).stdout
    try:
        blocks = {b["order"]: b for b in json.loads(text)["blocks"]}
        break
    except ValueError:
        time.sleep(3)
block = blocks[30]
assert "1997" in block["data"]["uz"]["text"] and "dd.gov.uz/uz/pages/1997" in block["data"]["uz"]["text"], block["data"]["uz"]
print({lang: block["data"][lang]["text"] for lang in ("uz", "ru", "en")})
ops = [{"slug": SLUG, "order": 30, "count": 1, "old": [{"block_type": block["block_type"], "data": block["data"]}], "new": []}]
Path("deploy/content/yillik-hisobot-2026-117/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ops), "op")
