# fjsti.uz → fermi.uz yo'naltirish rejasi

Maqsad: `fjsti.uz` va `www.fjsti.uz` ga kirgan har bir kishi (eski havola, Google, bukmark) yangi `fermi.uz` ning **aynan shu sahifasiga** o'tsin (301). Eski server veb-sayt uchun kerak bo'lmay qolsin.

## 1. Hozirgi holat (tekshirilgan, 2026-10-05)

| Narsa | Qiymat |
|---|---|
| Domen to'lovi | 2027-yil 20-maygacha (SUVAN NET) |
| DNS qayerda boshqariladi | `rdns1.ahost.uz`, `rdns2.ahost.uz` (**shu panelga kirish kerak**) |
| `fjsti.uz`, `www.fjsti.uz` (A) | `37.140.216.172` (eski server, New Line Solutions LLC, PHP 7.4) |
| **Pochta** `MX` | `0 mail.fjsti.uz` → `mail.fjsti.uz` = `37.140.216.172` (**pochta ham eski serverda!**) |
| SPF (`TXT`) | `v=spf1 ip4:185.196.212.52 +a +mx ~all` |
| `hemis.`, `moodle.fjsti.uz` | `213.230.68.118` (boshqa server, tegilmaydi) |
| Yangi server | `87.192.230.208` (`fermi.uz`, nginx, shared server) |

Eski sahifalarning yangi saytdagi qarshiligi: eski `/blog/<id>/<slug>` va `/detail/<slug>` URL'larining **246/253** tasi yangi saytda slug bo'yicha bor (qolgan 7 tasi kesilgan/bo'sh URL'lar). Yangi sayt `/blog/<son>/<slug>` ni faqat slug bo'yicha topadi, `<son>` ahamiyatsiz, shuning uchun yo'lni o'zgartirmasdan ko'chirish yetarli.

## 2. Nima o'zgaradi va nima o'zgarmaydi

* **O'zgaradi:** faqat `fjsti.uz` va `www.fjsti.uz` ning `A` yozuvi → `87.192.230.208`.
* **O'zgarmaydi (tegilmaydi):** `MX`, `mail.fjsti.uz`, `hemis.`, `moodle.`, `TXT`/SPF, `NS`. Pochta ishlashda davom etadi.
* **Eski serverni hali o'chirib bo'lmaydi:** pochta o'sha yerda. Veb qismi bo'sh qoladi, lekin server pochta uchun turishi kerak (alohida ish: pochtani ko'chirish).
* SPF dagi `+a` endi yangi serverning IP'sini ham ruxsat etilgan qiladi (zararsiz; pochta ko'chirilganda SPF yangilanadi).

## 3. Bizning tomondan (nginx, faqat yangi fayl)

Yangi fayl: `/etc/nginx/sites-available/fjsti-redirect` (+ symlink `sites-enabled`). Boshqa saytlar va umumiy sozlama o'zgarmaydi.

