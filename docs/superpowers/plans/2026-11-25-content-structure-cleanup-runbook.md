# “Institut haqida” boʻlimi: kontentni bazaga oʻtkazish (39–70-skriptlar)

Maqsad: boʻlimning 25 sahifasi uch tilda (uz, ru, en) bir xil tipli bloklardan iborat boʻlsin; rasmlar media kutubxonasida tursin; saytda sahifaga xos maxsus kod qolmasin.

**Muhim:** 36, 37 va 38-skriptlarni QOʻLLAMANG. Ularning tasdiqlangan matnlari 41-skriptga kirgan, 41 ularning oʻrnini bosadi.

## 1. Sinov muhitida (serverdan oldin)

1. Amaldagi bazaning nusxasi va unga mos `media/` papkasini alohida sinov muhitiga oling. Sinov uchun alohida `BACKUP_DIR` boʻlsin. Django sozlamalari aynan sinov bazasiga ulanganini tekshiring.
2. Repozitoriy ildizidan, har bir skript uchun (avval `MODE=dry`, natijani oʻqing, keyin `MODE=apply`):

```sh
export BACKUP_DIR=/absolute/path/to/scratch-backups
run_step() {   # run_step 40 MODE=dry
  local step="$1"; shift
  env "$@" .venv/bin/python manage.py shell < "deploy/content/yillik-hisobot-2026-${step}/apply.py"
}
```

3. Avval auditni ishga tushiring (eski HTML boʻyicha topilmalar kutiladi), oxirida yana:

```sh
.venv/bin/python manage.py shell < scripts/audit_section.py
```

Sinov natijasi (2026-11-25, sinov bazasi, 39–44 tartib bilan qoʻllangandan keyin): `legacy` topilmasi 56 dan 0 ga tushdi; struktura, til va havola muammosi yoʻq. Qolgan yozuvlar faqat `REVIEW` (hisobot sahifalarining rasm izohlari uch tilda bir xil) va sinov bazasidagi soxta rasm fayli.

## 2. Skriptlar (shu tartibda)

