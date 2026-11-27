"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-124/make_plan.py

Answers of the staff questions (the user, 2026-11-28: "2024, solve the rest"):
  * raqamli-talim-texnologiyalari-markazi #2: "the order of the Ministry of Higher Education, Science and Innovation of 25.06.2001 No. 23" (the ministry did not exist in 2001): the year is 2024, in all three
    languages (the other date of the text, the Cabinet of Ministers' resolution of 23.05.2001, is right and stays);
  * the page of the department of communal hygiene (page slug department-6) #30: the heading of the entry of the deputy dean Atadjanova Dilfuza: in Uzbek the name was broken by spaces
    ("A tadjanova Dilfuza Sharobidinov na", so the page did not take it for a name and the entry was lost from the staff tab), in English it was the name of ANOTHER person (Saidova Sohibakhon Abrorjon kizi, the
    name of #36): both read "Atadjanova Dilfuza Sharobidinovna" now (the Russian text already did).
Every op: {slug, order, lang, field, old, new}."""
import json
import re
import subprocess
import time
from pathlib import Path

ops = []


def api(path):
    for _ in range(5):
        text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/" + path + ("&" if "?" in path else "?") + "v=124"], capture_output=True, text=True).stdout
        try:
            return json.loads(text)
        except ValueError:
            time.sleep(3)
    raise SystemExit("API did not answer: " + path)


page = api("pages/raqamli-talim-texnologiyalari-markazi/")
block = {b["order"]: b for b in page["blocks"]}[2]
DATE = {"uz": "25.06.2001", "ru": "25.06.2001", "en": "June 25, 2001"}  # the English text writes the date in words
for lang in ("uz", "ru", "en"):
    old = block["data"][lang]["text"]
    assert old.count(DATE[lang]) == 1, (lang, old.count(DATE[lang]))
    ops.append({"slug": "raqamli-talim-texnologiyalari-markazi", "order": 2, "lang": lang, "field": "text", "old": old, "new": old.replace(DATE[lang], DATE[lang].replace("2001", "2024"))})

dep = api("departments/kommunal-va-mehnat-gigienasi-kafedrasi/")
dep = dep.get("data", dep)["page"]
assert dep["slug"] == "department-6"
b30 = {b["order"]: b for b in dep["blocks"]}[30]
NAME = "Atadjanova Dilfuza Sharobidinovna"
assert re.sub(r"\s+", "", b30["data"]["uz"]["text"]) == NAME.replace(" ", ""), b30["data"]["uz"]["text"]
assert b30["data"]["en"]["text"].startswith("Saidova Sohibakhon")
assert b30["data"]["ru"]["text"] == "Атаджанова Дилфуза Шаробидиновна"
for lang in ("uz", "en"):
    ops.append({"slug": "department-6", "order": 30, "lang": lang, "field": "text", "old": b30["data"][lang]["text"], "new": NAME})

Path("deploy/content/yillik-hisobot-2026-124/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
for o in ops:
    print(o["slug"], o["order"], o["lang"], "|", o["old"][-70:].replace("\n", " "), "->", o["new"][-70:].replace("\n", " "))
