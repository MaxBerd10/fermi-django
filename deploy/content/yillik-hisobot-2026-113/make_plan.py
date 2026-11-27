"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-113/make_plan.py

vrachlar-malakasini-oshirish-sertifikati (certificates of the doctors' further-training courses): the whole page was Uzbek in Russian and English. Russian: the 102 names are written in Cyrillic
(translit.py: the usual way Uzbek names are written in Russian; the staff should read them), the column headers and the four course headings are Russian. English: the column headers and the headings
are English; the names stay Latin. Diploma and certificate numbers, the picture and the Uzbek text stay as they are. Every op replaces the one block at `order` ("old": what it is now, "new")."""
import copy
import json
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from translit import name_ru  # noqa: E402

SLUG = "vrachlar-malakasini-oshirish-sertifikati"
for _ in range(5):
    text = subprocess.run(["curl", "-s", "--max-time", "90", "https://fermi.uz/api/v1/pages/%s/?v=113" % SLUG], capture_output=True, text=True).stdout
    try:
        blocks = {b["order"]: b for b in json.loads(text)["blocks"]}
        break
    except ValueError:
        time.sleep(3)

HEAD_RU = ["№", "Ф.И.О.", "№ диплома", "Номер сертификата"]
HEAD_EN = ["№", "Full name", "Diploma No.", "Certificate No."]
HEADINGS = {
    3: ("Направление «Клиническая ИФА, ИХЛА и ПЦР-диагностика: правильная оценка результатов анализов», 144 часа, UMO",
        "Direction “Clinical ELISA, CLIA and PCR diagnostics: correct evaluation of test results”, 144 hours, UMO"),
    5: ("(144 часа) UMO, направление «Оториноларингология», с 03.04.2026 по 30.04.2026",
        "(144 hours) UMO, direction “Otorhinolaryngology”, from 03.04.2026 to 30.04.2026"),
    7: ("(144 часа) UMO, направление «Общая эндокринология», с 06.04.2026 по 02.05.2026",
        "(144 hours) UMO, direction “General endocrinology”, from 06.04.2026 to 02.05.2026"),
    9: ("(144 часа) MMO, направление «Неврология: современные методы диагностики, реабилитации и лечения», с 07.04.2026 по 03.05.2026",
        "(144 hours) MMO, direction “Neurology: modern methods of diagnosis, rehabilitation and treatment”, from 07.04.2026 to 03.05.2026"),
}
ops = []
for order, block in sorted(blocks.items()):
    old = {"block_type": block["block_type"], "data": block["data"]}
    new = copy.deepcopy(block["data"])
    if block["block_type"] == "table":
        assert new["uz"]["headers"] == ["№", "F.I.SH", "№diplom", "Sertifikat raqami"], new["uz"]["headers"]
        for lang, head in (("ru", HEAD_RU), ("en", HEAD_EN)):
            new[lang]["headers"] = head
        new["ru"]["rows"] = [[r[0], name_ru(r[1])] + r[2:] for r in new["uz"]["rows"]]
        assert len(new["ru"]["rows"]) == len(block["data"]["ru"]["rows"]) == len(block["data"]["en"]["rows"])
    elif block["block_type"] == "heading":
        new["ru"]["text"], new["en"]["text"] = HEADINGS[order]
    else:
        continue
    ops.append({"slug": SLUG, "order": order, "count": 1, "old": [old], "new": [{"block_type": block["block_type"], "data": new}]})

Path("deploy/content/yillik-hisobot-2026-113/plan.json").write_text(json.dumps(ops, ensure_ascii=False, indent=1), encoding="utf8")
print(len(ops), "ops")