| Skript | Nima qiladi | Qoʻllashdan oldin |
|---|---|---|
| 39 | Hisobot sahifalari: 98 ta rasm `image` bloklariga, hisobot PDF sahifa oxiridagi `document` blokiga | `dry`. Kutilmagan `SKIPPED` boʻlsa, sababini tekshiring (blok adminʻda oʻzgartirilgan). Rasmlar repozitoriydagi `frontend/public/images/hisobot`, PDF `frontend/public/files` dan oʻqiladi. |
| 40 | “Institut xaqida”: sarlavha, ikkita matn, bino rasmi, ECAQA hujjatiga nom | `dry`. Rasm `frontend/public/images/institut-about.jpg` dan. Eski 25 KB HTML (saytda koʻrinmagan) olib tashlanadi, nusxasi backup JSONʻda qoladi. |
| 41 | Missiya, USMLE, Ichki tartib qoidalari, Odob-axloq kodeksi: uch tilda bir xil tipli bloklar | `dry`. Fayllar serverdagi `media/` papkasidan oʻqiladi (`migrated/...` va `uploads/2026/09/USMLE_targibot_*.jpg`), nusxalanmaydi. Ichki tartib qoidalarining ru/en matnidagi bitta qator (“professor-oʻqituvchilar”) uz matndan tarjima qilingan: ru va en oʻquvchi tekshirsin. |
| 42 | Olti rasmli sahifa (yoʻriqnoma, kredit modul, test markazi, talabalar kengashi, taʻlim yoʻnalishlari, xalqaro akkreditatsiya) | `dry`. Rasm fayllari `media/migrated/...` da boʻlmasa `dry` roʻyxat bilan toʻxtaydi. |
| 43 | Institut tarixi (`department-42`): 59 blok yangi tartibda, 13 shaxs | `dry`. Sahifaning BARCHA bloklari rejadagi holatda boʻlishi shart, bittasi oʻzgargan boʻlsa hech narsa yozilmaydi va farq roʻyxati chiqadi. Portretlar `frontend/public/images/institute-history/*.webp` dan. |
| 44 | Menyu nomlari (ru, en) va boʻlim nomi | `dry` oxirida `EXPECTED_SOURCE_SHA=...` chiqadi; `apply` uchun shu qiymatni bering (`MODE=apply EXPECTED_SOURCE_SHA=...`). Kredit modul nizomi “Meʼyoriy hujjatlar” ostida ham turadi (1881-band): unga ham xuddi shu nomlar beriladi. |
| 45 | Hujjat kartalarining nomi (yoʻriqnoma, kredit modul, test markazi, tuzilma) uch tilda | `dry`. Faqat `caption` yoziladi; adminʻda oʻzgargan yoki nomi bor blok `SKIPPED`. 44 dan keyin qoʻllang (ru/en nomlari shundan olingan). |
| 46 | Institut konferensiyalari (4 sahifa): maqola/toʻplam havolalari `document` bloklariga | `dry`. Fayllar serverdagi `media/migrated/...` da boʻlishi shart, yoʻq boʻlsa `dry` roʻyxat bilan toʻxtaydi. PDFʻlar `uploads/documents/` ga nusxalanadi (eski yoʻlar 100 belgidan uzun). 2 ta havolaning fayli yoʻq (410): ularning sarlavhasi matn boʻlib qoladi, `tarjima-kerak.md`ga qarang. |
| 47 | Institut binolari (8 sahifa): rasm-faqat `raw_html` bloklari rasm bloklariga (bir nechta rasm galereya koʻrinishida) | `dry`. Uz rasmlari asos, ru/en farqlari (2-Oʻquv kampusi en, Vivariy en, Kongress zallari ru tartib va en) `dry` chiqishida roʻyxat bilan koʻrsatiladi. Rasmlar serverdagi `media/migrated/img/fotogallery/...` da boʻlishi shart, yoʻq boʻlsa `dry` roʻyxat bilan toʻxtaydi. Bu boʻlim “Institut haqida” bilan bogʻliq emas, alohida qoʻllanadi. |
| 48 | Institut kengashi (5 sahifa): kengash matni (paragraf, sarlavha, 2 roʻyxat), tarkib/kun tartibi/qarorlar rasmlari, qarorlar PDF kartalari, avtoreferatlar (13 himoya = 13 karta, 2 sarlavha) | `dry`. Fayllar serverdagi `media/migrated/img/...` da boʻlishi shart, yoʻq boʻlsa `dry` roʻyxat bilan toʻxtaydi. PDFʻlar `uploads/documents/` ga nusxalanadi. Mavjud 3 ta PDF kartaga nom beriladi (kartada fayl nomi koʻrinmasin). en tilidagi 5 ta vazifa rus tilidan tarjima qilingan: `tarjima-kerak.md`. |
| 49 | Institut gazetasi (6 sahifa): muqova rasmi, arxivlarda har son PDF kartaga (uch tilda nom), mavjud kartalarga nom | `dry`. ru/en roʻyxatlari (arxivlarning nusxasi) va ru/en dagi boshqa rasm saqlanmaydi: uz asos. Fayllar `media/migrated/img/yangilikar/FJSTI gazetasi/...` da boʻlishi shart. |
| 50 | Meʻyoriy hujjatlar (7 sahifa; “Kredit modul nizomi” 42-skriptda): qonun maʼlumotlari, akt roʻyxatlari ([nom](havola) koʻrinishida), Vazirlar buyruqlari, kartalarga nom | `dry`. ru/en matnlari uz bilan qator-qator moslangan, yoʻq boʻlgan joylar tarjima qilingan: `tarjima-kerak.md` (ru/en oʻquvchi tekshirsin). Frontend `[nom](havola)` ni havolaga aylantirishi uchun yangi frontend bilan birga chiqadi. |
| 51 | FJSTI Ilmiy jurnali (6 sahifa): tahrir hayʼati, jurnal muqovasi, JCPM-2023/2024/2025 arxivlari (har maqola PDF kartaga, sarlavhalar KATTA HARFdan oddiy yozuvga) | `dry`. ~200 PDF `uploads/documents/` ga nusxalanadi (uzun nomlar 50 belgigacha qisqartiriladi). Maqola sarlavhalarini bir marta koʻzdan kechiring (`tarjima-kerak.md`). |
| 52 | “Thumbay Fergana College” sahifasi (Institut yangiliklari): ingliz reklama matni uch tilda; uz va ru tarjima qilingan | `dry`. `tarjima-kerak.md` (uz va ru oʻquvchi tekshirsin). |
| 53 | “Institut sertifikatlari”: sertifikat nomlari ru/en da (Stomatologiya, Pediatriya, Farmatsiya, akkreditatsiya hujjati) tarjima qilingan | `dry`. Faqat ru/en nomlari, eski oʻzbekcha matn boʻlsa. |
| 54 | Faoliyat > Xalqaro faoliyat: “Xalqaro xamkor tashkilotlar” (ofis manzillari, rasm, kartaga nom) va “Iqlim boʻyicha xarakatlar strategiyasi” (besh yillik reja, 16 siyosat PDF kartaga); ingliz matni uz va ru ga tarjima qilingan | `dry`. 16 PDF `uploads/documents/` ga nusxalanadi. `tarjima-kerak.md` (uz va ru oʻquvchi tekshirsin). “Xalqaro taʼlim” sahifasi faqat bitta hujjat kartasi, oʻzgarmaydi; Thumbay sahifasi 52-skriptda. |
| 55 | Faoliyat > Ilmiy faoliyat (5 sahifa): Normativ-huquqiy hujjatlar (Vazirlar Mahkamasining 304-son qarori ingliz tiliga tarjima qilindi), Grant siyosati, Innovatsion gʻoyalar, Ilmiy tadqiqot yoʻnalishlari, Oliy oʻquv yurtidan keyingi taʻlim; uz asos, ru/en moslangan | `dry`. 7 PDF `uploads/documents/` ga nusxalanadi; Innovatsion gʻoyalar rasmining yoʻli 100 belgidan uzun, shuning uchun rasm kutubxonaga nusxalanadi (undo nusxani diskda qoldiradi). Konferensiyalar, Kengash, Jurnal, Avtoreferatlar 46, 48, 51 da. `tarjima-kerak.md` (uz, ru va en oʻquvchi tekshirsin). Frontend `[nom](havola)` bilan birga chiqadi. |
| 56 | Faoliyat > Moliyaviy faoliyat (8 sahifa): 4 eski HTML sahifa (smeta havolalari kartaga, bitta tugallanmagan gap), 4 PDF karta nomlari uch tilda | `dry`. 4 PDF/Excel `uploads/documents/` ga nusxalanadi. “Davlat xaridlari ... komissiya tarkibi” sahifasi aslida tugallanmagan bitta gap: xodimlar tarkibni qoʻshishi kerak. `tarjima-kerak.md`. |
| 57 | Faoliyat > Madaniy-maʼrifiy va Oʻquv-uslubiy faoliyat (4 sahifa): “Kam taʼminlangan talabalar...” (toza oʻzbekchada qayta yozilgan), Malaka tavsifnoma va Malaka talablari (15 PDF kartaga), Reyting nizomi (karta nomi) | `dry`. 15 PDF (~135 MB) `uploads/documents/` ga nusxalanadi: diskda joy bor-yoʻqligini tekshiring. `tarjima-kerak.md` (oʻzbekcha matnni oʻqituvchi/oʻquvchi koʻrib chiqsin). |
| 58 | Faoliyat > Fakultetlar faoliyati (3 sahifa): sarlavhalar va 11 PDF kartasi (har tilning oʻz PDF faylida) | `dry`. ~15 PDF `uploads/documents/` ga nusxalanadi. Ba’zi tillar uchun PDF yoʻq: oʻzbekcha PDF koʻrsatiladi (`tarjima-kerak.md`). |
| 59 | Faoliyat > Korrupsiyaga qarshi kurashish faoliyati (6 sahifa): tadbirlar (rasmlar), Tavsiyaviy qoʻllanma (ru/en qayta yozilgan), Davlat dasturlari, SSV buyrugʻi va 19 ilova (20 PDF kartaga), 2 ta PDF karta nomi | `dry`. ~22 PDF `uploads/documents/` ga nusxalanadi. `tarjima-kerak.md` (ru va en oʻquvchi 4 abzatsni tekshirsin). |
| 60 | Faoliyat > Doktorantura (3 sahifa): Doktorantura maʻlumotlari (inglizcha matn qayta yozilgan, 7 sarlavha, 4 roʻyxat), Malakaviy imtihonlar (12 dastur), Monografiya (muqova va 4 PDF) | `dry`. ~35 PDF (12 dastur ikki sahifada) `uploads/documents/` ga nusxalanadi: diskda joy bor-yoʻqligini tekshiring. `tarjima-kerak.md` (inglizcha matnni toʻliq oʻqitish kerak). |
| 61 | Tuzilma, Abiturient, Talabalar, Xorijiy-talabalar, Kongress, Interaktiv xizmatlar, Yashil Universitet: 60 sahifa (uch tilda bir xil tuzilishli), umumiy konverter `_auto_plan.py` bilan bloklarga | `dry`. Rasm va PDF nusxalanadi (diskni tekshiring). Tarjima qilinmagan: faqat tarjimalangan sarlavhalar roʻyxati `tarjima-kerak.md` da. Tuzilishi turlicha sahifalar keyingi skriptlarda. |
| 62 | Tuzilma va Abiturient: 13 sahifa (uch tilda tuzilishi turlicha edi, qoʻlda moslangan, tarjima kerak emas) | `dry`. Rasm va PDF nusxalanadi (diskni tekshiring). `tarjima-kerak.md`. |
| 63 | Tuzilma, Abiturient, Talabalar, Xorijiy, Interaktiv, Yashil: 28 sahifa (uch tilda tuzilishi turlicha, qoʻlda moslangan, 91 ta matn bizning tarjimamiz) | `dry`. Rasm va PDF nusxalanadi (diskni tekshiring). `tarjima-kerak.md`. |
| 64 | Abiturient, Talabalar, Interaktiv: 10 sahifa (3 tasi qoʻlda yozilgan, 74 ta matn bizning tarjimamiz) | `dry`. Rasm va PDF nusxalanadi (diskni tekshiring). `tarjima-kerak.md`. |
| 65 | Tuzilma va Yashil Universitet: 4 sahifa (biri qoʻlda yozilgan, 7 ta matn bizning tarjimamiz) | `dry`. Rasm va PDF nusxalanadi (diskni tekshiring). `tarjima-kerak.md`. |
| 66 | Interaktiv xizmatlar: shifokorlar malaka oshirish sertifikatlari reyestri (2 jadval, birlashgan kataklar) | `dry`. Rasm va PDF nusxalanadi (diskni tekshiring). `tarjima-kerak.md`. |
| 67 | Tuzilma: hududiy boshqarmalar (14 hudud, xaritalar bilan) va bilim yurtlari (10 muassasa) qoʻlda yozilgan | `dry`. Rasm va PDF nusxalanadi (diskni tekshiring). `tarjima-kerak.md`. |
| 68 | Abiturient: texnikum bitiruvchilarini qabul qilish nizomi (inglizcha matn toʻliq bizning tarjimamiz, 53 blok) | `dry`. Rasm va PDF nusxalanadi (diskni tekshiring). `tarjima-kerak.md`. |
| 69 | Abiturient: qabul nizomi (bakalavriat; ruscha va inglizcha matnlar toʻliq bizning tarjimamiz, 91 blok, lex.uz izohlari olib tashlangan) | `dry`. Rasm va PDF nusxalanadi (diskni tekshiring). `tarjima-kerak.md`. |
| 70 | Talabalar: bakalavr talabalari uchun yoʻriqnoma (koʻchirish, tiklash, chetlashtirish; ruscha va inglizcha matn uzbekchadan yozilgan, eski inglizcha matn alohida faylda saqlandi) | `dry`. Rasm va PDF nusxalanadi (diskni tekshiring). `tarjima-kerak.md`. |

