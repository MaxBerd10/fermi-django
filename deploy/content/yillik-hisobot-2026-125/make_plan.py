"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-125/make_plan.py

Found by the check of the staff tabs of all departments in three languages (the user, 2026-11-28: "are the other places OK?"): the Uzbek heading of the lecturer's entry on the page of the
department of medical and biological chemistry (page slug department-7) #20 is 'A xadjonov Mavlonjon Maxmudjon oʻgʻli' (a space inside the surname), so the page did not take it for a name and
the entry was lost from the Uzbek staff tab. Russian (Ахаджонов Мавлонжон Махмуджон угли) and English (Axadjonov Mavlonjon Maxmudjon ugli) were right.
Every op: {slug, order, lang, field, old, new}."""
import json
import subprocess
from pathlib import Path

text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/departments/tibbiy-va-biologik-kimyo-kafedrasi/?v=125"], capture_output=True, text=True).stdout
dep = json.loads(text)
dep = dep.get("data", dep)["page"]
assert dep["slug"] == "department-7"
block = {b["order"]: b for b in dep["blocks"]}[20]
old = block["data"]["uz"]["text"]
NEW = "Axadjonov Mavlonjon Maxmudjon oʻgʻli"
assert old.replace(" ", "").replace("ʻ", "") == NEW.replace(" ", "").replace("ʻ", ""), old
assert block["data"]["en"]["text"] == "Axadjonov Mavlonjon Maxmudjon ugli"
ops = [{"slug": "department-7", "order": 20, "lang": "uz", "field": "text", "old": old, "new": NEW}]
Path("deploy/content/yillik-hisobot-2026-125/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
for o in ops:
    print(o["slug"], o["order"], o["lang"], "|", repr(o["old"]), "->", repr(o["new"]))
