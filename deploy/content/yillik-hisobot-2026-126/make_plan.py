"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-126/make_plan.py

Short blocks of the department pages (the user, 2026-11-28: "do 3"). An audit of 1261 short texts (headings, names, list items) of the 30 department pages in uz/ru/en (the same Uzbek text on
several pages must have the same ru/en; names must look like names in all three languages; a text must not be the translation of ANOTHER block) found:
  (a) wrong ru/en texts (they belong to another block of the page; the Uzbek text is the master):
      department-29 #31 en: a name + 'Department Head (PhD)' instead of the Uzbek 'Xalq tabobati va farmakologiya kafedrasi dotsenti';
      department-29 #50 en: 'Research work of the Department ...' instead of 'Oʻqitish tizimi quyidagi tasdiqlangan hujjatlar boʻyicha olib boriladi:';
      department-20 #78 en: a person's name instead of 'Dissertatsiya himoyalari';
      department-19 #46 ru: 'technical resources' instead of the same 'approved documents' line (the Russian text of department-29 #50 is the model);
  (b) Uzbek typos (a space inside a word, or words glued): 'kafedra a ssistenti', 'KAFEDRA OC HIQ DARSLARI', 'SIDDIQOVObidjonSiddiqovich', 'Max buba', 'D exkanova Nigora Namanjanovna .'
      (the staff tab of the Uzbek page lost the three names: a name is taken for a name only when its words are separate and capitalised).
Every op: {slug, order, lang, field, old, new}."""
import json
import subprocess
import time
from pathlib import Path

FIXES = [
    # (page slug, order, lang, what the text is now (start), the new text)
    ("department-29", 31, "en", "KHOLIKOVA OYISTAKHON YULDASHEVNA", "Associate professor of the Department of Traditional Medicine and Pharmacology"),
    ("department-29", 50, "en", "Research work of the Department of Traditional Medicine and Pharmacology", "The teaching system is carried out on the basis of the following approved documents:"),
    ("department-20", 78, "en", "Zhurava Mastura Tozhihakimkizi", "Dissertation Defenses"),
    ("department-19", 46, "ru", "В процессе обучения используется следующее техническое обеспечение:", "Система обучения ведётся на основе следующих утверждённых документов:"),
    ("department-11", 40, "uz", "kafedra a ssistenti", "kafedra assistenti"),
    ("department-11", 44, "uz", "kafedra a ssistenti", "kafedra assistenti"),
    ("department-11", 48, "uz", "kafedra a ssistenti", "kafedra assistenti"),
    ("department-3", 30, "uz", "KAFEDRA OC HIQ DARSLARI", "KAFEDRA OCHIQ DARSLARI"),
    ("department-17", 41, "uz", "KAFEDRA OC HIQ DARSLARI", "KAFEDRA OCHIQ DARSLARI"),
    ("department-20", 96, "uz", "KAFEDRA OC HIQ DARSLARI", "KAFEDRA OCHIQ DARSLARI"),
    ("department-35", 54, "uz", "KAFEDRA OC HIQ DARSLARI", "KAFEDRA OCHIQ DARSLARI"),
    ("department-26", 6, "uz", "SIDDIQOVObidjonSiddiqovich", "SIDDIQOV Obidjon Siddiqovich"),
    ("department-4", 21, "uz", "Mamatqulova Max buba Tojalievna", "Mamatqulova Maxbuba Tojalievna"),
    ("department-7", 12, "uz", "D exkanova Nigora Namanjanovna .", "Dexkanova Nigora Namanjanovna."),
]


def api(path):
    for _ in range(5):
        text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/" + path + ("&" if "?" in path else "?") + "v=126"], capture_output=True, text=True).stdout
        try:
            return json.loads(text)
        except ValueError:
            time.sleep(3)
    raise SystemExit("API did not answer: " + path)


slugs = [d["slug"] for d in api("departments/")]
wanted = {f[0] for f in FIXES}
pages = {}
for s in slugs:
    if len(pages) == len(wanted):
        break
    d = api("departments/%s/" % s)
    d = d.get("data", d)["page"]
    if d["slug"] in wanted:
        pages[d["slug"]] = {b["order"]: b for b in d["blocks"]}
    time.sleep(0.5)
ops = []
for slug, order, lang, start, new in FIXES:
    block = pages[slug][order]
    old = block["data"][lang]["text"]
    assert old.startswith(start) and block["block_type"] == "paragraph", (slug, order, lang, old[:60])
    ops.append({"slug": slug, "order": order, "lang": lang, "field": "text", "old": old, "new": new})
Path("deploy/content/yillik-hisobot-2026-126/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
for o in ops:
    print(o["slug"], o["order"], o["lang"], "|", o["old"][:50], "->", o["new"][:60])
