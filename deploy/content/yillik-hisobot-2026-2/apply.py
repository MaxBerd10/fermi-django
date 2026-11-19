# Second part of the annual-report update (FJSTI_Yillik_hisobot_2026_yangi.pdf):
#
#   1. Page "Doktorantura maʻlumotlari" (uz, ru, en): 42 base doctoral students / 204 independent applicants
#      -> 40 / 255 (report p. 39, 2026).
#   2. Home page "Bizning loyihalar": the "Teletibbiyot" card becomes "iShifo" (the telemedicine platform, link ishifo.uz) and a
#      new "Soʻx modeli" card is added (opens the page /sox-modeli).
#   3. Three new CMS pages (editable in the admin panel under "Sahifalar"), each with an entry in the menu
#      Institut -> Institut xaqida:  "Yillik hisobot 2026" (key figures + the report PDF), "Reyting va akkreditatsiya",
#      "Strategik maqsadlar — 2027". Their Russian and English text is a COPY of the Uzbek text (the admin panel marks such
#      blocks "needs translation"); nothing was machine-translated. Only the three menu labels have Russian/English names.
#
# NOT changed: the number of faculties (the report says 5 and does not name the fifth), "Xorijiy boʻlim" (its "100+ foreign
# students" is the department's own figure, not the institute's 1 641).
#
# SAFE BY DESIGN: dry (default) writes nothing and shows everything it would do; every replacement must find its text EXACTLY
# once; apply first saves the old values and the ids of what it creates to a backup file (a second apply is refused) and
# writes everything in one transaction; undo restores the old values and removes only what apply created.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-2/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-2/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-2/apply.py
import json
import os
from datetime import datetime

from django.db import transaction

from apps.content.block_schemas import validate_block_data
from apps.content.models import ContentBlock, Page
from apps.menu.models import MenuItem
from apps.site_settings.models import HomeItem

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-2.json")
PDF_URL = "/files/FJSTI-Yillik-hisobot-2026.pdf"

# ---------------------------------------------------------------- 1. doctoral page
DOCTORAL_SLUG = "doktorantura-malumotlari"
DOCTORAL = {
    "uz": ("Institutda 42 nafar tayanch doktorant, 204&nbsp;nafar mustaqil izlanuvchi", "Institutda 40 nafar tayanch doktorant, 255&nbsp;nafar mustaqil izlanuvchi"),
    "ru": ("42 базовых докторанта и 204 самостоятельных соискателя", "40 базовых докторантов и 255 самостоятельных соискателей"),
    "en": ("42 basic doctoral students and 204 independent applicants", "40 basic doctoral students and 255 independent applicants"),
}

# ---------------------------------------------------------------- 2. home project cards
SOX_CARD = {
    "title_uz": "Soʻx modeli",
    "title_ru": "Модель «Сох»",
    "title_en": "Soʻx model",
    "url": "/sox-modeli",
    "icon": "ri-heart-pulse-line",
    "image_path": "/images/projects/sox-modeli.jpg",
}

# ---------------------------------------------------------------- 3. new pages
PARENT_LABEL = "Institut xaqida"
GRANDPARENT_LABEL = "Institut"


def h(text):
    return ("heading", {"text": text})


def p(text):
    return ("paragraph", {"text": text})


def ul(*items):
    return ("list", {"items": list(items)})


def table(headers, rows):
    return ("table", {"headers": headers, "rows": rows})


def pdf_link(title):
    return ("raw_html", {"html": '<p><a href="%s">%s</a></p>' % (PDF_URL, title)})


