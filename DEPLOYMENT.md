# Production deployment — Django backend

This is the backend half of a same-box deploy: nginx (TLS) -> the frontend's
Node service (`frontend/DEPLOYMENT.md`) -> gunicorn (this service, 127.0.0.1:8000
only, never public). The two are deployed as separate systemd services on the
same server; neither is reachable directly from the internet except through
nginx.

## Server prerequisites

- Everything in `frontend/DEPLOYMENT.md`'s prerequisites, plus:
- Python 3.13, PostgreSQL 16+, Redis
- A PostgreSQL database and user created for this app (matching whatever you
  put in `/etc/fermi-django.env`'s `DB_*` values)

## First deployment

```bash
sudo mkdir -p /var/www/fermi-django
sudo chown "$USER":www-data /var/www/fermi-django
git clone <YOUR_GITHUB_REPOSITORY_URL> /var/www/fermi-django
cd /var/www/fermi-django
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Create the server-only env file (never committed — see `.gitignore`):

```bash
sudo cp deploy/fermi-django.env.example /etc/fermi-django.env
sudo nano /etc/fermi-django.env   # fill in SECRET_KEY, DB_PASSWORD, real domain, etc.
sudo chmod 600 /etc/fermi-django.env
sudo chown root:root /etc/fermi-django.env
```

Generate a real `SECRET_KEY` (don't reuse the dev one):

```bash
.venv/bin/python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Run migrations and collect static files (admin CSS/JS — not media, that's
served straight from `MEDIA_ROOT`, see `config/urls.py`):

```bash
set -a; source /etc/fermi-django.env; set +a
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
```

Create the first admin user (real production credentials, not the local-dev
`admin`/`fermi-admin-2026` one used during development):

```bash
.venv/bin/python manage.py createsuperuser
```

Install and start the service:

```bash
sudo cp deploy/systemd/fermi-django.service /etc/systemd/system/fermi-django.service
sudo systemctl daemon-reload
sudo systemctl enable --now fermi-django
sudo systemctl status fermi-django
```

Then deploy the frontend service per `frontend/DEPLOYMENT.md` — it must be
running and pointed at this one (`FERMI_API_BASE_URL=http://127.0.0.1:8000`,
already the default in `frontend/deploy/fjsti-web.env.example`) before nginx
is put in front of either.

## Updating after a Git push

```bash
cd /var/www/fermi-django
git pull --ff-only
.venv/bin/pip install -r requirements.txt
set -a; source /etc/fermi-django.env; set +a
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart fermi-django
sudo systemctl status fermi-django
```

## Verification

```bash
curl -I http://127.0.0.1:8000/api/v1/settings   # direct to gunicorn, bypasses nginx/Node
curl -I https://your-domain.uz/api/v1/settings  # through the full chain
curl -I https://your-domain.uz/media/<some-real-uploaded-file-path>
curl -I https://your-domain.uz/django-admin/
sudo journalctl -u fermi-django -n 100 --no-pager
```

A 301 on the direct `127.0.0.1:8000` check is expected and correct
(`SECURE_SSL_REDIRECT`, see `config/settings.py`) unless you pass
`-H "X-Forwarded-Proto: https"` — nginx supplies that header for real
requests, curl doesn't by default.

## What's deliberately NOT here yet

- **Database backups.** Nothing in this repo backs up Postgres — set up
  `pg_dump` on a cron/timer, or your hosting provider's managed backup, before
  this holds real user submissions (`apps.forms`) that can't be re-imported
  from the old site.
- **Error monitoring / structured logging.** Errors currently only go to
  `journalctl` via gunicorn's `--error-logfile -`. Fine to start; add Sentry
  or similar once this is handling real traffic.
- **HSTS preload / `SECURE_HSTS_PRELOAD`.** `config/settings.py` enables HSTS
  at a conservative 1-hour value once `DEBUG=False`. Raise the duration once
  HTTPS has been confirmed stable for a while; don't submit to the browser
  preload list without reading what that commitment means first (very hard to
  reverse).