**A bosqich: DNS dan OLDIN** (faqat 80-port; `Host: fjsti.uz` ni hali hech kim bu IP'ga yubormaydi, shuning uchun zararsiz):

```nginx
server {
    listen 80;
    listen 192.168.0.101:80;     # MUHIM: shu qator bo'lmasa so'rov boshqa loyihaning blokiga tushadi
    server_name fjsti.uz www.fjsti.uz;
    location ^~ /.well-known/acme-challenge/ { root /var/www/certbot; }
    location / { return 301 https://fermi.uz$request_uri; }
}
```

**B bosqich: DNS dan KEYIN, sertifikat olingach** (443-port qo'shiladi):

```nginx
server {
    listen 443 ssl;
    listen 192.168.0.101:443 ssl;
    server_name fjsti.uz www.fjsti.uz;
    ssl_certificate     /etc/letsencrypt/live/fjsti.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fjsti.uz/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    # eski fayl havolalari: saytga ko'chirilgan rasm/hujjatlar yangi manzilga
    location ^~ /uploads/img/ { rewrite ^/uploads/img/(.*)$ https://fermi.uz/media/migrated/img/$1 permanent; }
    location /               { return 301 https://fermi.uz$request_uri; }
}
```

Sertifikat (faqat shu domen uchun): `certbot certonly --webroot -w /var/www/certbot -d fjsti.uz -d www.fjsti.uz --cert-name fjsti.uz`. Avtomatik yangilanish shu sozlama bilan ishlaydi (80-portdagi IP qatori tufayli).

## 4. Tartib (taxminan 1 soat ish + DNS tarqalishi)

| # | Qachon | Kim | Nima |
|---|---|---|---|
| 1 | 24 soat oldin | DNS egasi | `fjsti.uz` va `www.fjsti.uz` `A` yozuvlarining **TTL** ini 300 soniyaga tushirish |
| 2 | Kuni, oldin | Men + siz | nginx **A bosqich** (nusxa, `nginx -t`, `reload`) |
| 3 | Past yuklama vaqti (kechqurun/dam olish) | DNS egasi | `A fjsti.uz` va `A www.fjsti.uz` → `87.192.230.208` |
| 4 | +5…15 daqiqa | Men | `certbot` (webroot) → sertifikat |
| 5 | | Men | nginx **B bosqich** (nusxa, `nginx -t`, `reload`) |
| 6 | | Men | tekshiruv (5-bo'lim) |
| 7 | 1–2 hafta keyin | DNS egasi | TTL ni yana oshirish (3600) |

3–5-qadam orasida (taxminan 10–15 daqiqa) `https://fjsti.uz` ga kirganlar sertifikat ogohlantirishini ko'rishi mumkin. `http://` ishlaydi.

## 5. Tekshiruv ro'yxati

* `http(s)://fjsti.uz/` va `www` → `301` → `https://fermi.uz/`
* `https://fjsti.uz/blog/33/institut-xaqida` → `https://fermi.uz/blog/33/institut-xaqida` (200, kontent chiqadi)
* `https://fjsti.uz/detail/<yangilik>?menu_id=71` → `https://fermi.uz/detail/<yangilik>?menu_id=71`
* `https://fjsti.uz/uploads/img/…` (ko'chirilgan fayl) → `fermi.uz/media/migrated/img/…` (200)
* **Pochta**: `@fjsti.uz` ga xat yuborib/qabul qilib ko'rish (MX o'zgarmagan, ishlashi shart)
* `hemis.fjsti.uz`, `moodle.fjsti.uz` ochiladi (o'zgarmagan)
* `fermi.uz` va boshqa saytlar ishlaydi, sertifikat yangilanishi: `certbot renew --dry-run --cert-name fjsti.uz`

## 6. Orqaga qaytarish

DNS da `A` yozuvlarini qaytadan `37.140.216.172` ga qo'yish (TTL 300 bo'lgani uchun bir necha daqiqada). Bizning nginx fayli ta'sir qilmaydi (u faqat `fjsti.uz` Host'iga javob beradi); xohlasak `sites-enabled` dagi symlink olib tashlanadi.

## 7. Cheklovlar

* `/uploads/…` dagi **ko'chirilmagan** fayllar `fermi.uz` da topilmaydi (404/"topilmadi" sahifasi). Eski saytning ommaga ko'rinadigan fayllari arxivlanmoqda; muhimlarini keyin `media` ga qo'shish mumkin.
* Yangi sayt noma'lum yo'lga ham "sahifa topilmadi" ni 200 bilan qaytaradi (SPA), Google uchun bu "soft 404".
* Google Search Console da `fjsti.uz` ni tasdiqlab, **"Change of address"** → `fermi.uz` qilish tavsiya etiladi (reyting ko'chishini tezlashtiradi). 301 lar baribir ishlaydi.
* Eski serverni (pochta bilan birga) o'chirish uchun pochtani ko'chirish kerak, alohida reja.

## 8. Boshlashdan oldin kerak

1. **DNS panelga kirish** (`ahost.uz` hisobi yoki domen egasi orqali SUVAN NET). Shu bo'lmasa reja boshlanmaydi.
2. Vaqtni tanlash (past yuklama).
3. Bizning nginx fayli (3-bo'lim) uchun ruxsat (faqat `fjsti.uz` nomlari).
