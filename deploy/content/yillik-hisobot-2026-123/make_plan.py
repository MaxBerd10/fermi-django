"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-123/make_plan.py

klinik-fikrlashga-doir-video-darslar (166 video lessons of the institute's own YouTube channel, @Fergana_Medical_Institute): every link was checked against the title YouTube gives for it (oEmbed). Two lessons
are wrong and are REMOVED (the staff said: "put the right one, or remove it"; the right videos were not found on the channel): "Renal Tubular Acidosis" (#3, item 10) had no link at all, and "Anticoagulant
Drugs" (#7, item 6) pointed to the video "Sickle Cell Anemia" (the same video as the lesson "Sickle Cell Anemia" two lines below). The item goes out of the list in all three languages. When the staff
upload the two videos, the lessons can be added again in the admin. Every op replaces the one block at `order`."""
import copy
import json
import subprocess
import time
from pathlib import Path

SLUG = "klinik-fikrlashga-doir-video-darslar"
REMOVE = {3: "Renal Tubular Acidosis", 7: "Anticoagulant Drugs"}
for _ in range(5):
    text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/?v=123" % SLUG], capture_output=True, text=True).stdout
    try:
        blocks = {b["order"]: b for b in json.loads(text)["blocks"]}
        break
    except ValueError:
        time.sleep(3)
ops = []
for order, name in REMOVE.items():
    block = blocks[order]
    data = block["data"]
    new = copy.deepcopy(data)
    for lang in ("uz", "ru", "en"):
        items = data[lang]["items"]
        hits = [i for i, item in enumerate(items) if ("[%s](" % name in item) or item == name]
        if lang != "ru":
            assert len(hits) == 1, (order, lang, hits)
        index = hits[0] if hits else None
        if lang == "ru":  # the Russian list is parallel to the English one: the same place
            index = [i for i, item in enumerate(data["en"]["items"]) if ("[%s](" % name in item) or item == name][0]
        new[lang]["items"] = items[:index] + items[index + 1:]
    assert len(new["uz"]["items"]) == len(new["ru"]["items"]) == len(new["en"]["items"]) == len(data["uz"]["items"]) - 1
    ops.append({"slug": SLUG, "order": order, "count": 1, "old": [{"block_type": "list", "data": data}], "new": [{"block_type": "list", "data": new}]})
Path("deploy/content/yillik-hisobot-2026-123/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ops), "blocks")
