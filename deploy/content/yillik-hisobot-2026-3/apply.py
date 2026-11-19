# Third part of the annual-report update (FJSTI_Yillik_hisobot_2026_yangi.pdf): the rest of the report as six admin-editable
# CMS pages (Sahifalar), each with an entry in the menu Institut -> Institut xaqida, after the three added in part 2:
#
#   1. Xalqaro hamkorlik va investitsiyalar      (report p. 20, 33-36)
#   2. Ilmiy va innovatsion faoliyat             (p. 37-49)
#   3. Sunʻiy intellekt tizimlari                (p. 23-31; the demo log-ins printed on p. 28-29 are NOT copied)
#   4. 2027-yil vazifalari: batafsil             (p. 62-74)
#   5. Maʻnaviy-maʻrifiy ishlar va olimpiadalar  (p. 14, 50-56)
#   6. Moliya, oʻquv-uslubiy ishlar va raqamlashtirish, institut tarixi va rahbarlari (p. 8-9, 15-22, 57-60)
#
# Every figure is taken from the report as it is printed. The Russian and English text of the blocks is a COPY of the Uzbek text
# (the admin panel marks such blocks "needs translation"); nothing was machine-translated. Only the six menu labels have
# Russian and English names. Where the report disagrees with itself the text says so or uses the figure that adds up:
# Scopus 2026 = 159 (the yearly figures plus one nashr dated 2027 give the report's total of 340).
#
# SAFE BY DESIGN: dry (default) writes nothing and shows everything it would do; every block is validated first; apply saves the
# ids of what it creates to a backup file (a second apply is refused) and writes everything in one transaction; undo removes
# only what apply created.
#
#   cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
#   MODE=dry   .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-3/apply.py
#   MODE=apply .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-3/apply.py
#   MODE=undo  .venv/bin/python manage.py shell < deploy/content/yillik-hisobot-2026-3/apply.py
import json
import os
from datetime import datetime

from django.db import transaction

from apps.content.block_schemas import validate_block_data
from apps.content.models import ContentBlock, Page
from apps.menu.models import MenuItem

MODE = os.environ.get("MODE", "dry")
BACKUP_DIR = os.environ.get("BACKUP_DIR", "/var/backups/fermi-django")
BACKUP_FILE = os.path.join(BACKUP_DIR, "yillik-hisobot-2026-3.json")
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


