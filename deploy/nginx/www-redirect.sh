#!/usr/bin/env bash
# Sends www.fermi.uz to fermi.uz with ONE permanent (301) redirect, keeping the path and the query:
#   http://www.fermi.uz/a?b=1   -> https://fermi.uz/a?b=1   (one hop, not two)
#   https://www.fermi.uz/a?b=1  -> https://fermi.uz/a?b=1
# Until now www.fermi.uz served the same site as fermi.uz, i.e. the site existed at two addresses (split search ranking,
# a login on one address not seen on the other, split statistics).
#
# How: in the ONE fermi file, the two existing server blocks (port 80 and 443) stop answering to www (their server_name
# becomes just "fermi.uz"), and two small new server blocks for www.fermi.uz are added at the end of the same file. The
# certificate already covers www.fermi.uz, so browsers show no warning.
#
# Touches ONLY /etc/nginx/sites-enabled/fermi-django-frontend, never another site's config. The server is shared (about 50
# sites), so: it backs the file up, runs `nginx -t`, puts the old file back by itself if the test fails, reloads gracefully
# (no dropped connections), checks the error log of that reload, then tests the real answers (www redirects, fermi.uz
# still 200) and puts the old file back by itself if any of them is wrong.
#
#   bash deploy/nginx/www-redirect.sh              # MODE=dry: shows the diff, changes nothing
#   MODE=apply bash deploy/nginx/www-redirect.sh
#   MODE=undo  bash deploy/nginx/www-redirect.sh   # puts the newest backup back
#
# Paths and commands can be overridden for testing: VHOST_FILE, BACKUP_ROOT, NGINX_BIN, RELOAD_CMD, ERROR_LOG,
# CERT_FILE, SKIP_LIVE_TEST.
set -euo pipefail

MODE="${MODE:-dry}"
VHOST_FILE="${VHOST_FILE:-/etc/nginx/sites-enabled/fermi-django-frontend}"
# its own backup folder: the campus-limits script keeps its backups (two files each) in /root/nginx-fermi-backup
BACKUP_ROOT="${BACKUP_ROOT:-/root/nginx-fermi-backup-www}"
NGINX_BIN="${NGINX_BIN:-nginx}"
RELOAD_CMD="${RELOAD_CMD:-systemctl reload nginx}"
ERROR_LOG="${ERROR_LOG:-/var/log/nginx/error.log}"
CERT_FILE="${CERT_FILE:-/etc/letsencrypt/live/fermi.uz/fullchain.pem}"

say() { printf '%s\n' "$*"; }
die() { say "STOP: $*"; exit 1; }

nginx_ok() {
  local out
  if out="$($NGINX_BIN -t 2>&1)"; then return 0; fi
  say "$out"
  return 1
}

restore_from() { cat "$1/fermi-django-frontend" > "$VHOST_FILE"; }

[ -f "$VHOST_FILE" ] || die "$VHOST_FILE not found."

if [ "$MODE" = "undo" ]; then
  latest="$(ls -1d "$BACKUP_ROOT"/*/ 2>/dev/null | sort | tail -n 1 || true)"
  [ -n "$latest" ] || die "no backup found in $BACKUP_ROOT."
  restore_from "${latest%/}"
  nginx_ok || die "nginx -t failed after restoring ${latest}; fix by hand before reloading."
  $RELOAD_CMD
  say "UNDONE: the file from ${latest} is back and nginx was reloaded."
  exit 0
fi

[ "$MODE" = "dry" ] || [ "$MODE" = "apply" ] || die "MODE must be dry, apply or undo."

# the current file must still be exactly what this script was written for
[ "$(grep -cE '^[[:space:]]*server_name fermi\.uz www\.fermi\.uz;[[:space:]]*$' "$VHOST_FILE")" = "2" ] || die "the line 'server_name fermi.uz www.fermi.uz;' is not there exactly twice (already changed, or written differently?). Nothing was modified."
[ "$(grep -cE '^[[:space:]]*listen 80;' "$VHOST_FILE")" = "1" ] || die "expected exactly one 'listen 80;'. Nothing was modified."
[ "$(grep -cE '^[[:space:]]*listen 443 ssl;' "$VHOST_FILE")" = "1" ] || die "expected exactly one 'listen 443 ssl;'. Nothing was modified."
grep -qF 'ssl_certificate /etc/letsencrypt/live/fermi.uz/fullchain.pem;' "$VHOST_FILE" || die "the ssl_certificate line is not the expected one. Nothing was modified."
grep -qF 'ssl_certificate_key /etc/letsencrypt/live/fermi.uz/privkey.pem;' "$VHOST_FILE" || die "the ssl_certificate_key line is not the expected one. Nothing was modified."
# the certificate must really list www.fermi.uz (otherwise browsers would show a warning on the redirect)
if command -v openssl >/dev/null 2>&1 && [ -f "$CERT_FILE" ]; then
  openssl x509 -in "$CERT_FILE" -noout -text 2>/dev/null | grep -q 'DNS:www\.fermi\.uz' || die "the certificate does not list www.fermi.uz. Nothing was modified."
