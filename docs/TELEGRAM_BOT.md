# Telegram bot for staff news

University staff send photos and text to a Telegram bot; it lands in the admin panel as a **draft** news post.
Nothing is published without an administrator (Yangiliklar -> status "E'lon qilingan").

## How people get in
* The admin panel page **Sozlamalar -> Telegram bot** shows an invite link `t.me/<bot>?start=<code>`.
  Whoever opens the bot through it types their name and department and is **active** at once.
* Anyone without the code is registered too but stays **pending** until an approver taps "Ruxsat berish" in Telegram
  or the admin sets the status in **Murojaatlar -> Telegram xodimlar**.
* "Havolani almashtirish" makes a new code: the old link stops registering people.
* Approvers (a flag on the person) get a Telegram message for every new person and every new draft.

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