PAGES = [
    {
        "slug": "yillik-hisobot-2026",
        "title": {"uz": "Yillik hisobot 2026", "ru": "Годовой отчёт 2026", "en": "Annual report 2026"},
        "blocks": [
            p("Fargʻona jamoat salomatligi tibbiyot institutining 2026-yildagi taʻlim, ilm-fan, innovatsiya va xalqaro hamkorlik natijalari haqidagi yillik hisobotining asosiy koʻrsatkichlari."),
            pdf_link("Yillik hisobot 2026 (PDF)"),
            h("2026-yil bir qarashda"),
            table(
                ["Koʻrsatkich", "Qiymat"],
                [
                    ["Talabalar", "7 950+"],
                    ["Professor-oʻqituvchilar", "494"],
                    ["UI GreenMetric jahon reytingida", "TOP 700"],
                    ["Xorijiy talabalarni qamrab olgan tibbiyot yoʻnalishidagi institutlar orasida", "TOP 2"],
                    ["2026-yil umumiy mablagʻi", "190 mlrd soʻm"],
                    ["Jalb etilgan investitsiya va grantlar", "8 mln USD"],
                    ["Hamkor xorijiy universitetlar", "38"],
                    ["Fan olimpiadalari gʻoliblari", "84"],
                ],
            ),
            h("Institut raqamlarda"),
            ul("29 kafedra", "10 ta taʻlim yoʻnalishi", "13 magistratura mutaxassisligi", "32 doktorantura", "45 ordinatura"),
            h("Kadrlar salohiyati"),
            ul(
                "Jami tarkib: 494 nafar professor-oʻqituvchi",
                "Fan doktorlari (DSc): 40",
                "PhD, fan nomzodlari: 201",
                "Boshqa professor-oʻqituvchilar: 253",
                "241 nafar professor-oʻqituvchi ilmiy darajaga ega (DSc va PhD)",
            ),
            h("Taʻlim va amaliyot"),
            ul(
                "255 ta mutaxassislik fanlari dasturi, 350 ta amaliyot va laboratoriya darsi",
                "20 ta fan TOP-300 universitetlar oʻquv dasturlari asosida oʻqitiladi",
                "1 700 ta yangi oʻquv-uslubiy material",
                "305+ hamkor tibbiyot muassasasi, 1 750 ta amaliyot shartnomasi",
                "3 000 nafar talaba AQShning tibbiy litsenziyalash imtihoni (USMLE) dasturida oʻqitilmoqda",
                "Bitiruvchilarning 91 foizi ish bilan taʻminlangan (2025/2026-oʻquv yili)",
            ),
            h("Sunʻiy intellekt tizimlari"),
            p("Institutda ishlab chiqilgan va joriy etilgan platformalar yagona raqamli ekotizimni tashkil etadi."),
            ul(
                "iMentor — sunʻiy intellekt asosidagi taʻlim tizimi",
                "iTest — onlayn imtihon platformasi",
                "Situatsion markaz — sunʻiy intellekt asosidagi kamera nazorati",
                "aiShifokor — klinik qarorni qoʻllab-quvvatlovchi platforma",
                "iShifo — masofaviy tibbiyot (telemeditsina) platformasi",
                "Soʻx modeli — tuman miqyosida amaliy joriy etish",
            ),
            h("Xalqaro hamkorlik va investitsiyalar"),
            ul(
                "38 ta hamkor xorijiy universitet, 10 ta xalqaro tashkilot, 9 ta hamkor davlat",
                "2026-yil yanvar–iyul oylarida 8 mln USD mablagʻ jalb etildi; 13 ta xorijiy hamkor yoki donor bilan kelishuvga erishildi",
                "118 nafar xorijiy talaba qabul qilindi (jami 1 641 nafar)",
            ),
            h("Ilmiy va innovatsion faoliyat"),
            ul(
                "Scopus bazasida 340 ta ilmiy nashr (2021–2026)",
                "Intellektual mulk guvohnomalari: 113 tadan (2021) 297 tagacha (2026)",
                "Ilmiy salohiyat: 11,5 foizdan (2021) 32,8 foizgacha (2026)",
                "295 nafar izlanuvchi ilmiy tadqiqot olib bordi (255 mustaqil izlanuvchi va 40 tayanch doktorant)",
                "13 ta ixtisoslashtirilgan boʻlinma va korxona (spin-off) tashkil etildi",
            ),
            h("Maʼnaviy-maʼrifiy ishlar"),
            ul(
                "113 ta muntazam tadbir: ekologik aksiyalar, qon donorligi, sahna sanʼati, kasbiy va shaxsiy rivojlanish treninglari",
                "Respublika va viloyat tanlovlarida 4 ta yutuq",
                "Korrupsiyaga qarshi kurash: 26 ta davra suhbati, seminar va uchrashuv, 3 700+ ishtirokchi",
            ),
            h("Moliyaviy faoliyat"),
            ul(
                "2026-yil umumiy mablagʻi 190 mlrd soʻm (2021-yildan 326 foizga oʻsgan)",
                "Toʻlov-kontrakt mablagʻlari 75,3 foiz, byudjetdan ajratilgan mablagʻ 24,7 foiz",
            ),
            p("Manba: Fargʻona jamoat salomatligi tibbiyot instituti, Yillik hisobot 2026."),
        ],
    },
    {
        "slug": "reyting-va-akkreditatsiya",
        "title": {"uz": "Reyting va akkreditatsiya", "ru": "Рейтинги и аккредитация", "en": "Rankings and accreditation"},
        "blocks": [
            p("Institutning milliy va xalqaro reytinglardagi oʻrni hamda xalqaro akkreditatsiyadan oʻtgan taʻlim yoʻnalishlari (Yillik hisobot 2026 maʼlumotlari)."),
            h("Milliy va xalqaro reytinglar"),
            table(
                ["Reyting", "Natija", "Izoh"],
                [
                    ["NQAAE milliy reytingi", "Tibbiyot toifasidagi oliygohlar orasida 2-oʻrin", "Ball: 2,83"],
                    ["UI GreenMetric World University Rankings, 2025", "Jahonda 700-oʻrin, Oʻzbekistonda 19-oʻrin", "Jami ball: 6 210"],
                    ["Round University Ranking (RUR), 2023", "Oʻzbekistonda 9-oʻrin", "Xalqaro reyting"],
                ],
            ),
            h("Xalqaro akkreditatsiya"),
            table(
                ["Taʻlim yoʻnalishi", "Agentlik", "Muddati"],
                [
                    ["Davolash ishi", "ECAQA", "2023–2028"],
                    ["Pediatriya ishi", "IAAR", "5 yilga, 2030-yilgacha"],
                    ["Stomatologiya", "IAAR", "3 yilga, 2028-yilgacha"],
                    ["Farmatsiya", "IAAR", "3 yilga, 2028-yilgacha"],
                ],
            ),
            p("Sertifikatlar bilan «Institut sertifikatlari» va «Institut xalqaro akkreditatsiyasi» sahifalarida tanishish mumkin."),
            h("Rejalar"),
            ul(
                "2027-yil aprel: Buyuk Britaniya QAA xalqaro institutsional akkreditatsiyasidan oʻtish",
                "2027-yil: UI GreenMetric reytingida TOP 500, QS reytingiga maʼlumot topshirish",
                "2028-yil: THE Impact Rankings reytingiga kirish",
                "2029-yil: QS Asia reytingiga kirish",
                "2030-yil: QS, THE va GreenMetric reytinglarining uchalasiga kirish",
            ),
        ],
    },
    {
        "slug": "strategik-maqsadlar-2027",
        "title": {"uz": "Strategik maqsadlar — 2027", "ru": "Стратегические цели — 2027", "en": "Strategic goals — 2027"},
        "blocks": [
            p("Institutning 2027-yil ustuvor vazifalari: xalqaro akkreditatsiya, reytinglar, yangi markazlar va ilmiy salohiyatni oshirish (Yillik hisobot 2026 maʼlumotlari)."),
            h("2027-yil ustuvor vazifalari"),
            table(
                ["№", "Vazifa", "Muddat"],
                [
                    ["1", "Zamonaviy stomatologiya va yuz-jagʻ jarrohligi markazini tashkil etish", "2028-yil sentabr"],
                    ["2", "Buyuk Britaniya QAA akkreditatsiyasidan oʻtish", "2027-yil aprel"],
                    ["3", "QS, THE va GreenMetric reytinglariga kirish", "2030-yil sentabr"],
                    ["4", "PhD va DSc himoya qilgan tadqiqotchilar sonini 200 taga yetkazib, ilmiy salohiyatni 70 foizga oshirish", "2030-yil aprel"],
                    ["5", "Erasmus+ doirasida «Sunʻiy intellekt hamjamiyati» xalqaro loyihasida ishtirok etish (Singidunum universiteti, Janubiy Qozogʻiston tibbiyot akademiyasi, Turkiya Transport va infratuzilma vazirligi bilan)", "2027-yil oktabr"],
                    ["6", "10 ta bakalavriat va magistratura taʼlim dasturini QS va THE TOP-300 universitetlari dasturlariga moslashtirish", "2027-yil aprel"],
                    ["7", "«Tibbiyotda sunʻiy intellekt» bakalavriat va magistratura taʼlim dasturlarini yaratish", "2027-yil aprel — 2030-yil aprel"],
                    ["8", "Institutning byudjetdan tashqari mablagʻlari hisobidan «Fargʻona salomatlik bogʻi»ni barpo etish", "2027-yil noyabr"],
                    ["9", "Fargʻona vodiysida yagona Nevrologiya, Altsgeymer va Parkinson kasalliklari ilmiy-amaliy markazini tashkil etish", "2028-yil aprel"],
                    ["10", "500 oʻrinli talabalar yotoqxonasi qurilishi", "2028-yil oktabr"],
                ],
            ),
            h("Asosiy koʻrsatkichlar"),
            ul(
                "Ilmiy salohiyat: 28,5 foiz (2025), 32,8 foiz (2026), 41 foiz (2027), 50 foiz (2028), 60 foiz (2029), 70 foiz (2030)",
                "Doktoranturadagi izlanuvchilar: 295 nafardan (2026) 345 nafargacha (2028)",
                "Stomatologiya markazi: 8 ta stomatologik qurilma, 16 oʻrinli fantom simulyatsiya zali, kuniga 60–80 bemor",
                "Talabalar yotoqxonasi: 500 oʻrin, 9 qavatli bino",
            ),
        ],
    },
]
MENU_LABELS = {
    "yillik-hisobot-2026": ("Yillik hisobot 2026", "Годовой отчёт 2026", "Annual report 2026"),
    "reyting-va-akkreditatsiya": ("Reyting va akkreditatsiya", "Рейтинги и аккредитация", "Rankings and accreditation"),
    "strategik-maqsadlar-2027": ("Strategik maqsadlar — 2027", "Стратегические цели — 2027", "Strategic goals — 2027"),
}


