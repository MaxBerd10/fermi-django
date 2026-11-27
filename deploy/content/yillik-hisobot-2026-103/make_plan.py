"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-103/make_plan.py

klinik-fikrlashga-doir-video-darslar ("STEP 1", 166 video lessons as YouTube links in seven sections): three of the seven section lines were paragraphs, the other four headings: all
seven are headings now (uz without the closing full stop, like the four that already were); plain letter errors: the section name "Infekstion kaslliklar", "Biochemstry" (en) and seven
English lesson titles (Alcolosis, Klinefeter, Thallassemias, Sicle, Microtuble, Antibiotiotics, Cadiac). Every op replaces ONE block ("old": what it is now, "new": what it becomes)."""
import copy
import json
import subprocess
from pathlib import Path

SLUG = "klinik-fikrlashga-doir-video-darslar"
LANGS = ("uz", "ru", "en")
TITLE_FIXES = {"Alcolosis": "Alkalosis", "Klinefeter": "Klinefelter", "Thallassemias": "Thalassemias", "Sicle Cell": "Sickle Cell",
               "Microtuble": "Microtubule", "Antibiotiotics": "Antibiotics", "Cadiac": "Cardiac"}
blocks = {b["order"]: b for b in json.loads(subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/" % SLUG], capture_output=True, text=True, check=True).stdout)["blocks"]}
ops = []
for order, b in sorted(blocks.items()):
    old = {"block_type": b["block_type"], "data": b["data"]}
    new = copy.deepcopy(old)
    if b["block_type"] == "paragraph" and order in (4, 6, 8):  # "... bo'limi mavzulari." lines: headings like the other four
        new["block_type"] = "heading"
        for lang in LANGS:
            text = new["data"][lang]["text"]
            new["data"][lang] = {"text": text[:-1] if lang == "uz" and text.endswith(".") else text, "level": 3}
    if b["block_type"] == "heading" and order == 10:
        assert new["data"]["uz"]["text"].count("Infekstion kaslliklar") == 1
        new["data"]["uz"]["text"] = new["data"]["uz"]["text"].replace("Infekstion kaslliklar", "Infeksion kasalliklar")
    if b["block_type"] == "heading" and order == 12:
        assert new["data"]["en"]["text"].count("Biochemstry") == 1
        new["data"]["en"]["text"] = new["data"]["en"]["text"].replace("Biochemstry", "Biochemistry")
    if b["block_type"] == "list":
        for lang in LANGS:
            new["data"][lang]["items"] = [item for item in new["data"][lang]["items"]]
            for wrong, right in TITLE_FIXES.items():
                for i, item in enumerate(new["data"][lang]["items"]):
                    if wrong in item:
                        assert item.count(wrong) == 1
                        new["data"][lang]["items"][i] = item.replace(wrong, right)
    if new != old:
        ops.append({"slug": SLUG, "order": order, "count": 1, "old": [old], "new": [new]})
Path("deploy/content/yillik-hisobot-2026-103/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ops), "ops:", [(o["order"], o["new"][0]["block_type"]) for o in ops])
