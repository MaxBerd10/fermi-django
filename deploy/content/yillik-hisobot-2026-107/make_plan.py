"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-107/make_plan.py

Pediatriya faculty page, block 2 (the mission of the faculty): the English text is a copy of the Pharmacy programme's mission (it repeats block 4); the uz and ru texts are the faculty
mission. Only the English text of this one block is replaced, by a translation of the Russian text (the uz text says the same)."""
import json
import subprocess
from pathlib import Path

EN = ("The mission of the Pediatrics faculty is to train medical students taking into account the best achievements of national and world science and healthcare, "
      "and to form highly qualified specialists who are able to solve current healthcare problems in modern conditions and who are competitive and in demand in the labour market.")
d = json.loads(subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/faculty-4/"], capture_output=True, text=True, check=True).stdout)
b = {x["order"]: x for x in d["blocks"]}[2]
assert b["block_type"] == "paragraph" and b["data"]["en"]["text"].startswith("The mission of the Pharmacy educational program"), b["data"]["en"]
old = {"block_type": b["block_type"], "data": b["data"]}
new = {"block_type": "paragraph", "data": {**b["data"], "en": {**b["data"]["en"], "text": EN}}}
Path("deploy/content/yillik-hisobot-2026-107/plan.json").write_text(json.dumps([{"slug": "faculty-4", "order": 2, "count": 1, "old": [old], "new": [new]}], ensure_ascii=False, indent=1), encoding="utf8")
print("1 op")