def links(*pairs):
    return ("raw_html", {"html": "<p>" + " · ".join('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (url, label) for url, label in pairs) + "</p>"})


# ============================================================================================ 1. international
INTERNATIONAL = [
    p("Fargʻona jamoat salomatligi tibbiyot institutining xalqaro hamkorligi, qoʻshma taʻlim dasturi, loyihalari va 2026-yilda jalb etilgan investitsiya hamda grantlar (Yillik hisobot 2026 maʻlumotlari)."),
    h("Hamkorlik geografiyasi"),
    ul("38 ta hamkor xorijiy universitet", "10 ta xalqaro tashkilot", "9 ta hamkor davlat"),
    table(
        ["Davlat", "Hamkorlar"],
        [
            ["AQSh", "University of Michigan"],
            ["BAA", "Thumbay Group, Gulf Medical University"],
            ["Yaponiya", "Juntendo University, Keio University"],
            ["Turkiya", "Tivall Health"],
            ["Hindiston", "ITEC, klinik hamkorlik"],
            ["Germaniya", "Ilmiy-taʻlim hamkorligi"],
            ["Xitoy", "Ilmiy-taʻlim hamkorligi"],
            ["Polsha", "Ilmiy-taʻlim hamkorligi"],
            ["Rossiya", "Qozon federal universiteti"],
        ],
    ),
    p("Shuningdek, Pokiston, Qirgʻiziston, Serbiya, Latviya va Avstriya bilan alohida loyihalar amalga oshirilmoqda."),
    h("BAA «Thumbay Group» bilan qoʻshma taʻlim dasturi"),
    p("«Thumbay Fergana College of Medical Sciences»: BAAdagi Thumbay Group va Gulf Medical University bilan hamkorlikda qoʻshma taʻlim dasturi amalga oshirilmoqda: oʻqituvchilar va talabalar almashinuvi, qoʻshma ilmiy-amaliy tadbirlar va yangi magistratura yoʻnalishi. Hamkorlikda maxsus (elita) guruhlar ingliz tilida tahsil oladi."),
    ul(
        "1-bosqich (3 yil, Fargʻona, Oʻzbekiston): 34 nafar talaba",
        "2-bosqich (3 yil, Ajman, BAA): 22 nafar talaba",
        "Taxminan 1 mln USD investitsiya jalb qilingan",
        "Xorijiy talabalar 6 dan ortiq davlatdan: AQSh, Turkiya, BAA, Xitoy, Kanada, Braziliya",
    ),
    h("Xalqaro loyihalar va investitsiyalar"),
    table(
        ["Yoʻnalish", "Mazmuni"],
        [
            ["«Yangi Qadam», Turkiya — 1 mln USD", "Tivall bilan nevrologik reabilitatsiya: «TİKYAPUNKTUR» qurilmasi SMA, tarqoq skleroz, serebral falaj, insult va Parkinson kasalligida qoʻllaniladi."],
            ["Yaponiya va AQSh — TOP-20", "Juntendo University (JICA, UHC dasturi) doktoranturasi, Keio Universityʻda malaka oshirish; University of Michiganʻda 2 oʻqituvchi va 2 talaba."],
            ["Birlashgan Arab Amirliklari — yangi magistratura", "Hamkorlik shartnomalari, oʻqituvchi va talabalar almashinuvi, qoʻshma ilmiy-amaliy tadbirlar."],
            ["Hindiston — bepul koʻriklar", "Nefrologiya va nevrologiya boʻyicha bepul tibbiy koʻriklar; ITEC grantida «Big Data Analytics» kursi."],
        ],
    ),
    h("2026-yil investitsiya va grant portfeli (yanvar–iyul)"),
    ul(
        "Jami jalb etilgan mablagʻ: 8 mln USD",
        "13 ta xorijiy hamkor yoki donor bilan kelishuv",
        "118 nafar xorijiy talaba qabul qilindi (jami 1 641 nafar)",
        "Talabalar eksporti: 7 930 170 USD",
    ),
    table(
        ["Hamkor", "Mablagʻ, USD"],
        [
            ["Juntendo University (Yaponiya)", "16 600"],
            ["University of Michigan (AQSh)", "12 350"],
            ["Qozon federal universiteti", "8 000"],
            ["Dr. M. Mahajan (Hindiston)", "7 700"],
            ["Daugavpils University (Latviya)", "6 250"],
            ["Keio University (Yaponiya)", "5 600"],
            ["ITEC/C-DAC (Hindiston)", "3 500"],
            ["Dr. L.K. Tripathi (Hindiston)", "3 210"],
            ["EAN Spring School (Avstriya)", "2 100"],
            ["Tivall Health (Turkiya)", "2 000"],
            ["Konferensiya (Hindiston)", "1 200"],
            ["Singidunum (Serbiya)", "750"],
            ["Oʻsh davlat universiteti", "570"],
        ],
    ),
]

# ============================================================================================ 2. science and innovation
SCIENCE = [
    p("Institutning ilmiy salohiyati, doktorantura, Scopus koʻrsatkichlari, spin-off korxonalari, simulyatsiya va innovatsion markazlari (Yillik hisobot 2026 maʻlumotlari)."),
    h("Ilmiy faoliyat raqamlarda (2021–2026)"),
    table(
        ["Koʻrsatkich", "2021", "2026", "Oʻzgarish"],
        [
            ["Ilmiy salohiyat", "11,5%", "32,8%", "+21,3 foiz punkt"],
            ["Xalqaro ilmiy loyihalar", "0", "2", "+2 ta loyiha"],
            ["Mahalliy ilmiy loyihalar", "0", "4", "+4 ta loyiha"],
            ["Intellektual mulk guvohnomalari", "113", "297", "+163%"],
        ],
    ),
    h("Doktorantura va tayanch doktorantura"),
    table(
        ["Yil", "Mustaqil izlanuvchilar", "Tayanch doktorantura", "Jami"],
        [["2024", "215", "29", "244"], ["2025", "235", "34", "269"], ["2026", "255", "40", "295"]],
    ),
    p("2026-yilda 295 nafar izlanuvchi ilmiy tadqiqot olib bordi (255 mustaqil izlanuvchi va 40 tayanch doktorant). Prognoz: 2028-yilgacha 345 nafar."),
    h("Scopus bazasidagi ilmiy maqolalar"),
    p("Institut Scopus AF-ID 60275644. Maʻlumot manbasi: Scopus, 2026-yil noyabr holati."),
    table(
        ["Yil", "Maqolalar soni"],
        [["2021", "2"], ["2022", "4"], ["2023", "43"], ["2024", "45"], ["2025", "86"], ["2026", "159"]],
    ),
    ul(
        "2021–2026-yillarda jami 340 ta ilmiy nashr Scopus bazasida indekslangan (shu jumladan 2027-yil sanasi bilan 1 ta)",
        "2025-yildan 2026-yilga maqolalar soni 86 tadan 159 taga oshdi (+85 foiz); 2023-yildan beri yillik nashrlar 3,7 barobar koʻpaydi",
        "886 ta iqtibos (2026-yil 13-noyabr holatiga); 2026-yil maqolalariga 52 ta",
        "36 ta maqola Scopusʻdan chiqarilgan (discontinued) jurnallarda; hisobga olinmasa 2026-yil koʻrsatkichi 122 ta",
        "2027-yil rejasi: 185 ta maqola (2026-yilga nisbatan +17 foiz), taxminan 1 400 ta iqtibos",
        "Sifat siljishi (2026 dan 2027 gacha): Q1 8 dan 14 taga, Q2 44 dan 55 taga, Q3 19 dan 30 taga; Q4 ulushi 52 foizdan 44 foizgacha kamaytiriladi, mutlaq soni deyarli saqlanadi (82 dan 81 taga)",
        "Kvartillar SCImago SJR 2025 koʻrsatkichlari asosida, har bir jurnalning eng yuqori toifasi boʻyicha berilgan",
    ),
    h("Patentlar, jamgʻarma va xalqaro stajirovkalar"),
    ul(
        "1 ta patent Intellektual mulk markazida davlat roʻyxatidan oʻtkazildi",
        "355 mln soʻm innovatsiya jamgʻarmasidan ilmiy-innovatsion loyihalarga ajratildi",
        "Hindiston, ITEC grant dasturi: «Specialised Programme on Big Data Analytics» (Hadoop, Spark, MongoDB) — Karimova Madinabonu; barcha xarajatlar Hindiston tomonidan qoplandi",
        "Gulf Medical University (BAA, Ajman): I. Iminaxunova «USMLE dasturini kredit-modul tizimiga joriy etish» stajirovkasini yakunladi (2025-yil 19-noyabr — 5-dekabr)",
        "Qozon federal universiteti (Rossiya): A.M. Butlerov nomidagi «Kimyo» institutida 2 oʻqituvchi stajirovkadan oʻtdi (2026-yil 16-mart — 10-aprel); Innovatsion rivojlanish agentligi moliyalashtirdi",
    ),
    h("Spin-off korxonalar va markazlar (2026-yilda tashkil etilgan)"),
    table(
        ["Sana", "Nomi", "Faoliyati"],
        [
            ["2026-yil 15-may", "«OnLab» MCHJ", "Klinik laboratoriya: PCR, NGS, gistologiya, biobank; kuniga 1 000+ bemor"],
            ["2026-yil 7-iyul", "«FJSTI Tipografiya va poligrafiya»", "Kitob, darslik, ilmiy jurnal va poligrafiya xizmatlari kampus ichida"],
            ["2026-yil 6-avgust", "«FJSTI MedTech Innovation Hub»", "Dasturiy taʻminot, tibbiy qurilmalar va onlayn taʻlim — 6 yoʻnalish"],
            ["2026-yil avgust", "«TivaLL Fergana» MCHJ", "Nevrologik reabilitatsiya markazi (PF-54 ijrosida; institut ulushi — 25%)"],
        ],
    ),
    p("Jami 13 ta ixtisoslashtirilgan boʻlinma va korxona. Yana ikkita markaz: «Startap» markazi (2025-yil 20-sentabr, 387-I-05-son buyruq) va «Inkubatsiya va akseleratsiya» markazi (2026-yil 11-aprel, 220-I-05-son buyruq) — yoshlarni ilmiy-tadqiqot va innovatsion ishlarga jalb etish uchun."),
    h("«IL» — Institut laboratoriyasi"),
    p("2026-yil 15-mayda tashkil etildi; loyihaning umumiy qiymati 2 mlrd soʻm. 6 ta ixtisoslashtirilgan boʻlim, 1 000+ turdagi tahlil, kuniga 1 000+ bemor oqimi."),
    ul(
        "Klinik-diagnostik tahlillar: gematologiya, biokimyo, immunologiya, PCR, bakteriologiya, onkomarkerlar, TORCH",
        "Gistologiya va patomorfologiya: sitologiya (Pap-test), IHC, sunʻiy intellekt asosidagi raqamli patomorfologiya",
        "Genomika va molekulyar tibbiyot: NGS, genom va ekzom sekvenslash, farmakogenetika, prenatal skrining",
        "Innovatsion tekshiruvlar: POCT, liquid biopsy, metabolomika, mikrobiom, biobank",
    ),
    h("Steril dorilar ishlab chiqarish zonasi"),
    p("Talabalar uchun ishlab chiqarish amaliyoti bazasi. Zonani tashkil etish xarajati 800 mln soʻm; 47+ xil inyeksion va poroshok dori vositasi, 2 dori shakli (eritma va poroshok)."),
    ul(
        "Jarayon bosqichlari: 1) tayyorlash (xom ashyo va idishlar), 2) sterilizatsiya (avtoklavda bugʻ bilan), 3) quritish (termik ishlov), 4) quyish (aseptik dozalash), 5) sifat nazorati (tekshiruv va hujjatlar)",
        "Aseptik sharoitda ishlash, steril dori texnologiyasi va sifat nazorati talablari — farmatsevtika sanoatiga tayyor kadr",
    ),
    h("Simulyatsiya markazi"),
    p("Real klinik vaziyatlarga yaqin xavfsiz muhit; loyiha qiymati 7 mlrd soʻm."),
    ul(
        "6 ta amaliyot kabinasi, 3 turdagi robot-simulyator, 18+ klinik stsenariy, yiliga 600+ talaba mashgʻuloti",
        "Robot-simulyatorlar: Leonardo HF (katta yoshli), Arthur (oʻsmir), MIA HF (0–30 kunlik chaqaloq)",
        "Yoʻnalishlar: reanimatsiya va shoshilinch yordam; neonatologiya va pediatriya; akusherlik-ginekologik holatlar; debrifing va video-tahlil; OSCE formatida attestatsiya",
    ),
    h("VR simulyatsiya markazi"),
    p("«Startap» markazi tarkibidagi VR zona: 12 ta VR koʻzoynagi, 10+ virtual modul, 4 yoʻnalish, yiliga 300+ talaba."),
    ul(
        "Modullar: virtual anatomiya (3D), virtual jarrohlik, favqulodda vaziyatlar, klinik koʻrik koʻnikmalari",
        "Afzalliklari: real bemorsiz xavfsiz mashq muhiti, xatolarni cheklovsiz takrorlash, kamyob klinik holatlarni simulyatsiya qilish, natijalarni raqamli baholash",
    ),
    h("«FJSTI MedTech Innovation Hub» va startap gʻoyalar"),
    p("2026-yil 6-avgustda tashkil etilgan markaz zonalari: Developer Zone (dasturiy mahsulotlar), VR Zone (virtual simulyatsiya), MedDevice (tibbiy qurilmalar), 3D Zone (3D printer, silikon quyma), MedEdu Lab (onlayn taʻlim platformasi), BioAnalytics (AI diagnostika xizmatlari)."),
    p("«Startup loyihalar — 2025» gʻoliblari: 14 ta loyihadan eng yuqori baholangan 4 tasi moliyalashtirildi (197-I-05-son buyruq)."),
    table(
        ["Loyiha", "Muallif", "Moliyalashtirish"],
        [
            ["«Clinic Monitoring»", "Sh. Ahmadaliyev", "155 mln soʻm"],
            ["«AI doctor»", "I. Raxmonberdiyev", "305 mln soʻm"],
            ["«Online exam»", "—", "180 mln soʻm"],
            ["«Teletibbiyot»", "—", "150 mln soʻm"],
        ],
    ),
    h("Tibbiyot sohasida innovatsion tadqiqotlar ilmiy markazi: 2026-yilgi pilot loyihalar"),
    ul(
        "Yurak-qon tomir kasalliklarini erta aniqlash: xavf guruhidagi bemorlar skriningi va zamonaviy diagnostika usullari samaradorligi oʻrganildi",
        "Raqamli monitoring: tibbiy xizmat sifatini oshirish va bemor holatini muntazam kuzatishda raqamli texnologiyalar tadqiq etildi",
        "Amaliy tavsiyalar: diagnostika va profilaktikani takomillashtirish, innovatsion texnologiyalarni joriy etish boʻyicha tavsiyalar ishlab chiqildi",
    ),
]

# ============================================================================================ 3. artificial intelligence
AI = [
    p("Institutda ishlab chiqilgan va joriy etilgan sunʻiy intellekt platformalari: taʻlim, imtihon, xavfsizlik, klinik qaror va teletibbiyot. Ular FJSTI raqamli boshqaruv ekotizimiga integratsiyalashgan (Yillik hisobot 2026 maʻlumotlari)."),
    ul(
        "iMentor — sunʻiy intellekt asosidagi taʻlim tizimi",
        "iTest — onlayn imtihon platformasi",
        "Situatsion markaz — sunʻiy intellekt asosidagi video-kuzatuv va nazorat",
        "aiShifokor — klinik qarorni qoʻllab-quvvatlash",
        "iShifo — teletibbiyot platformasi",
        "Soʻx modeli — tuman miqyosida amaliy joriy etish",
    ),
    links(("https://imentor.uz", "imentor.uz"), ("https://aishifokor.uz", "aishifokor.uz"), ("https://ishifo.uz", "ishifo.uz")),
    h("iMentor"),
    p("Talabalarning oʻquv jarayonini shaxsiylashtirilgan tarzda qoʻllab-quvvatlovchi tizim. Oʻqituvchilar maʻruza, klinik holat, test va taqdimotlarni sunʻiy intellekt (DeepSeek AI) yordamida bir necha daqiqada yaratadi. Platforma FJSTI tomonidan ishlab chiqilgan va qoʻllab-quvvatlanadi."),
    ul("8+ taʻlim moduli", "3 til", "AI kontent generatori"),
    h("iTest"),
    p("Talabalar bilimini xolis va shaffof baholash uchun nazoratli onlayn imtihon tizimi. Imtihon savollari iMentor platformasidan API orqali avtomatik olinadi, ikkala tizim yagona ekotizim sifatida ishlaydi."),
    ul("Jarayon: iMentor savollar bazasi, API orqali avtomatik uzatish, iTest nazoratli imtihon, natija — xolis baholash"),
    h("Situatsion markaz"),
    p("Institut hududidagi kameralardan real vaqtda video oqimlar yagona nazorat markazida birlashtiriladi; sunʻiy intellekt xavfsizlik, intizom va davomatni avtomatik kuzatadi."),
    ul("Kampus xavfsizligi", "Davomat nazorati", "Intizom monitoringi"),
    h("aiShifokor"),
    p("Klinik qaror qabul qilishni qoʻllab-quvvatlovchi AI platforma. Bemor shikoyatlari, anamnez, dori vositalari, hayotiy koʻrsatkichlar, laboratoriya va instrumental tekshiruvlar (EKG, rentgen, KT, MRT) asosida ehtimoliy differensial tashxislarni shakllantiradi va AI mutaxassislar ishtirokida virtual konsilium tashkil etadi. Maqsad — shifokorni almashtirish emas, uning tajribasini AI tahlili bilan kuchaytirish."),
    ul("AI konsilium", "Klinik xavf skoringi", "EKG tahlili", "Klinik protokollar", "Dorilar oʻzaro taʻsiri", "Global bilimlar bazasi", "Yakuniy tibbiy hisobot"),
    h("iShifo"),
    p("Masofaviy tibbiyot (telemeditsina) platformasi: bemor, shifokor va institut oʻrtasidagi yagona aloqa."),
    ul(
        "Bemorlar uchun: masofadan tibbiy maslahat, shifokor bilan onlayn muloqot, raqamli tibbiy murojaat, tavsiyalarni masofadan olish",
        "Shifokorlar uchun: bemorlar bilan masofaviy ishlash, murojaatlarni qabul qilish, tibbiy maʻlumotlarni koʻrib chiqish, konsultatsiyani raqamli tashkil etish",
        "Istiqbol yoʻnalishlari: mobil ilova va video konsultatsiya, elektron tibbiy karta va retsept, laboratoriya natijalari integratsiyasi, klinikalar bilan integratsiya, onlayn navbat va reyting, AI yordamchi",
    ),
    h("Soʻx modeli"),
    p("Sunʻiy intellekt, teletibbiyot va raqamli boshqaruv — tuman miqyosida. Prezidentning PQ–60-son qarori (2022-yil 28-yanvar) va Sogʻliqni saqlash vazirligi topshirigʻiga koʻra institut Soʻx tumanida tibbiy audit, klinik verifikatsiya, aholi koʻriklari, kadrlarni oʻqitish va raqamli tizimlarni joriy etdi. Xizmat zanjiri: uyda, AI tahlil, mutaxassis, marshrut, nazorat."),
    table(
        ["Koʻrsatkich", "Qiymat"],
        [
            ["Qayta klinik koʻrikdan oʻtgan aholi", "39 025+"],
            ["Yagona raqamli registrdagi aholi", "85 129"],
            ["Mobil brigadalar (mahallalarda)", "14"],
            ["Koʻriklarda qatnashgan shifokorlar", "400+"],
            ["Oʻqitilgan shifokor va IT-hamshira", "27"],
        ],
    ),
    h("Soʻx modeli: muammolardan natijalargacha"),
    table(
        ["Aniqlangan muammo", "Qiymat"],
        [
            ["Aholida oxirgi koʻrik sanasi qayd etilmagan", "59,8%"],
            ["Tibbiy yozuvlar (13 411 ta) klinik holatga mos kelmadi", "34,4%"],
            ["Boʻsh shtat birligi — tor mutaxassislar tanqis", "20,75"],
            ["Bemor tumandan tashqariga yuborildi (2025); aholi xarajati yiliga kamida 2,7 mlrd soʻm", "7 019"],
        ],
    ),
    ul(
        "Dispanser nazorati: 11 890 dan 33 360 gacha (+181 foiz)",
        "Reimbursatsiya: 30 mln soʻmdan 117 mln soʻmgacha (+290 foiz)",
        "13 411 tibbiy yozuv klinik koʻrik asosida tuzatildi; aiShifokor va iShifo orqali onlayn konsultatsiyalar yoʻlga qoʻyildi",
        "Asosiy takliflar: telemeditsina xonalari; DMED, aiShifokor va iShifo; maqsadli ordinatura grantlari; laboratoriya autsorsingi; qoʻshimcha tez yordam brigadasi; real vaqt monitoringi",
    ),
    p("Soʻx modeli haqida batafsil maʻlumot va toʻliq hisobot — «Soʻx modeli» sahifasida."),
]

# ============================================================================================ 4. 2027 priorities in detail
PRIORITIES = [
    p("Institutning 2027-yil ustuvor vazifalari: har bir vazifaning mazmuni, bosqichlari va muddatlari (Yillik hisobot 2026 maʻlumotlari). Rektor A. Sidikov va prorektorlar masʻul. Vazifalarning umumiy jadvali — «Strategik maqsadlar — 2027» sahifasida."),
    h("1. Stomatologiya va yuz-jagʻ jarrohligi markazini tashkil etish (muddat: 2028-yil sentabr)"),
    p("Stomatologiya bazasida yagona klinik, oʻquv va ilmiy markaz. Klinik, oʻquv va ilmiy zonalar bir qavatda (taxminan 900 kv. m), toza va iflos oqimlar ajratilgan."),
    ul(
        "8 ta stomatologik qurilma (4 kattalar, 2 bolalar, 2 jarrohlik)",
        "1 ta yuz-jagʻ operatsiya xonasi va 4 oʻrinli reanimatsiya",
        "KT 3D va panoramik tasvirlash",
        "Oʻz CAD-CAM protezlash laboratoriyasi",
        "16 oʻrinli fantom simulyatsiya zali",
        "Klinik vazifa: kuniga 60–80 bemor; oʻquv vazifa: stomatologiya talabalari va rezidentlar amaliyoti; ilmiy vazifa: implantologiya, raqamli stomatologiya",
    ),
    h("2. Buyuk Britaniya QAA akkreditatsiyasidan oʻtish (muddat: 2027-yil aprel)"),
    p("Buyuk Britaniyaning Oliy taʻlim sifatini taʻminlash agentligi (QAA) xalqaro institutsional akkreditatsiyasi «yoʻl xaritasi»."),
    table(
        ["Bosqich", "Muddat", "Mazmuni"],
        [
            ["1. Tahlil", "2026-yil noyabr–dekabr", "Institut jarayonlarini QAA Sifat kodeksi bilan solishtirish; ishchi guruh tayinlash"],
            ["2. Oʻz-oʻzini baholash", "2027-yil yanvar", "Dalillar bazasi bilan oʻz-oʻzini baholash hujjatini (SED) tayyorlash"],
            ["3. Kamchiliklarni bartaraf etish", "2027-yil fevral", "Siyosatlar, talabalar fikr-mulohazasi va baholash qoidalarini yangilash"],
            ["4. Sinov ekspertizasi", "2027-yil mart", "Ekspertlar bilan ichki sinov; xodim va talabalar uchun brifinglar"],
            ["5. QAA tashrifi", "2027-yil aprel", "Ekspertlar tashrifi, xodimlar, talabalar va ish beruvchilar bilan uchrashuvlar"],
            ["6. Qaror va harakatlar rejasi", "Tashrifdan soʻng", "Akkreditatsiya hisoboti; keyingi harakatlar rejasi eʻlon qilinadi"],
        ],
    ),
    p("QAA asosiy yoʻnalishlari: akademik standartlar, taʻlim sifati, talabalar ishtiroki, boshqaruv, takomillashtirish."),
    h("3. QS, THE va GreenMetric reytinglariga kirish (muddat: 2030-yil sentabr)"),
    p("Milliy TOP-2 va GreenMetric TOP-700 dan uchta global reytingning barchasiga kirishgacha — bosqichma-bosqich oʻsish."),
    table(
        ["Yil", "Maqsad"],
        [
            ["2026", "GreenMetric TOP 700; milliy TOP 2"],
            ["2027", "GreenMetric TOP 500; QS ga maʻlumot topshirish"],
            ["2028", "THE Impact Rankings reytingiga kirish"],
            ["2029", "QS Asia reytingiga kirish"],
            ["2030", "QS, THE va GreenMetric uchalasida ham"],
        ],
    ),
    ul(
        "QS: akademik obroʻ 30 foiz, ish beruvchilar fikri 15 foiz, iqtiboslar bir oʻqituvchiga 20 foiz. Vositamiz: soʻrovnoma hamkorlari, Scopusʻda koʻrinish",
        "THE: taʻlim, ilmiy muhit, ilmiy sifat, sanoat, xalqaro yoʻnalganlik. Vositamiz: maʻlumotlar portali, xalqaro hammualliflik",
        "GreenMetric: hudud va infratuzilma, energiya, chiqindi, suv, transport, taʻlim. Vositamiz: «yashil kampus» loyihalari («Fargʻona salomatlik bogʻi»)",
    ),
    h("4. Ilmiy salohiyatni 2030-yilgacha 70 foizga oshirish (muddat: 2030-yil aprel)"),
    p("PhD va DSc dissertatsiyasini himoya qiluvchi tadqiqotchilar sonini 200 taga yetkazib, ilmiy darajali oʻqituvchilar ulushini 70 foizga oshirish."),
    table(
        ["Yil", "Ilmiy salohiyat"],
        [["2025 (amalda)", "28,5%"], ["2026 (amalda)", "32,8%"], ["2027", "41%"], ["2028", "50%"], ["2029", "60%"], ["2030", "70%"]],
    ),
    ul(
        "200 nafar tadqiqotchi PhD / DSc himoyasi — 2030-yilgacha",
        "Doktoranturadagi izlanuvchilar: 295 nafardan 345 nafargacha (2026–2028)",
        "2026-yildan ilmiy salohiyat oʻsishi: +37,2 foiz punkt (2027–2029 — rejalashtirilgan koʻrsatkichlar)",
    ),
    h("5. Erasmus+ xalqaro «AI Community» loyihasini amalga oshirish (muddat: 2027-yil oktabr)"),
    p("Erasmus+ doirasida universitetlar va davlat hamkorlaridan iborat «Sunʻiy intellekt hamjamiyati»ni yaratish boʻyicha qoʻshma loyiha. Ishtirokchilar: FJSTI (Oʻzbekiston), Singidunum University (Serbiya), Janubiy Qozogʻiston tibbiyot akademiyasi, Turkiya Transport va infratuzilma vazirligi."),
    ul(
        "FJSTI hissasi: tibbiy AI yechimlari (iMentor, aiShifokor, iShifo), tibbiy maʻlumotlar toʻplamlari va klinik validatsiya, pilot hudud — Soʻx tumani modeli",
        "Kutilayotgan natijalar: umumiy AI oʻquv dasturi va qoʻshma kurslar, xodim va talabalar akademik mobilligi, qoʻshma nashrlar va ochiq platforma",
    ),
    h("6. 10 ta dasturni TOP-300 universitetlari dasturlariga moslashtirish (muddat: 2027-yil aprel)"),
    p("10 ta bakalavriat va magistratura dasturini QS/THE TOP-300 hamkor universitetlar dasturlari bilan solishtirish — har bir dastur uchun bitta sikl: hamkor dasturni tanlash, taʻlim natijalari va kreditlarni solishtirish, oʻquv reja va fan dasturlarini yangilash, tasdiqlash va joriy etish, qoʻshma tahlil va mobillik."),
    ul(
        "Davolash ishi; Pediatriya ishi; Stomatologiya; Farmatsiya; Jamoat salomatligi; Oliy hamshiralik ishi; Tibbiy profilaktika ishi",
        "Magistratura: klinik mutaxassisliklar; jamoat salomatligi; tibbiy taʻlim",
        "Natija: ECTS ga mos oʻquv rejalar, qoʻshma diplom dasturlariga tayyorlik va QS/THE da akademik obroʻning oshishi",
        "Dasturlar roʻyxati taxminiy — Ilmiy kengash tomonidan tasdiqlanadi",
    ),
    h("7. «Tibbiyotda sunʻiy intellekt» taʻlim dasturlarini yaratish (2027-yil aprel — 2030-yil aprel)"),
    p("Tibbiyot, maʻlumotlar fani va AI muhandisligini birlashtirgan yangi bakalavriat va magistratura — institutning oʻz AI platformalari asosida."),
    table(
        ["Bosqich", "Fanlar"],
        [
            ["Bakalavriat (4 yil), 1-kurs", "Biotibbiyot fanlari, Python, matematika va statistika"],
            ["Bakalavriat, 2-kurs", "Anatomiya va fiziologiya, maʻlumotlar tuzilmasi, maʻlumotlar bazalari"],
            ["Bakalavriat, 3-kurs", "Mashinali oʻqitish, tibbiy tasvirlar, biosignallar"],
            ["Bakalavriat, 4-kurs", "Klinik AI loyihasi, etika va meʻyorlar, amaliyot"],
            ["Magistratura (2 yil), 1-kurs", "Chuqur oʻqitish, tibbiy hujjatlar uchun NLP, kompyuter koʻrish"],
            ["Magistratura, 2-kurs", "Klinik validatsiya, AI mahsulot ishlab chiqish, dissertatsiya"],
        ],
    ),
    ul(
        "Amaliyot bazasi: iMentor, iTest, aiShifokor, iShifo, Situatsion markaz, MedTech Innovation Hub",
        "Muddatlar: 2027-yil aprel — konsepsiya va litsenziya; 2027-yil sentabr — bakalavriatga birinchi qabul; 2028-yil — magistratura dasturi; 2030-yil aprel — toʻliq ishga tushirish, birinchi bitiruvchilar",
        "Bitiruvchilar: klinik maʻlumotlar mutaxassislari, AI mahsulot mutaxassislari, tibbiy AI tadqiqotchilari",
    ),
    h("8. «Fargʻona salomatlik bogʻi» loyihasini amalga oshirish (muddat: 2027-yil noyabr)"),
    p("Institutning byudjetdan tashqari mablagʻlari hisobidan Fargʻona viloyati aholisi, xorijiy talabalar va mehmonlar uchun: yashil zonalar, ochiq amfiteatr, skeyt park, futbol, tennis va basketbol maydonlari."),
    ul(
        "Tashrif buyuruvchilar uchun: bepul koʻrik (qon bosimi, glyukoza, TVI), talabalar nazorati ostida skrining, sport va sogʻlomlashtirish dasturlari, yashil kampus (GreenMetric)",
        "Moliyalashtirish va faoliyat: institutning byudjetdan tashqari mablagʻlari, har kuni aholi uchun ochiq, koʻngilli talabalar va tibbiyot xodimlari",
        "Loyiha tarkibi: asosiy darvoza, favvora, amfiteatr, institutga kirish yoʻlagi, ochiq sport trenajyorlari, dam olish zonalari, Book Cafe, skeyt park, sport maydonlari",
    ),
    h("9. Nevrologiya, Altsgeymer va Parkinson markazini tashkil etish (muddat: 2028-yil aprel)"),
    p("Fargʻona vodiysidagi ilk ixtisoslashgan markaz — institutning koʻp tarmoqli klinikasi tarkibida. Yoʻl: birlamchi boʻgʻindan yoʻllanma, xotira va harakat skriningi, diagnostika (MRT, EEG, laboratoriya), davolash va reabilitatsiya, iShifo orqali masofaviy kuzatuv."),
    ul(
        "Xotira klinikasi: Altsgeymer va demensiya, erta kognitiv test, oilaviy maslahat",
        "Harakat buzilishlari: Parkinson, dori terapiyasi, yurish va tremorni baholash",
        "Neyroreabilitatsiya: TİKYAPUNKTUR qurilmasi (Tivall, Turkiya), fizioterapiya va logopediya",
        "Ilmiy tadqiqot va registr: vodiy boʻyicha bemorlar registri, klinik tadqiqotlar, PhD mavzulari",
        "Nega Fargʻona vodiysi: Oʻzbekistonning eng aholi zich hududi; aholi qarishi demensiya va Parkinson kasalligining koʻpayishiga olib keladi; hozir bemorlar Toshkentga qatnaydi; institutning Turkiya bilan reabilitatsiya loyihasi asosida",
    ),
    h("10. Zamonaviy talabalar turar joyini qurish — 500 oʻrinli (muddat: 2028-yil oktabr)"),
    p("Umumiy xizmat koʻrsatish bloki bilan tutashgan 9 qavatli bino."),
    ul(
        "500 oʻrin jami, har qavatda taxminan 55 oʻrin; har qavatda Wi-Fi bilan oʻquv xonalari; 24/7 xavfsizlik (Situatsion markaz)",
        "Bino tarkibi: 2–3 oʻrinli xonalar (har birida sanitariya uzeli); xizmat bloki — oshxona, sport zal, kirxona; yoʻlakning ikki chetida oʻquv burchaklari; sport maydoni, avtoturargoh, velosiped joylari",
    ),
]

# ============================================================================================ 5. spiritual work and olympiads
SPIRITUAL = [
    p("Institutning maʻnaviy-maʻrifiy ishlari: ijtimoiy hayot, tanlovlar, bayramlar, kitobxonlik, kasaba uyushmasi va korrupsiyaga qarshi kurash; xalqaro fan olimpiadalari natijalari (Yillik hisobot 2026 maʻlumotlari)."),
    h("Xalqaro fan olimpiadalari (2026-yil yanvar — iyul)"),
    ul("11 ta olimpiada", "193 nafar ishtirokchi talaba", "84 nafar gʻolib talaba", "Gʻoliblik ulushi: 43,5 foiz"),
    table(
        ["Olimpiada", "Gʻoliblar", "Ishtirokchilar"],
        [
            ["Avitsenna izdoshlari (TDTU)", "47", "90"],
            ["Gigiyena. Tibbiy ekologiya (TDTU)", "5", "45"],
            ["Bilimlar xazinasi (TDTU)", "5", "14"],
            ["ZARMED-2026", "7", "10"],
            ["Urganch-2030 (UrDU)", "5", "10"],
            ["Andijon-2025 (ADTI)", "5", "8"],
            ["Kommunal gigiyena (TDTU)", "1", "5"],
            ["Avitsenna izdoshlari-2026", "2", "3"],
            ["Birinchi tibbiy yordam (OʻshDU)", "3", "3"],
            ["Mikrobiologiya (TDTU)", "2", "3"],
            ["MEGA Master (TDSI)", "2", "2"],
        ],
    ),
    h("Ijtimoiy hayot qisqa satrlarda"),
    p("Yil davomida 113 ta muntazam tadbir: ekologik aksiyalar, qon donorligi, sahna sanʻati va kasbiy-shaxsiy rivojlanish treninglari."),
    table(
        ["Yoʻnalish", "Tadbirlar soni"],
        [["Kurs va treninglar", "45"], ["«Yashil makon»", "24"], ["Talabalar teatri", "23"], ["«Men donorman»", "21"]],
    ),
    h("Erishilgan yutuqlar"),
    ul(
        "Respublika va viloyat miqyosida 4 ta tanlovda yutuq; 1 ta mutlaq gʻolib jamoa",
        "«Yurtim qadriyatlari»: Davolash ishi fakulteti jamoasi viloyat bosqichida mutlaq gʻolib",
        "«Vatanga sodiq inson»: Sh. Nasirdinova sut bezi saratoni diagnostikasi maqolasi bilan medal oldi",
        "«Giyohvandlik — umr zavoli»: «Nastarin» talabalar teatr studiyasi faxrli 3-oʻrinni egalladi",
    ),
    h("Ijtimoiy hayotdan lavhalar"),
    p("Milliy va umumxalq bayramlari: Milliy urf-odatlar kechasi, Milliy taomlar koʻrgazmasi, Jamoa sayli."),
    h("Kitobxonlik haftaligi"),
    ul(
        "13-fevral: Ahmad Fargʻoniy nomidagi viloyat axborot-kutubxonasiga tashrif — 1-bosqich talabalari kutubxona fondlari, elektron resurslar va xorijiy bazalar bilan tanishdi",
        "23-aprel: uch bosqichli kitobxonlik tanlovi — Davolash ishi fakulteti talabalarining mutolaa darajasi, fikrlash va adabiy bilimlari sinaldi",
        "25-iyun: «Sogʻlom turmush» aksiyasi — talaba-qizlar bir kun smartfonsiz, kitob mutolaasi va tabiat qoʻynidagi suhbatlar bilan oʻtkazdi",
    ),
    h("Kasaba uyushma qoʻmitasi: xodimlarning dam olishi va ijtimoiy himoyasi"),
    table(
        ["Tadbir", "Natija"],
        [
            ["8-mart sovgʻalari", "300 ayol xodim (24 mln soʻm)"],
            ["Yangi yil sovgʻalari", "700 farzandga (68,75 mln soʻm)"],
            ["Sanatoriyda dam olish", "38 xodim va oila aʻzosi (45% qoplandi)"],
            ["Moddiy yordam", "15,5 mln soʻm xodimlarga"],
            ["«Oʻzbekiston boʻylab sayohat qiling!» dasturi", "29 xodim"],
            ["«Avval» dam olish zonasiga sayohat", "150+ xodim"],
            ["Fargʻona–Samarqand turistik sayohati", "10 xodim"],
            ["Oʻquv qurollari", "15 kam taʻminlangan xodim farzandiga"],
        ],
    ),
    h("Korrupsiyaga qarshi kurash: «Komplaens nazorat» tizimi — 2026"),
    ul(
        "26 ta davra suhbati, seminar va uchrashuv; 8 oy davomida 3 700+ ishtirokchi",
        "Barcha talabalar uchun 12 soatlik maxsus kurs",
        "12 nafar xodim «Virtual akademiya» sertifikatini oldi",
        "Tadbirlar mavzulari: «Biz korrupsiyaga qarshimiz», «Korrupsiya millat kushandasi», «Korrupsiyasiz kelajak sari», «Adolatli imtihonlar», «Korrupsiyadan holi hudud», «Korrupsiyasiz soha»",
        "Murojaat kanallari: fermi.uz, @FjstiMurojaatbot, t.me/antikorrupsiya_fjstida, t.me/ferghana_medical_institute",
    ),
]

# ============================================================================================ 6. finance, teaching, history
FINANCE = [
    p("Institutning moliyaviy faoliyati, oʻquv-uslubiy ishlari, axborot-resurs markazi, raqamlashtirish, institut tarixi va rahbarlari (Yillik hisobot 2026 maʻlumotlari)."),
    h("Moliyaviy oʻsish dinamikasi (umumiy mablagʻ, mlrd soʻm)"),
    table(
        ["Yil", "Umumiy mablagʻ"],
        [["2021", "44,6"], ["2022", "67,7"], ["2023", "86,3"], ["2024", "88,4"], ["2025", "154,7"], ["2026", "190"]],
    ),
    p("2021–2026-yillarda umumiy mablagʻ 326 foizga oʻsdi; oʻrtacha yillik oʻsish surʻati taxminan 34 foiz."),
    h("Institut moliyaviy koʻrsatkichlari: 2026-yil — jami 190 mlrd soʻm"),
    table(
        ["Yil", "Toʻlov-kontrakt", "Byudjet"],
        [["2021", "65,0%", "35,0%"], ["2022", "66,7%", "33,3%"], ["2023", "68,8%", "31,2%"], ["2024", "70,3%", "29,7%"], ["2025", "72,5%", "27,5%"], ["2026", "75,3%", "24,7%"]],
    ),
    ul(
        "Toʻlov-kontrakt mablagʻlari: 75,3 foiz (143 070 000 ming soʻm)",
        "Byudjetdan ajratilgan mablagʻ: 24,7 foiz (46 930 000 ming soʻm)",
    ),
    h("Ijtimoiy qoʻllab-quvvatlash va moddiy-texnik baza (2026–2027-oʻquv yiliga tayyorgarlik)"),
    ul(
        "44 nafar talabaga moddiy ragʻbat va yordam, 25 mln soʻm toʻlandi",
        "26 nafar chin yetim va ota-onasiz talaba qoʻllab-quvvatlandi",
        "6 ta klinik laboratoriya boʻlimi (1 000+ tahlil turi), 6 ta simulyatsiya kabinasi, 550 metrlik taktil (inklyuziv) yoʻlak",
        "Vivariy binosida ilmiy laboratoriya (infuzion dorilar) va IT laboratoriya-spinoff (2 oyda 5 dasturiy loyiha) tashkil etildi; kirish yoʻlagiga 4 metrlik «Fonendoskop» badiiy maketi oʻrnatildi",
    ),
    h("Oʻquv-uslubiy faoliyat raqamlarda"),
    table(
        ["Koʻrsatkich", "Qiymat"],
        [
            ["Mutaxassislik fanlari dasturi", "255"],
            ["Amaliyot va laboratoriya darsi", "350"],
            ["TOP-300 universitetlar oʻquv dasturlari asosida oʻqitish yoʻlga qoʻyilgan fanlar soni", "20"],
            ["Yangi oʻquv-uslubiy material", "1 700"],
        ],
    ),
    table(
        ["Material turi", "2025", "2026", "Oʻsish"],
        [
            ["Oʻquv qoʻllanmalar", "24", "30", "+25%"],
            ["Uslubiy koʻrsatmalar", "1", "2", "+100%"],
            ["Takomillashtirilgan darsliklar", "61", "76", "+24,6%"],
            ["Fan dasturlari", "204", "255", "+25%"],
        ],
    ),
    h("Amaliyotga yoʻnaltirilgan taʻlim"),
    p("Talabalar davolash muassasalarida stajirovka va dual taʻlim orqali klinik koʻnikma orttiradi — bu institutning eng keng hamkorlik tarmogʻi."),
    ul(
        "305+ hamkor tibbiyot muassasasi, 1 750 ta amaliyot shartnomasi",
        "137 nafar mutaxassis malaka oshirdi",
        "3 000 nafar talaba AQShning tibbiy litsenziyalash imtihoni (USMLE) dasturida oʻqitilmoqda",
        "Bitiruvchilarning 91 foizi ish bilan taʻminlangan (2025/2026-oʻquv yili); viloyat, tuman va shahar sogʻliqni saqlash boʻlimlari bilan hamkorlikda «Mehnat yarmarkasi» va «Ochiq eshiklar kuni» oʻtkazildi",
    ),
    h("Malaka oshirish va stajirovkalar — 2026 (rahbar xodimlar va professor-oʻqituvchilar)"),
    table(
        ["Yoʻnalish", "Xodimlar", "Ulushi"],
        [
            ["Xalqaro miqyosda (xorijiy taʻlim muassasalarida)", "101", "56%"],
            ["Respublika miqyosida (Oliy taʻlim tizimi kadrlarini qayta tayyorlash institutida)", "71", "39%"],
            ["Mintaqaviy darajada (mintaqaviy va tarmoq markazlarida)", "9", "5%"],
        ],
    ),
    p("Jami 181 nafar xodim."),
    h("Axborot-resurs markazi"),
    p("1 810 nomda 17 193 nusxa — toʻliq elektron xizmat."),
    table(
        ["Fond tarkibi", "Nusxa"],
        [
            ["Oʻquv darsliklar (764 nom)", "8 322"],
            ["Oʻquv qoʻllanmalar (428 nom)", "4 432"],
            ["Ilmiy adabiyot (266 nom)", "1 774"],
            ["Badiiy adabiyot (163 nom)", "1 762"],
            ["Boshqa adabiyot (189 nom)", "903"],
        ],
    ),
    ul(
        "27 475 nomdagi elektron adabiyot — library.fjsti.uz; 3 830 nomdagi resurs unilibrary.uz milliy platformasida",
        "9 922 — umumiy kitob fondi (kontingentning 61 foizi); @FJSTI_ARM Telegram kanalida 763 nafar aʻzo",
        "Talabalar — ARM aʻzosi: 6 132 / 6 725 (91 foiz); professor-oʻqituvchilar — ARM aʻzosi: 226 / 267 (85 foiz)",
        "2025 va 2026-yillar taqqoslamasi: 640 dan 800 donagacha kitob (+25 foiz); 6 dan 8 turgacha adabiyot (+33 foiz); 146 dan 182,7 mln soʻmgacha ajratildi (+25,1 foiz)",
        "2026-yilda 800 mln soʻmga 8 nomdagi 800 ta ingliz tilidagi oʻquv adabiyotlari xarid qilindi",
    ),
    h("Raqamlashtirish: FJSTI raqamli boshqaruv ekotizimi"),
    p("Taʻlim, ilmiy faoliyat, talabalar va magistratura, kadrlar, topshiriqlar hamda sifat nazorati yagona platformada birlashtirildi. Institut veb-sayti xalqaro Webometrics talablariga moslab yangilanmoqda. Raqamli tizimlar byudjetdan tashqari mablagʻlar hisobidan yildan-yilga oʻsib boruvchi hajmda moliyalashtirilmoqda."),
    ul("15 ta raqamli platforma va boshqaruv oynasi", "13 ta institut faoliyatini qamrovchi modul", "237+ interfeys ekrani", "6 ta asosiy faoliyat yoʻnalishi"),
    h("Xorijiy tilda oʻqitiladigan iqtidorli guruh"),
    p("«Thumbay Fergana College of Medical Sciences» twinning dasturi: Gulf Medical University (Thumbay Group, BAA) bilan hamkorlikda maxsus guruhlar ingliz tilida tahsil oladi — 1-bosqich (3 yil, Fargʻona) 34 nafar, 2-bosqich (3 yil, Ajman, BAA) 22 nafar talaba. Taxminan 1 mln USD investitsiya jalb qilingan."),
    h("Institut tarixi: 34 yillik taraqqiyot yoʻli"),
    ul(
        "1992-yil: Fargʻona davlat universiteti qoshida «Tibbiyot markazi» sifatida tashkil etildi (Oliy taʻlim va Sogʻliqni saqlash vazirliklarining 189/311-son qoʻshma buyrugʻi, 28-may)",
        "2020-yil: Prezidentning PQ-4911-son qarori (3-dekabr) bilan mustaqil oliy taʻlim muassasasi sifatida qayta tashkil etildi",
        "Institutsional yoʻl: FarDU «Tibbiyot markazi» (1992), Toshkent 2-DavTI Fargʻona filiali (1998), TTA Fargʻona filiali (2005), mustaqil «Fargʻona jamoat salomatligi tibbiyot instituti» (PQ-4911, 2020)",
    ),
    h("Institut rahbarlari (1992-yildan bugungi kungacha)"),
    table(
        ["Yillar", "Rahbar", "Unvoni"],
        [
            ["1992–1996", "Mirzayev Komil", "DSc, professor, birinchi rahbar"],
            ["1996–2005", "Nishonov Yusib", "DSc, professor"],
            ["2005–2012", "Abduraxmonov Muxammadjon", "DSc, professor"],
            ["2012–2015", "Usmanov Ravshanbek", "DSc, professor"],
            ["2015–2018", "Mamatqulov Xasan", "DSc, professor"],
            ["2018–2021", "Sultanov Gʻafurdjon", "Tibbiyot fanlari nomzodi"],
            ["2021 — hozir", "Sidikov Akmal", "Rektor, DSc, professor"],
        ],
    ),
]

PAGES = [
    {"slug": "xalqaro-hamkorlik-va-investitsiyalar", "title": ("Xalqaro hamkorlik va investitsiyalar", "Международное сотрудничество и инвестиции", "International cooperation and investment"), "blocks": INTERNATIONAL},
    {"slug": "ilmiy-va-innovatsion-faoliyat", "title": ("Ilmiy va innovatsion faoliyat", "Научная и инновационная деятельность", "Research and innovation"), "blocks": SCIENCE},
    {"slug": "suniy-intellekt-tizimlari", "title": ("Sunʻiy intellekt tizimlari", "Системы искусственного интеллекта", "Artificial intelligence systems"), "blocks": AI},
    {"slug": "2027-yil-vazifalari-batafsil", "title": ("2027-yil vazifalari: batafsil", "Задачи 2027 года: подробно", "2027 priorities in detail"), "blocks": PRIORITIES},
    {"slug": "manaviy-marifiy-ishlar-va-olimpiadalar", "title": ("Maʻnaviy-maʻrifiy ishlar va olimpiadalar", "Духовно-просветительская работа и олимпиады", "Cultural work and olympiads"), "blocks": SPIRITUAL},
    {"slug": "moliya-oquv-uslubiy-ishlar-va-raqamlashtirish", "title": ("Moliya, oʻquv-uslubiy ishlar va raqamlashtirish", "Финансы, учебно-методическая работа и цифровизация", "Finance, teaching and digitalization"), "blocks": FINANCE},
]


def block_data(kind, payload):
    """The same payload in all three languages (the Russian and English text is a copy of the Uzbek, see the header)."""
    return {lang: json.loads(json.dumps(payload)) for lang in ("uz", "ru", "en")}


print("MODE:", MODE)

if MODE == "undo":
    if not os.path.isfile(BACKUP_FILE):
        raise SystemExit("STOP: no backup file (%s): nothing to undo." % BACKUP_FILE)
    backup = json.load(open(BACKUP_FILE, encoding="utf8"))
    with transaction.atomic():
        MenuItem.objects.filter(pk__in=backup["created"]["menu"]).delete()
        Page.objects.filter(pk__in=backup["created"]["pages"]).delete()  # their blocks go with them
    os.rename(BACKUP_FILE, BACKUP_FILE + ".undone-" + datetime.now().strftime("%Y%m%d-%H%M%S"))
    print("UNDONE: the 6 pages and their menu entries are removed. (backup kept under a new name)")
    raise SystemExit(0)

if MODE not in ("dry", "apply"):
    raise SystemExit("STOP: MODE must be dry, apply or undo.")
if MODE == "apply" and os.path.exists(BACKUP_FILE):
    raise SystemExit("STOP: %s already exists, so this was applied before. Run MODE=undo first if you want to redo it." % BACKUP_FILE)

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

last = parent.children.order_by("-order", "-id").first()
base_order = (last.order if last else -1) + 1
print("\n[menu %s -> %s: %d entries now]" % (GRANDPARENT_LABEL, PARENT_LABEL, parent.children.count()))
for i, spec in enumerate(PAGES):
    uz, ru, en = spec["title"]
    print("   new entry (order %d): %s / %s / %s  ->  /blog/%d/%s   [%d blocks]" % (base_order + i, uz, ru, en, parent.pk, spec["slug"], len(spec["blocks"])))

if MODE == "dry":
    print("\nDRY RUN: nothing was changed. Run again with MODE=apply.")
    raise SystemExit(0)

os.makedirs(BACKUP_DIR, exist_ok=True)
backup = {"created_at": datetime.now().isoformat(), "created": {"menu": [], "pages": []}}
with transaction.atomic():
    for i, spec in enumerate(PAGES):
        uz, ru, en = spec["title"]
        new_page = Page.objects.create(slug=spec["slug"], title_uz=uz, title_ru=ru, title_en=en)
        backup["created"]["pages"].append(new_page.pk)
        for order, (kind, payload) in enumerate(spec["blocks"], start=1):
            ContentBlock.objects.create(page=new_page, order=order, block_type=kind, data=block_data(kind, payload))
        entry = MenuItem.objects.create(parent=parent, label_uz=uz, label_ru=ru, label_en=en, url="/blog/%d/%s" % (parent.pk, spec["slug"]), order=base_order + i)
        backup["created"]["menu"].append(entry.pk)
    json.dump(backup, open(BACKUP_FILE, "w", encoding="utf8"), ensure_ascii=False)
print("\nbackup saved:", BACKUP_FILE)
print("DONE: %d pages and menu entries created. To put everything back: MODE=undo with the same command." % len(PAGES))
print("(the site shows it within about 10 minutes at most)")