Har bir skript: `dry` hech narsa yozmaydi; reja (`plan.json`) tuzilgan paytdagi blok oʻzgarmagan boʻlsa ishlaydi; adminʻda tahrirlangan blok `SKIPPED` boʻlib roʻyxatga tushadi; `apply` bitta tranzaksiya va backup bilan bajariladi; ikkinchi `apply` rad etiladi; `undo` faqat yangi bloklar oʻzgarmagan joyda eskisini qaytaradi.

Diqqat: agar `apply` barcha bloklarni `SKIPPED` qilib oʻtkazsa ham skript “DONE” deb yozadi va backup qoldiradi; rejani qayta tuzgach `apply` “bu avval qoʻllangan” deb rad etadi. Bunday holda avval `MODE=undo` (hech narsani oʻzgartirmaydi), soʻng qayta `apply` qiling.

Reja eskirsa (sahifa adminʻda oʻzgargan boʻlsa), skriptni qayta tuzing: `python deploy/content/yillik-hisobot-2026-40/make_plan.py` (40–43 uchun shu nomdagi fayl), 39 uchun `python deploy/content/_report_images.py deploy/content/yillik-hisobot-2026-39/plan.json`.

## 3. Serverga chiqarish

Serverda faqat alohida ruxsatdan keyin ishlang. Skriptlar serverda `/home/fermi-django` ichida, `set -a && . /etc/fermi-django.env && set +a` dan keyin ishlaydi.

