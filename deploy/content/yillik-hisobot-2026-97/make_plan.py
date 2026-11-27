"""Builds plan.json from the LIVE site's API (read-only, needs the network):  python3 deploy/content/yillik-hisobot-2026-97/make_plan.py"""
import json
import subprocess
from pathlib import Path


def get(url):
    return json.loads(subprocess.run(["curl", "-s", "--max-time", "90", url], capture_output=True, text=True, check=True).stdout)


def block(slug, order):
    return next(b for b in get("https://fermi.uz/api/v1/pages/%s/" % slug)["blocks"] if b["order"] == order)


FIXES = [
    ("ekofaol-yoshlar-loyihasi", 2, "uz",
     "vazirligining 2026-yil 6-apreldagi yuqorida koʻrsatilgan vazifalar ijrosini",
     "vazirligining 2026-yil 6-apreldagi 04/61-2241-sonli topshiriq xatida belgilangan yuqorida koʻrsatilgan vazifalar ijrosini"),
    ("ekofaol-yoshlar-loyihasi", 2, "ru",
     "В целях обеспечения исполнения вышеуказанных задач, 8 апреля 2026 года состоялась церемония открытия проекта «Экоактивная молодежь», организованная Министерством высшего образования, науки и инноваций.",
     "В целях обеспечения исполнения вышеуказанных задач, определённых в письме-поручении Министерства высшего образования, науки и инноваций от 6 апреля 2026 года № 04/61-2241, 8 апреля 2026 года состоялась церемония открытия проекта «Экоактивная молодежь»."),
    ("ekofaol-yoshlar-loyihasi", 2, "en",
     "In order to ensure the implementation of the above-mentioned tasks, the opening ceremony of the “Eco-Active Youth” project was held on April 8, 2026, organized by the Ministry of Higher Education, Science and Innovation.",
     "In order to ensure the implementation of the above-mentioned tasks set out in the assignment letter No. 04/61-2241 of the Ministry of Higher Education, Science and Innovation dated April 6, 2026, the opening ceremony of the “Eco-Active Youth” project was held on April 8, 2026."),
    ("ekofaol-yoshlar-loyihasi-navbatdagi-bosqich", 28, "uz", "loyihasi doirasida yakuni", "loyihasi doirasida yakuniy tadbir"),
    ("ekofaol-yoshlar-loyihasi-navbatdagi-bosqich", 9, "uz",
     "jajji bolajonlarni tabiatga mehr, ona zaminga ehtirom va kelajak avlod oldidagi masʻuliyatimiz ekanligini yana bir bor koʻrsatib berishdi",
     "jajji bolajonlarga tabiatga mehr, ona zaminga ehtirom va kelajak avlod oldidagi masʻuliyatimizni yana bir bor koʻrsatib berishdi"),
]
entries = []
for slug, order, lang, old, new in FIXES:
    b = block(slug, order)
    text = b["data"][lang]["text"]
    assert text.count(old) == 1, (slug, order, lang, "old text not found exactly once")
    entries.append({"slug": slug, "order": order, "lang": lang, "anchor": b["data"]["uz"]["text"][:30], "old": old, "new": new})
Path("deploy/content/yillik-hisobot-2026-97/plan.json").write_text(json.dumps(entries, ensure_ascii=False, indent=1), encoding="utf8")
print(len(entries), "corrections")
