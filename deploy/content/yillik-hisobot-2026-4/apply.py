# Fourth part of the annual-report update: what the first three parts left out of the report (FJSTI_Yillik_hisobot_2026_yangi.pdf).
#
#   1. TEXT added to the nine report pages: "Kirish soʻzi" (the quotations of the President and the Minister of Health, p. 4-5),
#      "Rektor murojaati" (p. 6), the Scopus quartile table (p. 41), one sentence of p. 15 and the closing words and contacts (p. 75).
#   2. The report's PHOTOGRAPHS (98 pictures, p. 1-75) shown on the pages, each at the end of the section it belongs to. The pictures
#      are files of the website (/images/hisobot/pNN-k.webp), so no upload is needed. Decorative patterns were left out.
#   3. Eight apostrophes written as U+02BC in the first three pages are changed to the site's mark (U+02BB).
#
# Existing blocks keep their content; new blocks are inserted and the blocks of a page are renumbered (1, 2, 3 ...).
# SAFE BY DESIGN: dry (default) writes nothing and lists every insertion; every anchor must match exactly one heading, otherwise
# the script stops before writing; apply saves the old block order, the changed old texts and the ids of the new blocks to a
# backup file (a second apply is refused) and writes everything in one transaction; undo removes only the new blocks and puts
# the old order and texts back.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-4/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-4/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-4/apply.py
import json
import os
from datetime import datetime

from django.db import transaction
from django.utils import timezone

from apps.content.block_schemas import validate_block_data
from apps.content.models import ContentBlock, Page

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-4.json")
IMG_DIR = "/images/hisobot/"
OFFSET = 100000  # temporary shift of the old orders (the order is unique per page)
MARK, WRONG = chr(0x2BB), chr(0x2BC)  # the site's mark, and the look-alike that is replaced

IMAGES = {"p01-1": [960, 640], "p02-1": [960, 720], "p04-1": [960, 639], "p05-1": [960, 640], "p06-1": [960, 1225], "p07-1": [960, 639], "p08-1": [960, 640], "p08-2": [960, 640], "p08-3": [960, 639], "p08-4": [960, 640], "p11-1": [960, 678], "p11-2": [960, 678], "p11-3": [842, 595], "p11-4": [842, 595], "p11-5": [842, 595], "p12-1": [960, 639], "p12-2": [960, 639], "p14-1": [960, 540], "p14-2": [960, 639], "p14-3": [960, 720], "p14-4": [960, 720], "p15-1": [960, 639], "p15-2": [960, 639], "p16-1": [960, 639], "p16-2": [960, 639], "p16-3": [960, 639], "p16-4": [960, 639], "p19-1": [960, 639], "p19-2": [960, 639], "p20-1": [960, 639], "p20-2": [960, 639], "p20-3": [960, 639], "p20-4": [960, 639], "p21-1": [960, 640], "p21-2": [960, 640], "p22-1": [770, 750], "p23-1": [960, 1094], "p25-1": [540, 690], "p26-1": [675, 690], "p27-1": [655, 377], "p27-2": [668, 378], "p27-3": [960, 960], "p28-1": [837, 632], "p30-1": [960, 639], "p32-1": [960, 1094], "p33-1": [960, 639], "p33-2": [960, 639], "p33-3": [960, 540], "p37-1": [960, 1440], "p44-1": [960, 535], "p44-2": [960, 540], "p45-1": [960, 540], "p45-2": [960, 540], "p45-3": [960, 540], "p46-1": [960, 540], "p46-2": [960, 540], "p46-3": [960, 540], "p47-1": [900, 473], "p47-2": [900, 255], "p48-1": [960, 639], "p49-1": [900, 285], "p49-2": [900, 285], "p50-1": [960, 639], "p51-1": [900, 368], "p51-2": [440, 368], "p51-3": [440, 368], "p52-1": [860, 495], "p53-1": [960, 538], "p53-2": [960, 639], "p53-3": [960, 639], "p54-1": [822, 363], "p54-2": [960, 639], "p55-1": [600, 270], "p55-2": [600, 270], "p55-3": [581, 270], "p56-1": [770, 488], "p57-1": [960, 1094], "p60-1": [383, 353], "p60-2": [383, 353], "p60-3": [383, 353], "p64-1": [960, 535], "p64-2": [960, 535], "p64-3": [960, 535], "p70-1": [960, 535], "p71-1": [960, 394], "p71-2": [822, 487], "p71-3": [960, 568], "p71-4": [960, 568], "p72-1": [960, 614], "p72-2": [960, 614], "p72-3": [960, 614], "p72-4": [960, 613], "p72-5": [960, 613], "p72-6": [960, 613], "p74-1": [960, 535], "p74-2": [960, 535], "p74-3": [960, 535], "p75-1": [960, 678]}  # name -> [width, height]