def block_data(kind, payload):
    """The same payload in all three languages (the Russian and English text is a copy of the Uzbek, see the header)."""
    if kind == "raw_html":
        ru = payload["html"].replace("Yillik hisobot 2026 (PDF)", "Годовой отчёт 2026 (PDF)")
        en = payload["html"].replace("Yillik hisobot 2026 (PDF)", "Annual report 2026 (PDF)")
        return {"uz": dict(payload), "ru": {"html": ru}, "en": {"html": en}}
    return {"uz": json.loads(json.dumps(payload)), "ru": json.loads(json.dumps(payload)), "en": json.loads(json.dumps(payload))}


print("MODE:", MODE)

# ================================================================ undo
if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    with transaction.atomic():
        block = ContentBlock.objects.get(pk=backup["doctoral"]["block_id"])
        for lang, old_html in backup["doctoral"]["html"].items():
            block.data[lang]["html"] = old_html
        block.save(update_fields=["data"])
        block.page.save()
        for pk, fields in backup["project_old"].items():
            item = HomeItem.objects.get(pk=int(pk))
            for field, value in fields.items():
                setattr(item, field, value)
            item.save(update_fields=list(fields))
        MenuItem.objects.filter(pk__in=backup["created"]["menu"]).delete()
        Page.objects.filter(pk__in=backup["created"]["pages"]).delete()  # their blocks go with them
        HomeItem.objects.filter(pk__in=backup["created"]["items"]).delete()
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: the doctoral text and the project card are back, the 3 pages, their menu entries and the So'x card are removed. (backup kept under a new name)")
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