fi

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

sed -e 's/^\([[:space:]]*\)server_name fermi\.uz www\.fermi\.uz;[[:space:]]*$/\1server_name fermi.uz;/' "$VHOST_FILE" > "$work/vhost"
cat >> "$work/vhost" <<'NGINX_BLOCKS'

# www.fermi.uz -> fermi.uz (one permanent redirect, path and query kept). Added by deploy/nginx/www-redirect.sh
server {
    listen 80;
    listen 192.168.0.101:80;
    server_name www.fermi.uz;
    server_tokens off;
    return 301 https://fermi.uz$request_uri;
}

server {
    listen 443 ssl;
    listen 192.168.0.101:443 ssl;
    server_name www.fermi.uz;
    server_tokens off;

    ssl_certificate /etc/letsencrypt/live/fermi.uz/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/fermi.uz/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    return 301 https://fermi.uz$request_uri;
}
NGINX_BLOCKS

say "MODE: $MODE"
say "=== $VHOST_FILE"
diff -u "$VHOST_FILE" "$work/vhost" || true
say

if [ "$MODE" = "dry" ]; then
  say "DRY RUN: nothing was changed. Run again with MODE=apply to put this in place."
  exit 0
fi

stamp="$(date +%Y%m%d-%H%M%S)"
backup="$BACKUP_ROOT/$stamp"
mkdir -p "$backup"
cat "$VHOST_FILE" > "$backup/fermi-django-frontend"
say "backup: $backup"

cat "$work/vhost" > "$VHOST_FILE"

if ! nginx_ok; then
  restore_from "$backup"
  say "ROLLED BACK: nginx -t failed with the new file, the old file is back and nginx was NOT reloaded."
  exit 1
fi

log_lines_before=0
[ -f "$ERROR_LOG" ] && log_lines_before="$(wc -l < "$ERROR_LOG")"
$RELOAD_CMD
sleep "${RELOAD_WAIT:-2}"

rollback() {
  say "$1"
  restore_from "$backup"
  nginx_ok || die "nginx -t failed after restoring the old file; look at it by hand."
  $RELOAD_CMD
  say "ROLLED BACK: the old file is back and nginx was reloaded with it."
  exit 1
}

# a real reload can still be refused (nginx keeps the OLD configuration and logs an [emerg] line)
if [ -f "$ERROR_LOG" ] && tail -n +"$((log_lines_before + 1))" "$ERROR_LOG" | grep -i "emerg" | grep -qi "fermi\|server_name\|listen\|ssl"; then
  rollback "nginx refused the reload: $(tail -n +"$((log_lines_before + 1))" "$ERROR_LOG" | grep -i emerg | tail -n 2)"
fi

# test the real answers from this machine (fresh connections, no browser cache)
if [ "${SKIP_LIVE_TEST:-0}" != "1" ] && command -v curl >/dev/null 2>&1; then
  http_www="$(curl -s -o /dev/null -w '%{http_code} %{redirect_url}' --max-time 15 --resolve www.fermi.uz:80:127.0.0.1 'http://www.fermi.uz/detail/x?a=1&b=2' || true)"
  https_www="$(curl -sk -o /dev/null -w '%{http_code} %{redirect_url}' --max-time 15 --resolve www.fermi.uz:443:127.0.0.1 'https://www.fermi.uz/detail/x?a=1&b=2' || true)"
  apex="$(curl -sk -o /dev/null -w '%{http_code}' --max-time 15 --resolve fermi.uz:443:127.0.0.1 'https://fermi.uz/' || true)"
  say "http://www.fermi.uz/detail/x?a=1&b=2  -> $http_www"
  say "https://www.fermi.uz/detail/x?a=1&b=2 -> $https_www"
  say "https://fermi.uz/                      -> $apex"
  [ "$http_www" = "301 https://fermi.uz/detail/x?a=1&b=2" ] || rollback "the http www answer is not the expected redirect."
  [ "$https_www" = "301 https://fermi.uz/detail/x?a=1&b=2" ] || rollback "the https www answer is not the expected redirect."
  [ "$apex" = "200" ] || rollback "fermi.uz itself no longer answers 200."
fi
say "DONE: www.fermi.uz now redirects to fermi.uz."
say "(to put the old file back: MODE=undo bash deploy/nginx/www-redirect.sh)"