def norm(text):
    return text.replace(WRONG, MARK)


def h(text):
    return ("heading", {"text": text})


def p(text):
    return ("paragraph", {"text": text})


def table(headers, rows):
    return ("table", {"headers": headers, "rows": rows})


def photos(names, alt):
    parts = []
    for i, name in enumerate(names, start=1):
        w, hh = IMAGES[name]
        label = alt if len(names) == 1 else "%s, %d" % (alt, i)
        parts.append('<p><img src="%s%s.webp" alt="%s" width="%d" height="%d" loading="lazy"></p>' % (IMG_DIR, name, label, w, hh))
    return ("raw_html", {"html": "".join(parts)})


# ---------------------------------------------------------------------------------------------------------------- the plan
# anchors: ("after", n)  after the old block with order n;  ("end_of", "heading")  end of the section of that heading (the
# heading is found by its beginning, exactly one match);  ("page_end",)
PLAN = {
    "yillik-hisobot-2026": [
        (("after", 1), [photos(["p01-1"], "Fargʻona jamoat salomatligi tibbiyot instituti")]),
        (
            ("after", 2),
            [
                h("Kirish soʻzi"),
                p("Davlat rahbariyati: «Sifatli taʻlim — kuchli iqtisodiyot va mamlakat kelajagining garovidir.» — Shavkat Mirziyoyev, Oʻzbekiston Respublikasi Prezidenti."),
                photos(["p04-1"], "Oʻzbekiston Respublikasi Prezidenti"),
                p("«Bugun tibbiyot sohasida qabul qilayotgan qarorlarimiz kelajak avlod qanday imkoniyatlarga ega boʻlishini belgilab beradi.» — Eldor Adilov, Oʻzbekiston Respublikasi Sogʻliqni saqlash vaziri."),
                photos(["p05-1"], "Oʻzbekiston Respublikasi Sogʻliqni saqlash vaziri"),
                h("Rektor murojaati"),
                photos(["p06-1"], "Akmal Sidikov, rektor"),
                p("Aziz talabalar! Akmal Sidikov, rektor, tibbiyot fanlari doktori, professor."),
                p("«Katta shifokor boʻlish yoʻli katta orzudan boshlanadi, ammo bu yoʻl bilim, mehnat, sabr va fidoyilik bilan bosib oʻtiladi.»"),
                p("Siz tanlagan kasb oddiy kasb emas. Shifokorlik inson hayoti, uning salomatligi va taqdiri bilan bogʻliq ulkan masʻuliyatdir. Har bir mashgʻulot, har bir amaliyot va har bir imkoniyatni kelajagingiz uchun muhim qadam sifatida qabul qiling."),
                p("Talabalik yillarini faqat auditoriya va imtihonlar bilan cheklab qoʻymang: ilmiy loyihalarda ishtirok eting, chet tillarini oʻrganing, sport va jamoat ishlarida faol boʻling."),
                p("Sizning har bir yutugʻingiz — institutimizning yutugʻi."),
            ],
        ),
        (("end_of", "Institut raqamlarda"), [photos(["p12-1", "p12-2"], "Institut raqamlarda")]),
        (
            ("page_end",),
            [
                p("«Dalillarga asoslangan tibbiyot — sifatli taʻlim, ishonchli ilm-fan va sogʻlom kelajak poydevori!»"),
                p("Aloqa: info@fermi.uz, +998 95 062-23-45, Fargʻona shahri, Yangi Turon koʻchasi, 2-a uy; fermi.uz, t.me/ferghana_medical_institute"),
                photos(["p02-1", "p75-1"], "Fargʻona jamoat salomatligi tibbiyot instituti"),
            ],
        ),
    ],
    "reyting-va-akkreditatsiya": [
        (("end_of", "Milliy va xalqaro reytinglar"), [photos(["p11-1"], "UI GreenMetric sertifikati")]),
        (("end_of", "Xalqaro akkreditatsiya"), [photos(["p11-2", "p11-3", "p11-4", "p11-5"], "Xalqaro akkreditatsiya sertifikatlari")]),
    ],
    "xalqaro-hamkorlik-va-investitsiyalar": [
        (("after", 1), [photos(["p32-1"], "Xalqaro hamkorlik")]),
        (("end_of", "BAA «Thumbay Group»"), [photos(["p20-1", "p20-2", "p20-3", "p20-4", "p33-1", "p33-2", "p33-3"], "Thumbay Fergana College of Medical Sciences")]),
    ],
    "ilmiy-va-innovatsion-faoliyat": [
        (("after", 1), [photos(["p37-1"], "Ilmiy faoliyat")]),
        (
            ("end_of", "Scopus bazasidagi ilmiy maqolalar"),
            [
                table(
                    ["Yil", "Q1", "Q2", "Q3", "Q4", "Kvartilsiz", "Jami"],
                    [
                        ["2023", "—", "—", "—", "—", "35", "43"],
                        ["2024", "5", "—", "8", "7", "22", "45"],
                        ["2025", "—", "13", "17", "43", "10", "86"],
                        ["2026", "8", "44", "19", "82", "5", "158"],
                        ["2027 (reja)", "14", "55", "30", "81", "5", "185"],
                    ],
                ),
                p("«—» belgisi hisobot diagrammasida koʻrsatilmagan qiymatni bildiradi. Kvartillar SCImago SJR 2025 koʻrsatkichlari asosida, har bir jurnalning eng yuqori toifasi boʻyicha. 2026-yil jami: bu jadvalda hisobotning kvartillar boʻlimidagi 158 ta, yuqoridagi jadvalda esa hisobotning Scopus boʻlimidagi 159 ta koʻrsatilgan."),
            ],
        ),
        (("end_of", "«IL»"), [photos(["p44-1", "p44-2"], "Institut laboratoriyasi")]),
        (("end_of", "Steril dorilar"), [photos(["p45-1", "p45-2", "p45-3"], "Steril dorilar ishlab chiqarish zonasi")]),
        (("end_of", "Simulyatsiya markazi"), [photos(["p46-1", "p46-2", "p46-3"], "Simulyatsiya markazi")]),
        (("end_of", "VR simulyatsiya markazi"), [photos(["p47-1", "p47-2"], "VR simulyatsiya markazi")]),
        (("end_of", "«FJSTI MedTech"), [photos(["p48-1"], "MedTech Innovation Hub")]),
        (("end_of", "Tibbiyot sohasida innovatsion"), [photos(["p49-1", "p49-2"], "Innovatsion tadqiqotlar ilmiy markazi")]),
    ],
    "suniy-intellekt-tizimlari": [
        (("after", 1), [photos(["p23-1"], "Sunʻiy intellekt tizimlari")]),
        (("end_of", "iMentor"), [photos(["p25-1"], "iMentor platformasi")]),
        (("end_of", "iTest"), [photos(["p26-1"], "iTest platformasi")]),
        (("end_of", "Situatsion markaz"), [photos(["p27-1", "p27-2", "p27-3"], "Situatsion markaz")]),
        (("end_of", "aiShifokor"), [photos(["p28-1"], "aiShifokor platformasi")]),
        (("end_of", "Soʻx modeli$"), [photos(["p30-1"], "Soʻx modeli")]),
    ],
    "2027-yil-vazifalari-batafsil": [
        (("end_of", "1. Stomatologiya"), [photos(["p64-1", "p64-2", "p64-3"], "Stomatologiya markazi (konsept vizualizatsiya)")]),
        (("end_of", "7. «Tibbiyotda"), [photos(["p70-1"], "«Tibbiyotda sunʻiy intellekt» dasturi")]),
        (("end_of", "8. «Fargʻona salomatlik"), [photos(["p71-1", "p71-2", "p71-3", "p71-4", "p72-1", "p72-2", "p72-3", "p72-4", "p72-5", "p72-6"], "«Fargʻona salomatlik bogʻi» (konsept vizualizatsiya)")]),
        (("end_of", "10. Zamonaviy talabalar"), [photos(["p74-1", "p74-2", "p74-3"], "Talabalar turar joyi (konsept vizualizatsiya)")]),
    ],
    "manaviy-marifiy-ishlar-va-olimpiadalar": [
        (("after", 1), [photos(["p50-1"], "Maʻnaviy-maʻrifiy ishlar")]),
        (("end_of", "Xalqaro fan olimpiadalari"), [photos(["p14-1", "p14-2", "p14-3", "p14-4"], "Xalqaro fan olimpiadalari")]),
        (("end_of", "Ijtimoiy hayot qisqa"), [photos(["p51-1", "p51-2", "p51-3"], "Ijtimoiy hayot")]),
        (("end_of", "Erishilgan yutuqlar"), [photos(["p52-1"], "Erishilgan yutuqlar")]),
        (("end_of", "Ijtimoiy hayotdan lavhalar"), [photos(["p53-1", "p53-2", "p53-3"], "Ijtimoiy hayotdan lavhalar")]),
        (("end_of", "Kitobxonlik haftaligi"), [photos(["p54-1", "p54-2"], "Kitobxonlik haftaligi")]),
        (("end_of", "Kasaba uyushma"), [photos(["p55-1", "p55-2", "p55-3"], "Kasaba uyushma qoʻmitasi")]),
        (("end_of", "Korrupsiyaga qarshi kurash"), [photos(["p56-1"], "Korrupsiyaga qarshi kurash")]),
    ],
    "moliya-oquv-uslubiy-ishlar-va-raqamlashtirish": [
        (("after", 1), [photos(["p07-1"], "Institut va taʻlim")]),
        (("end_of", "Moliyaviy oʻsish dinamikasi"), [photos(["p57-1"], "Moliyaviy faoliyat")]),
        (("end_of", "Ijtimoiy qoʻllab-quvvatlash"), [photos(["p60-1", "p60-2", "p60-3"], "Ijtimoiy qoʻllab-quvvatlash va moddiy-texnik baza")]),
        (
            ("end_of", "Oʻquv-uslubiy faoliyat raqamlarda"),
            [p("Talabalar nazariy bilimni real bemor holatlari asosidagi topshiriqlar orqali mustahkamlaydi."), photos(["p15-1", "p15-2"], "Oʻquv-uslubiy faoliyat")],
        ),
        (("end_of", "Amaliyotga yoʻnaltirilgan"), [photos(["p16-1", "p16-2", "p16-3", "p16-4", "p21-1", "p21-2"], "Amaliyotga yoʻnaltirilgan taʻlim va bitiruvchilar bandligi")]),
        (("end_of", "Axborot-resurs markazi"), [photos(["p19-1", "p19-2"], "Axborot-resurs markazi")]),
        (("end_of", "Raqamlashtirish"), [photos(["p22-1"], "Raqamlashtirish")]),
        (("end_of", "Institut tarixi"), [photos(["p08-1", "p08-2", "p08-3", "p08-4"], "Institut tarixi")]),
    ],
}