# ================================================================ plan (nothing is written until every check has passed)
# 1. doctoral page
page = Page.objects.filter(slug=DOCTORAL_SLUG).first()
if page is None:
    raise SystemExit("STOP: page '%s' not found. Nothing was changed." % DOCTORAL_SLUG)
blocks = list(page.blocks.filter(block_type="raw_html").order_by("order"))
if len(blocks) != 1:
    raise SystemExit("STOP: page '%s' has %d text (raw_html) blocks, expected exactly 1. Nothing was changed." % (DOCTORAL_SLUG, len(blocks)))
doctoral_block = blocks[0]
old_html, new_html = {}, {}
for lang, (old, new) in DOCTORAL.items():
    html = (doctoral_block.data.get(lang) or {}).get("html") or ""
    found = html.count(old)
    if found != 1:
        raise SystemExit("STOP: [%s] the doctoral text %r occurs %d times, expected 1 (already changed or edited?). Nothing was changed." % (lang, old[:60], found))
    old_html[lang] = html
    new_html[lang] = html.replace(old, new)

# 2. project cards
tele = list(HomeItem.objects.filter(section=HomeItem.PROJECT, title_uz="Teletibbiyot"))
if len(tele) != 1:
    raise SystemExit("STOP: expected exactly one 'Teletibbiyot' project card, found %d. Nothing was changed." % len(tele))