1. Baza (`pg_dump`) va `media/` ning backupini oling.
2. Yangi frontendʻni chiqaring va DARHOL (bir xizmat oynasida) 40-skriptni qoʻllang. Sabab: yangi frontend eski `raw_html` bloklarini oddiy `block` sifatida chizadi. “Institut xaqida” sahifasida esa eski kod bu blokning katta matnini (har tilda taxminan 9–10 ming belgi, hech qachon tekshirilmagan tarixiy matn) yashirib, faqat rasmni koʻrsatardi: 40 qoʻllanmaguncha bu matn ommaga ochiq boʻlib qoladi. 40 `SKIPPED` desa (blok adminʻda oʻzgartirilgan), toʻxtang: frontendʻni oldingi versiyaga qaytaring yoki rejani qayta tuzib, 40ʻni qayta ishga tushiring. Boshqa sahifalar skriptlarsiz ham ishlaydi (hisobot rasmlari 39 gacha oddiy HTML boʻlib koʻrinadi, USMLE sahifasi 41 gacha sarlavhasiz turadi).
3. Serverdagi repozitoriy nusxasini yangilang (skriptlar rasm va PDFʻni shu nusxadan oʻqiydi).
4. 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54, 55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70 tartibida: har biri uchun avval `MODE=dry`, natijani oʻqing, keyin `MODE=apply`.
5. Tekshiruv: `chown` — yangi fayllar `www-data` egaligida boʻlishi kerak (`find /home/fermi-django/media -user root` boʻsh chiqsin). Skriptlar root nomidan ishlaganda oʻzi `chown` qiladi, baribir tekshiring. Keyin `scripts/audit_section.py` va 25 sahifani uch tilda brauzerda oching (sarlavha, ketma-ketlik, telefon koʻrinishi, rasm va hujjat kartalari, konsol).
6. Boʻlim qabul qilingandan keyingina `frontend/public/images/hisobot`, `institut-about.jpg` va `institute-history` fayllarini `public` dan oʻchirish mumkin (skriptlarni qayta ishlatish kerak boʻlsa, ular kerak).

## 4. Qaytarish

Faqat qoʻllangan skriptlarni teskari tartibda (70 → 39) qaytaring, `BACKUP_DIR` apply paytidagi bilan bir xil boʻlsin:

```sh
run_step 44 MODE=undo
run_step 43 MODE=undo
# ... 39 gacha
```

`undo` adminʻda tahrirlangan joyni `left ...` deb qoldiradi va tegmaydi: backup JSON va joriy kontentni solishtirib qaror qiling. 41 va 42 media papkadagi eski fayllarni oʻchirmaydi, faqat oʻzi yaratgan `Image` qatorlarini olib tashlaydi (41 repozitoriydan nusxalagan bino rasmini ham oʻchiradi); 39, 40 va 43 oʻzi nusxalagan rasm fayllarini ham oʻchiradi.