def block_data(kind, payload):
    return {lang: json.loads(json.dumps(payload)) for lang in ("uz", "ru", "en")}


def heading_text(block):
    return norm((block.data.get("uz") or {}).get("text", "")) if block.block_type == "heading" else None


def fix_marks(value):
    if isinstance(value, str):
        return value.replace(WRONG, MARK)
    if isinstance(value, list):
        return [fix_marks(v) for v in value]
    if isinstance(value, dict):
        return {k: fix_marks(v) for k, v in value.items()}
    return value


print("MODE:", MODE)

# ================================================================ undo
if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    with transaction.atomic():
        ContentBlock.objects.filter(pk__in=backup["created"]).delete()
        blocks = {b.pk: b for b in ContentBlock.objects.filter(pk__in=[int(k) for k in backup["orders"]])}
        for pk, b in blocks.items():  # out of the way first, then the old numbers
            b.order = OFFSET + b.order
            b.save(update_fields=["order"])
        for pk, b in blocks.items():
            b.order = backup["orders"][str(pk)]
            if str(pk) in backup["old_data"]:
                b.data = backup["old_data"][str(pk)]
            b.save(update_fields=["order", "data"])
        for pk, old_data in backup["old_data"].items():
            ContentBlock.objects.filter(pk=int(pk)).update(data=old_data)
        Page.objects.filter(pk__in=backup["pages"]).update(updated_at=timezone.now())
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: the new blocks are removed and the old order and texts are back. (backup kept under a new name)")
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