tele = tele[0]
if HomeItem.objects.filter(section=HomeItem.PROJECT, url=SOX_CARD["url"]).exists():
    raise SystemExit("STOP: the So'x card is already there. Nothing was changed.")

# 3. pages and menu
parents = list(MenuItem.objects.filter(label_uz=PARENT_LABEL, parent__label_uz=GRANDPARENT_LABEL, children__isnull=False).distinct())
if len(parents) != 1:
    raise SystemExit("STOP: expected exactly one menu item %s -> %s with entries, found %d. Nothing was changed." % (GRANDPARENT_LABEL, PARENT_LABEL, len(parents)))
parent = parents[0]
for spec in PAGES:
    if Page.objects.filter(slug=spec["slug"]).exists():
        raise SystemExit("STOP: the page '%s' already exists. Nothing was changed." % spec["slug"])
    if MenuItem.objects.filter(url="/blog/%d/%s" % (parent.pk, spec["slug"])).exists():
        raise SystemExit("STOP: a menu entry for '%s' already exists. Nothing was changed." % spec["slug"])
    for kind, payload in spec["blocks"]:
        validate_block_data(kind, block_data(kind, payload))  # a malformed block stops everything here, before any write

# ================================================================ show
print("\n[page %s] doctoral figures" % DOCTORAL_SLUG)
for lang, (old, new) in DOCTORAL.items():
    print("   [%s] - %s" % (lang, old))
    print("   [%s] + %s" % (lang, new))
print("\n[home page project cards]")
print("   Teletibbiyot (url %r)  ->  iShifo (url 'https://ishifo.uz')" % tele.url)
print("   new card: %s / %s / %s  ->  %s" % (SOX_CARD["title_uz"], SOX_CARD["title_ru"], SOX_CARD["title_en"], SOX_CARD["url"]))
last = parent.children.order_by("-order", "-id").first()
base_order = (last.order if last else -1) + 1
print("\n[menu %s -> %s: %d entries now]" % (GRANDPARENT_LABEL, PARENT_LABEL, parent.children.count()))
for i, spec in enumerate(PAGES):
    uz, ru, en = MENU_LABELS[spec["slug"]]
    print("   new entry (order %d): %s / %s / %s  ->  /blog/%d/%s   [%d blocks]" % (base_order + i, uz, ru, en, parent.pk, spec["slug"], len(spec["blocks"])))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

# ================================================================ apply
os.makedirs(BACKUP_DIR, exist_ok=True)
backup = {
    "created_at": datetime.now().isoformat(),
    "doctoral": {"block_id": doctoral_block.pk, "html": old_html},
    "project_old": {str(tele.pk): {"title_uz": tele.title_uz, "title_ru": tele.title_ru, "title_en": tele.title_en, "url": tele.url}},
    "created": {"menu": [], "pages": [], "items": []},
}
with transaction.atomic():
    for lang, html in new_html.items():
        doctoral_block.data[lang]["html"] = html
    doctoral_block.save(update_fields=["data"])
    page.save()

    tele.title_uz = tele.title_ru = tele.title_en = "iShifo"
    tele.url = "https://ishifo.uz"
    tele.save(update_fields=["title_uz", "title_ru", "title_en", "url"])
    sox = HomeItem.objects.create(section=HomeItem.PROJECT, order=tele.order, is_active=True, **SOX_CARD)
    backup["created"]["items"].append(sox.pk)

    for i, spec in enumerate(PAGES):
        new_page = Page.objects.create(slug=spec["slug"], title_uz=spec["title"]["uz"], title_ru=spec["title"]["ru"], title_en=spec["title"]["en"])
        backup["created"]["pages"].append(new_page.pk)
        for order, (kind, payload) in enumerate(spec["blocks"], start=1):
            ContentBlock.objects.create(page=new_page, order=order, block_type=kind, data=block_data(kind, payload))
        uz, ru, en = MENU_LABELS[spec["slug"]]
        entry = MenuItem.objects.create(parent=parent, label_uz=uz, label_ru=ru, label_en=en, url="/blog/%d/%s" % (parent.pk, spec["slug"]), order=base_order + i)
        backup["created"]["menu"].append(entry.pk)
    json.dump(backup, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
print("DONE: doctoral figures updated, project cards changed, %d pages and menu entries created. To put everything back: MODE=undo with the same command." % len(PAGES))
print("(the site shows it within about 10 minutes at most)")
