"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-120/make_plan.py

davlat-dasturlari (state programmes by year): the four PDFs of the newest years stand on top (#1-4) and the decree PF-37 of 21 February 2024 -- also a PDF, a document block -- stands alone at the very
bottom (#31), after 25 lex.uz cards. The decree moves up to place #5, right behind the other PDFs, and #5-#30 move down by one. Only the ORDER changes (the blocks keep their ids and texts).
"sig" = "type:document" or the beginning of the Uzbek text of the block."""
import json
import subprocess
import time
from pathlib import Path

SLUG = "davlat-dasturlari"
for _ in range(5):
    text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/?v=120" % SLUG], capture_output=True, text=True).stdout
    try:
        blocks = {b["order"]: b for b in json.loads(text)["blocks"]}
        break
    except ValueError:
        time.sleep(3)
last = max(blocks)
assert blocks[last]["block_type"] == "document" and last == 31


def sig(block):
    return "type:document" if block["block_type"] == "document" else block["data"]["uz"]["text"][:40]


moves = [{"old": last, "new": 5, "sig": sig(blocks[last])}]
for order in range(5, last):
    moves.append({"old": order, "new": order + 1, "sig": sig(blocks[order])})
Path("deploy/content/yillik-hisobot-2026-120/plan.json").write_text(json.dumps({"slug": SLUG, "moves": moves, "unmoved_check": {"1": "paragraph", "4": "paragraph"}}, ensure_ascii=False, indent=1), encoding="utf8")
print(len(moves), "moves")