# ================================================================ plan
final = {}  # slug -> (page, [("old", block) | ("new", kind, payload)])
for slug, ops in PLAN.items():
    page = Page.objects.filter(slug=slug).first()
    if page is None:
        raise SystemExit("STOP: page '%s' not found. Nothing was changed." % slug)
    old = list(page.blocks.order_by("order"))
    if not old:
        raise SystemExit("STOP: page '%s' has no blocks. Nothing was changed." % slug)
    insert_after = {}  # index in `old` (-1 = before the first) -> [new blocks]
    for anchor, specs in ops:
        if anchor[0] == "after":
            matches = [i for i, b in enumerate(old) if b.order == anchor[1]]
            if len(matches) != 1:
                raise SystemExit("STOP: [%s] no block with order %d. Nothing was changed." % (slug, anchor[1]))
            idx = matches[0]
        elif anchor[0] == "page_end":
            idx = len(old) - 1
        else:
            wanted = norm(anchor[1])
            exact = wanted.endswith("$")  # "text$" = the whole heading, otherwise its beginning
            starts = [i for i, b in enumerate(old) if (heading_text(b) == wanted[:-1] if exact else (heading_text(b) or "").startswith(wanted))]
            if len(starts) != 1:
                raise SystemExit("STOP: [%s] the heading %r matches %d blocks, expected 1. Nothing was changed." % (slug, anchor[1], len(starts)))
            idx = starts[0]
            while idx + 1 < len(old) and old[idx + 1].block_type != "heading":
                idx += 1
        insert_after.setdefault(idx, []).extend(specs)
    seq = []
    for i, b in enumerate(old):
        seq.append(("old", b))
        for kind, payload in insert_after.get(i, []):
            validate_block_data(kind, block_data(kind, payload))
            seq.append(("new", kind, payload))
    final[slug] = (page, seq)

