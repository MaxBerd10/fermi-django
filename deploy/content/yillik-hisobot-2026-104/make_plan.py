"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-104/make_plan.py

Each fix is ONE text of ONE language of ONE block: {"slug", "order", "lang", "field", "old" (the whole text now), "new" (the whole text after), "why"}.
  "sub":  letter errors, the new text is the old one with the listed pieces replaced (each piece must occur exactly once);
  "full": a caption that was missing in a language (a copy of the Uzbek one) or stood under the wrong document: the new text is given whole."""
import json
import subprocess
from pathlib import Path

U = "ʻ"  # the Uzbek apostrophe
CONF = "ilmiy-konferensiyalar"
FIXES = {  # order -> lang -> ("sub", [(old, new), ...]) | ("full", new)
    2: {"ru": ("sub", [("Дос a тижения", "Достижения")]),
        "uz": ("full", "Zamonaviy tibbiyotning yuqumli kasalliklar epidemiologiyasini o%srganishdagi yutuqlari" % U),
        "en": ("full", "Advances of modern medicine in the study of the epidemiology of infectious diseases")},
    3: {"ru": ("sub", [("Актувльные", "Актуальные"), ("диангостики", "диагностики")]),
        "en": ("full", "Current issues in the diagnosis and treatment of coronavirus infection")},
    4: {"uz": ("sub", [("Dermatoveneralogiya", "Dermatovenerologiya")]),
        "ru": ("sub", [("новых технологии", "новых технологий")]),
        "en": ("sub", [("dermatoveneralogy", "dermatovenerology")])},
    5: {"ru": ("full", "Новые горизонты исследований в физиологии и патологии: современные подходы и перспективы"),
        "en": ("full", "New horizons of research in physiology and pathology: modern approaches and prospects")},
    7: {"ru": ("sub", [("Инновационный подходы", "Инновационные подходы")])},
    11: {"en": ("sub", [("diagnossis", "diagnosis")])},
    13: {"uz": ("sub", [("Dermatoveneralogiya", "Dermatovenerologiya"), ("davbolashda", "davolashda")]),
         "ru": ("sub", [("Пепспективы", "Перспективы")]),
         "en": ("sub", [("dermatoveneralogy", "dermatovenerology")])},
    14: {"en": ("sub", [("issies", "issues")])},
    15: {"ru": ("sub", [("иммунодефитцитов", "иммунодефицитов")])},
    16: {"uz": ("sub", [("Dermatoveneralogiya", "Dermatovenerologiya")]),
         "ru": ("sub", [("дерматоверенологии", "дерматовенерологии")])},
    17: {"uz": ("sub", [("kasallikalr", "kasalliklar")]), "ru": ("sub", [("внутренных", "внутренних")]), "en": ("sub", [("diseses", "diseases")])},
    18: {"uz": ("sub", [("ilniy", "ilmiy")]),
         "ru": ("sub", [("студентической", "студенческой"), ("научнойной", "научной"), ("Актуальной вопрочы, проплемы", "Актуальные вопросы, проблемы")]),
         "en": ("sub", [("II-nd", "II"), ("issies", "issues"), ("anf ", "and ")])},
    19: {"uz": ("sub", [("konfrensiyasi", "konferensiyasi")]), "ru": ("sub", [("научно- практическаяконференция", "научно-практическая конференция")])},
    20: {"ru": ("full", "Клинико-морфологические и физиологические исследования: инновационные решения в хирургии"),
         "en": ("full", "Clinical-morphological and physiological research: innovative solutions in surgery")},
}
PARAGRAPH_EN_6 = ("The role innovation in improving the quality of medicine education", "The role of innovation in improving the quality of medicine and education")


def blocks_of(slug):
    return {b["order"]: b for b in json.loads(subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/" % slug], capture_output=True, text=True, check=True).stdout)["blocks"]}


out = []
b = blocks_of(CONF)
for order, langs in FIXES.items():
    assert b[order]["block_type"] == "document", order
    for lang, (kind, value) in langs.items():
        old = b[order]["data"][lang]["caption"]
        if kind == "sub":
            new = old
            for a, c in value:
                assert new.count(a) == 1, (order, lang, a)
                new = new.replace(a, c)
        else:
            new = value
        assert new != old, (order, lang)
        out.append({"slug": CONF, "order": order, "lang": lang, "field": "caption", "old": old, "new": new})
assert b[6]["block_type"] == "paragraph"
old = b[6]["data"]["en"]["text"]
assert old.count(PARAGRAPH_EN_6[0]) == 1
out.append({"slug": CONF, "order": 6, "lang": "en", "field": "text", "old": old, "new": old.replace(*PARAGRAPH_EN_6)})

# kop-berilayotgan-savollar #11: the Uzbek "fermi.uz" link pointed to the page itself (ru and en point to https://fermi.uz)
k = blocks_of("kop-berilayotgan-savollar")
old = k[11]["data"]["uz"]["text"]
bad = "[fermi.uz](/blog/241/kop-berilayotgan-savollar)"
assert old.count(bad) == 1 and "[fermi.uz](https://fermi.uz)" in k[11]["data"]["ru"]["text"]
out.append({"slug": "kop-berilayotgan-savollar", "order": 11, "lang": "uz", "field": "text", "old": old, "new": old.replace(bad, "[fermi.uz](https://fermi.uz)")})

Path("deploy/content/yillik-hisobot-2026-104/plan.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf8")
print(len(out), "text fixes in", len({(o["slug"], o["order"]) for o in out}), "blocks")
