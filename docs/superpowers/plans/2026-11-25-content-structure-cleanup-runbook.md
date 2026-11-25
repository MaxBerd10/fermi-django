# “Institut haqida” boʻlimi: kontentni bazaga oʻtkazish (39–44-skriptlar)

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
| 44 | Menyu nomlari (ru, en) va boʻlim nomi | `dry` oxirida `EXPECTED_SOURCE_SHA=...` chiqadi; `apply` uchun shu qiymatni bering (`MODE=apply EXPECTED_SOURCE_SHA=...`). Eslatma: 1881-band (`/blog/1879/kredit-modul-nizomi`) bu skriptda yoʻq. |

Har bir skript: `dry` hech narsa yozmaydi; reja (`plan.json`) tuzilgan paytdagi blok oʻzgarmagan boʻlsa ishlaydi; adminʻda tahrirlangan blok `SKIPPED` boʻlib roʻyxatga tushadi; `apply` bitta tranzaksiya va backup bilan bajariladi; ikkinchi `apply` rad etiladi; `undo` faqat yangi bloklar oʻzgarmagan joyda eskisini qaytaradi.

Diqqat: agar `apply` barcha bloklarni `SKIPPED` qilib oʻtkazsa ham skript “DONE” deb yozadi va backup qoldiradi; rejani qayta tuzgach `apply` “bu avval qoʻllangan” deb rad etadi. Bunday holda avval `MODE=undo` (hech narsani oʻzgartirmaydi), soʻng qayta `apply` qiling.

Reja eskirsa (sahifa adminʻda oʻzgargan boʻlsa), skriptni qayta tuzing: `python deploy/content/yillik-hisobot-2026-40/make_plan.py` (40–43 uchun shu nomdagi fayl), 39 uchun `python deploy/content/_report_images.py deploy/content/yillik-hisobot-2026-39/plan.json`.

## 3. Serverga chiqarish

Serverda faqat alohida ruxsatdan keyin ishlang. Skriptlar serverda `/home/fermi-django` ichida, `set -a && . /etc/fermi-django.env && set +a` dan keyin ishlaydi.

1. Baza (`pg_dump`) va `media/` ning backupini oling.
2. Yangi frontendʻni chiqaring va DARHOL (bir xizmat oynasida) 40-skriptni qoʻllang. Sabab: yangi frontend eski `raw_html` bloklarini oddiy `block` sifatida chizadi. “Institut xaqida” sahifasida esa eski kod bu blokning katta matnini (har tilda taxminan 9–10 ming belgi, hech qachon tekshirilmagan tarixiy matn) yashirib, faqat rasmni koʻrsatardi: 40 qoʻllanmaguncha bu matn ommaga ochiq boʻlib qoladi. 40 `SKIPPED` desa (blok adminʻda oʻzgartirilgan), toʻxtang: frontendʻni oldingi versiyaga qaytaring yoki rejani qayta tuzib, 40ʻni qayta ishga tushiring. Boshqa sahifalar skriptlarsiz ham ishlaydi (hisobot rasmlari 39 gacha oddiy HTML boʻlib koʻrinadi, USMLE sahifasi 41 gacha sarlavhasiz turadi).
3. Serverdagi repozitoriy nusxasini yangilang (skriptlar rasm va PDFʻni shu nusxadan oʻqiydi).
4. 39, 40, 41, 42, 43, 44 tartibida: har biri uchun avval `MODE=dry`, natijani oʻqing, keyin `MODE=apply`.
5. Tekshiruv: `chown` — yangi fayllar `www-data` egaligida boʻlishi kerak (`find /home/fermi-django/media -user root` boʻsh chiqsin). Skriptlar root nomidan ishlaganda oʻzi `chown` qiladi, baribir tekshiring. Keyin `scripts/audit_section.py` va 25 sahifani uch tilda brauzerda oching (sarlavha, ketma-ketlik, telefon koʻrinishi, rasm va hujjat kartalari, konsol).
6. Boʻlim qabul qilingandan keyingina `frontend/public/images/hisobot`, `institut-about.jpg` va `institute-history` fayllarini `public` dan oʻchirish mumkin (skriptlarni qayta ishlatish kerak boʻlsa, ular kerak).

## 4. Qaytarish

Faqat qoʻllangan skriptlarni teskari tartibda (44 → 39) qaytaring, `BACKUP_DIR` apply paytidagi bilan bir xil boʻlsin:

```sh
run_step 44 MODE=undo
run_step 43 MODE=undo
# ... 39 gacha
```

`undo` adminʻda tahrirlangan joyni `left ...` deb qoldiradi va tegmaydi: backup JSON va joriy kontentni solishtirib qaror qiling. 41 va 42 media papkadagi eski fayllarni oʻchirmaydi, faqat oʻzi yaratgan `Image` qatorlarini olib tashlaydi (41 repozitoriydan nusxalagan bino rasmini ham oʻchiradi); 39, 40 va 43 oʻzi nusxalagan rasm fayllarini ham oʻchiradi.
