"""plan.json of script 119 (written by hand from the live page, checked 2026-11-27):

prezident-farmon-va-qarorlari (a page of file cards): the order was LEX.UZ x5 (#1-5), PDF x5 (#6-10), LEX.UZ (#11, "Aholini soglom ovqatlanishini taminlash togrisida"), PDF (#12, the 3 December 2020
decree of the President as a document block): the two kinds were mixed. Now the LEX.UZ cards stand together (#1-5 and the one from #11), then all the PDFs (#6-10 and the decree), i.e. the block #11 moves up
to place #6, #6-#10 move down by one, #12 stays last. The blocks keep their ids and their text: only their order changes. "sig" = the beginning of the Uzbek text of the block (or its document id)."""
import json
from pathlib import Path

plan = {
    "slug": "prezident-farmon-va-qarorlari",
    "moves": [  # block now at `old` goes to `new`
        {"old": 11, "new": 6, "sig": "[Aholini sogʻlom ovqatlanishini taʻminlash toʻgʻrisida]"},
        {"old": 6, "new": 7, "sig": "[Tibbiyot muassasalarini farmatsevtika mahsulotlari"},
        {"old": 7, "new": 8, "sig": "[Sogʻliqni saqlash sohasida ixtisoslashtirilgan tibbiy yordam"},
        {"old": 8, "new": 9, "sig": "[Sogʻliqni saqlash sohasini kompleks rivojlantirishga"},
        {"old": 9, "new": 10, "sig": "[Tibbiy profilaktika ishlari samaradorligini"},
        {"old": 10, "new": 11, "sig": "[Sogʻlom turmush tarzini keng tatbiq etish"},
    ],
    "unmoved_check": {"12": "document"},
}
Path("deploy/content/yillik-hisobot-2026-119/plan.json").write_text(json.dumps(plan, ensure_ascii=False, indent=1), encoding="utf8")
print(len(plan["moves"]), "moves")
