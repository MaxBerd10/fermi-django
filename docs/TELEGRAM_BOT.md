# Telegram bot for staff news

University staff send photos and text to a Telegram bot; it lands in the admin panel as a **draft** news post.
Nothing is published without an administrator (Yangiliklar -> status "E'lon qilingan").

## How people get in
* The admin panel page **Sozlamalar -> Telegram bot** shows an invite link `t.me/<bot>?start=<code>`.
  Whoever opens the bot through it presses Start, is offered the «Ilovani ochish» button (the Mini App), types their name and
  department there and is **active** at once. (Typing the name into the chat still works as a fallback.)
* Anyone without the code is registered too but stays **pending** until an approver taps "Ruxsat berish" in Telegram
  or the admin sets the status in **Murojaatlar -> Telegram xodimlar**.
* "Havolani almashtirish" makes a new code: the old link stops registering people.
* Approvers (a flag on the person) get a Telegram message for every new person and every new draft.

## Files, video, links, translations
* PDF / Word / Excel / PowerPoint (up to 3 per news item, 20 MB; the first bytes must really be that kind of file) become a
  document card on the page (the editor's "new document" marker), in the chat and in the Mini App.
* Video is not accepted (too heavy, and the site's video page is built on YouTube links): people paste a YouTube/Telegram link
  into the text and the site makes it clickable.
* When an administrator publishes a post that came from the bot, its author gets a Telegram message with the public link
  (once; apps/telegram_bot/notify.py, called from the news editor). The Mini App also lists the link with a copy button.
* Uzbek written in Cyrillic is converted to Latin (the site's canonical script). Text that is clearly Russian (see
  `looks_russian`) is NOT converted: it is kept as the Russian version and the Uzbek/English versions are machine-translated
  from it; if the translator is down the person is asked to retry or write in Uzbek.
* Otherwise the draft holds the Uzbek text only. Russian/English are filled by the admin form's machine translation (Google's keyless
  endpoint) when the post is saved/published, and can be checked there.

## Limits (apps/telegram_bot/services.py)
10 pictures per news item, 10 sent items per person per day, 6000 characters of text, 30 messages per person per minute;
at most 20 people without the invite code may start registering per hour (all together); pictures must be JPEG/PNG/WEBP, are re-encoded to JPEG (metadata, GPS included, is dropped) and kept under
`media/uploads/telegram/`. Only private chats are served; a blocked person is ignored.

## Set-up on the server (once)
1. In Telegram, talk to **@BotFather**: `/newbot`. Keep the token secret.
2. Add to `/etc/fermi-django.env` (token from BotFather, secret = any long random string):

       TELEGRAM_BOT_TOKEN=123456:ABC...
       TELEGRAM_WEBHOOK_SECRET=<output of: openssl rand -hex 32>

3. `sudo systemctl restart fermi-django`
4. Connect the bot to the site (also sets the command menu):

       cd /home/fermi-django && set -a && . /etc/fermi-django.env && set +a
       sudo -u www-data -E .venv/bin/python manage.py telegram_set_webhook
       sudo -u www-data -E .venv/bin/python manage.py telegram_set_webhook --status

5. Open the admin panel -> Sozlamalar -> Telegram bot, join through the link yourself, then in
   Murojaatlar -> Telegram xodimlar open your row and tick "Tasdiqlovchi".

The webhook is `POST /api/v1/telegram/webhook/`; it answers 403 unless Telegram's secret header matches, and 404 while the
bot is not configured. To switch the bot off: remove the two variables (or `telegram_set_webhook --delete`).

## The Mini App (frontend/src/tg, API in apps/telegram_bot/webapp.py)
A phone-friendly form inside Telegram: register (name + department), pick pictures (shrunk to 2000 px before upload), title,
text, category, «Yuborish»; and "Mening yangiliklarim" with the state of each (Tasdiq kutmoqda / Saytda chiqdi / Rad etildi).
It opens from the bot's menu button ("Yangilik yuborish", set by `telegram_set_webhook`) and from the «📱 Ilovani ochish»
button in the bot's messages. Address: `https://<site>/tg`.
* Identity is Telegram's signed `initData` (HMAC with the bot token, at most 12 h old) sent as `Authorization: tma <initData>`;
  there are no passwords and no sessions. Same people, approval, daily limits and DRAFT-only rule as the chat.
* Only pictures the person uploaded through the app (`uploads/telegram/YYYY/MM/<telegram id>-<random>.jpg`) can be attached.
* `/tg` is the only page that may be framed (by *.telegram.org, for Telegram Web); see allowTelegramFraming in
  frontend/server/production-server.mjs. If Telegram Web shows an empty frame while phones work, check that nginx adds no
  X-Frame-Options / frame-ancestors header of its own.
* Telegram's own script is NOT loaded (it would run inside our origin): src/tg/bridge.ts speaks the few events needed.