# the eight wrong marks of the first three pages
fixes = {}
for slug in ("yillik-hisobot-2026", "reyting-va-akkreditatsiya", "strategik-maqsadlar-2027"):
    fix_page = Page.objects.filter(slug=slug).first()
    if fix_page is None:
        raise SystemExit("STOP: page '%s' not found. Nothing was changed." % slug)
    for b in fix_page.blocks.all():
        fixed = fix_marks(b.data)
        if fixed != b.data:
            fixes[b.pk] = (b, fixed)

# ================================================================ show
total_new = 0
for slug, (page, seq) in final.items():
    news = [s for s in seq if s[0] == "new"]
    total_new += len(news)
    print("\n[%s] %d old blocks, %d new" % (slug, len(seq) - len(news), len(news)))
    for pos, s in enumerate(seq, start=1):
        if s[0] == "new":
            kind, payload = s[1], s[2]
            what = payload.get("text") or payload.get("html", "")[:60] or str(payload)[:60]
            if kind == "raw_html":
                files = [part.split('"')[0].split("/")[-1].replace(".webp", "") for part in payload["html"].split('src="')[1:]]
                what = "%d photo(s): %s" % (len(files), ", ".join(files))
            elif kind == "table":
                what = "table: " + ", ".join(payload["headers"])
            print("   + #%d %s: %s" % (pos, kind, what[:110]))
print("\n%d new blocks in %d pages; %d old blocks get the standard apostrophe." % (total_new, len(final), len(fixes)))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

# ================================================================ apply
os.makedirs(BACKUP_DIR, exist_ok=True)
backup = {
    "created_at": datetime.now().isoformat(),
    "pages": [page.pk for page, _ in final.values()] + [b.page_id for b, _ in fixes.values()],
    "orders": {str(b.pk): b.order for _, (page, seq) in final.items() for s in seq if s[0] == "old" for b in [s[1]]},
    "old_data": {str(pk): b.data for pk, (b, fixed) in fixes.items()},
    "created": [],
}
with transaction.atomic():
    for slug, (page, seq) in final.items():
        olds = [s[1] for s in seq if s[0] == "old"]
        for b in olds:  # out of the way first (the order is unique per page)
            b.order = OFFSET + b.order
            b.save(update_fields=["order"])
        for number, s in enumerate(seq, start=1):
            if s[0] == "old":
                b = s[1]
                b.order = number
                if b.pk in fixes:
                    b.data = fixes[b.pk][1]
                b.save(update_fields=["order", "data"])
            else:
                nb = ContentBlock.objects.create(page=page, order=number, block_type=s[1], data=block_data(s[1], s[2]))
                backup["created"].append(nb.pk)
        page.save()
    for pk, (b, fixed) in fixes.items():  # pages that only get the standard apostrophe
        if not any(s[0] == "old" and s[1].pk == pk for _, seq in final.values() for s in seq):
            b.data = fixed
            b.save(update_fields=["data"])
            b.page.save()
    json.dump(backup, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
print("DONE: %d new blocks in %d pages. To put everything back: MODE=undo with the same command." % (len(backup["created"]), len(final)))
print("(the site shows it within about 10 minutes at most)")
