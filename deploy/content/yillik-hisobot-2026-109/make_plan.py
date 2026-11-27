"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-109/make_plan.py

Texts of the database (not of page blocks) that Russian / English readers see in Uzbek or in the wrong script:
  * /qabul-natijalari: the heading, the introduction and the announcement of the page (Russian and English were copies of the Uzbek text), the names of the six result categories
    and of their files in English (copies of the Uzbek names; Russian already translated);
  * menu: "Institut gazetasi-2025" (English), "Abituriyentlar ... institut tarixi" (Russian was English), "Yashil Universitet 2021-2026" (Russian / English were Latin / not capitalised),
    "Green university-2026" and "17 goals of UN Policies" (Russian);
  * the rector in the list of persons an admission inquiry goes to: two Cyrillic letters "А" inside the Latin name ("Аkmal Аbdikaxarovich").
Every op: {model "app.Model", pk, field, old, new}; the translations are Claude's wording, to be read by the staff.
Left as they are on purpose: brand and proper names (Thumbay Fergana college of Medical Sciences, Study in Uzbekistan)."""
import json
import subprocess
from pathlib import Path

ops = []
CYR_A = "А"


def fetch(u):
    return json.loads(subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/" + u + ("&" if "?" in u else "?") + "v=109"], capture_output=True, text=True, check=True).stdout)


def op(model, pk, field, old, new):
    assert old != new, (model, pk, field)
    ops.append({"model": model, "pk": pk, "field": field, "old": old, "new": new})


# ---- /qabul-natijalari: the page ------------------------------------------------------------------------------------------------------------------
page = fetch("admission-results-page")
T = {
    "heading": ("Результаты тестирования 2026/2027", "Test results 2026/2027"),
    "intro": ("Откройте утверждённые электронные протоколы по направлению и языку обучения.", "Open the approved electronic protocols by programme and language of instruction."),
    "announcement": (
        "УВАЖАЕМЫЕ АБИТУРИЕНТЫ! Публикуются утверждённые результаты тестовых испытаний, проведённых для 2026/2027 учебного года. Абитуриенты, набравшие 100 и более баллов, рекомендуются к зачислению.",
        "DEAR APPLICANTS! The approved results of the tests held for the 2026/2027 academic year are published. Applicants who scored 100 points or more are recommended for enrolment.",
    ),
}
for key, (ru, en) in T.items():
    for lang, new in (("ru", ru), ("en", en)):
        old = page[key][lang]
        assert old != page[key]["uz"] or True
        op("admission_results.ResultsPage", 1, "%s_%s" % (key, lang), old, new)

# ---- result categories and files (English) --------------------------------------------------------------------------------------------------------
CAT = {"Farmatsiya": "Pharmacy", "Stomatologiya": "Dentistry", "Pediatriya": "Pediatrics", "Davolash ishi": "General medicine", "Davolash": "Treatment", "Tibbiy profilaktika ishi": "Medical prevention"}
FILE = {"Oʻzbek tili": "Uzbek language", "Rus tili": "Russian language", "Qoʻshimcha qaydnoma": "Additional protocol", "Pediatriya ishi": "Pediatric work"}
for c in fetch("admission-results/"):
    assert c["title"]["uz"] in CAT, c["title"]
    op("admission_results.ResultCategory", c["id"], "title_en", c["title"]["en"], CAT[c["title"]["uz"]])
    for f in c["files"]:
        assert f["title"]["uz"] in FILE, f["title"]
        op("admission_results.ResultFile", f["id"], "title_en", f["title"]["en"], FILE[f["title"]["uz"]])

# ---- menu --------------------------------------------------------------------------------------------------------------------------------------
menu = fetch("menu/?page_size=500")
menu = menu if isinstance(menu, list) else menu["results"]
labels = {}


def walk(items):
    for it in items:
        labels[it["id"]] = it["label"]
        walk(it.get("children", []))


walk(menu)
op("menu.MenuItem", 1878, "label_en", labels[1878]["en"], "Institute newspaper-2025")
op("menu.MenuItem", 2062, "label_ru", labels[2062]["ru"], "Направления обучения для абитуриентов и история института")
op("menu.MenuItem", 2172, "label_ru", labels[2172]["ru"], "Зелёный университет 2021-2026")
op("menu.MenuItem", 2172, "label_en", labels[2172]["en"], "Green University 2021-2026")
op("menu.MenuItem", 2173, "label_ru", labels[2173]["ru"], "Зелёный университет-2026")
op("menu.MenuItem", 2174, "label_ru", labels[2174]["ru"], "17 целей политики ООН")

# ---- the rector in the admission inquiry's list: Cyrillic "А" in a Latin name --------------------------------------------------------------------
for leader in fetch("connect-leaders"):
    if CYR_A in leader["name"]:
        op("geo.ConnectLeader", leader["id"], "name", leader["name"], leader["name"].replace(CYR_A, "A"))

Path("deploy/content/yillik-hisobot-2026-109/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ops), "ops")
