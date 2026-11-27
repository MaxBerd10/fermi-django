"""plan.json of script 118: davlat-dasturlari #5, English text: "2022- [The Year ...](lex.uz)": the "2022-" stood OUTSIDE the link, so on the English page the line was not one link and stayed a grey tile
between the file cards. One link round the whole line now ("Interests" -> "interests" mended on the way). Scanned all 238 menu pages (all three languages) for a short lead-in before ONE file / lex.uz link:
this is the only one. Written from the live text (checked 2026-11-27)."""
import json
import re
import subprocess
from pathlib import Path

text = subprocess.run(["curl", "-s", "https://fermi.uz/api/v1/pages/davlat-dasturlari/?v=118"], capture_output=True, text=True).stdout
block = {b["order"]: b for b in json.loads(text)["blocks"]}[5]
old = block["data"]["en"]["text"]
m = re.fullmatch(r"2022- \[(The Year of ensuring human Interests and strengthening the mahalla)\]\((\S+?)\)", old)
assert m, old
new = "[2022 - The Year of ensuring human interests and strengthening the mahalla](%s)" % m.group(2)
Path("deploy/content/yillik-hisobot-2026-118/plan.json").write_text(json.dumps([{"slug": "davlat-dasturlari", "order": 5, "lang": "en", "field": "text", "old": old, "new": new}], ensure_ascii=False, indent=1), encoding="utf8")
print(old, "->", new)
