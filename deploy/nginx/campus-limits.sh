#!/usr/bin/env bash
# Raises fermi.uz's nginx rate limits so a whole campus behind ONE public address can use the site.
#
# Why: every limit below counts per client IP, and the institute's Wi-Fi shows up as a single IP. The old values stopped
# about 4 browsers loading the site at once (limit_conn 25), 2-3 page loads in a second (15 requests/second) and let only
# 10 + 5-per-minute applications through the whole campus (the forms share the "sensitive" zone with login).
#
#   limit_conn fermi_per_ip      25        -> 400
#   limit_req  fermi_general     15r/s b60 -> 100r/s b400
#   /api/v1/forms/  (applications)  5r/m b10 (shared with login) -> its own zone, 120r/m b60
#   /api/v1/auth/   (login etc.)    5r/m b10 -> unchanged (brute-force protection stays as strict as before)
#
# Touches ONLY the two fermi files below, never another site's config. The server is shared (about 50 sites), so:
# it backs both files up, runs `nginx -t`, puts the old files back by itself if the test fails, and only then does a
# graceful `reload` (no dropped connections).
#
#   bash deploy/nginx/campus-limits.sh              # MODE=dry: shows the diff, changes nothing
#   MODE=apply bash deploy/nginx/campus-limits.sh
#   MODE=undo  bash deploy/nginx/campus-limits.sh   # puts the newest backup back
#
# Paths and commands can be overridden for testing: ZONES_FILE, VHOST_FILE, BACKUP_ROOT, NGINX_BIN, RELOAD_CMD.
set -euo pipefail

MODE="${MODE:-dry}"
ZONES_FILE="${ZONES_FILE:-/etc/nginx/conf.d/fermi-rate-limits.conf}"
VHOST_FILE="${VHOST_FILE:-/etc/nginx/sites-enabled/fermi-django-frontend}"
BACKUP_ROOT="${BACKUP_ROOT:-/root/nginx-fermi-backup}"
NGINX_BIN="${NGINX_BIN:-nginx}"
RELOAD_CMD="${RELOAD_CMD:-systemctl reload nginx}"

say() { printf '%s\n' "$*"; }
die() { say "STOP: $*"; exit 1; }

nginx_ok() {
  local out
  if out="$($NGINX_BIN -t 2>&1)"; then return 0; fi
  say "$out"
  return 1
}

restore_from() {
  local dir="$1"
  cat "$dir/fermi-rate-limits.conf" > "$ZONES_FILE"
  cat "$dir/fermi-django-frontend" > "$VHOST_FILE"
}

[ -f "$ZONES_FILE" ] || die "$ZONES_FILE not found."
[ -f "$VHOST_FILE" ] || die "$VHOST_FILE not found."

if [ "$MODE" = "undo" ]; then
  latest="$(ls -1d "$BACKUP_ROOT"/*/ 2>/dev/null | sort | tail -n 1 || true)"
  [ -n "$latest" ] || die "no backup found in $BACKUP_ROOT."
  restore_from "${latest%/}"
  nginx_ok || die "nginx -t failed after restoring ${latest}; fix by hand before reloading."
  $RELOAD_CMD
  say "UNDONE: the files from ${latest} are back and nginx was reloaded."
  exit 0
fi

[ "$MODE" = "dry" ] || [ "$MODE" = "apply" ] || die "MODE must be dry, apply or undo."

# the current files must still be exactly what this script was written for
grep -qF 'limit_req_zone $binary_remote_addr zone=fermi_general:10m rate=15r/s;' "$ZONES_FILE" || die "fermi_general zone is not the expected 15r/s line (already changed?). Nothing was modified."
grep -qF 'zone=fermi_sensitive:10m rate=5r/m;' "$ZONES_FILE" || die "fermi_sensitive zone is not the expected line. Nothing was modified."
grep -qF 'limit_conn fermi_per_ip 25;' "$VHOST_FILE" || die "limit_conn is not the expected 'fermi_per_ip 25' (already changed?). Nothing was modified."
grep -qF 'limit_req zone=fermi_general burst=60 nodelay;' "$VHOST_FILE" || die "limit_req fermi_general is not the expected 'burst=60'. Nothing was modified."
[ "$(grep -cF 'limit_req zone=fermi_sensitive burst=10 nodelay;' "$VHOST_FILE")" = "1" ] || die "the fermi_sensitive limit_req line is not there exactly once. Nothing was modified."

work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

cat > "$work/zones" <<'EOF'
# Per-IP limits for fermi.uz. A whole campus can share ONE public address, so the numbers are generous: they stop real
# floods (thousands of requests per second from one address), not a classroom opening the site together.
limit_req_zone $binary_remote_addr zone=fermi_general:10m rate=100r/s;
limit_conn_zone $binary_remote_addr zone=fermi_per_ip:10m;

# Login/register/refresh (/api/v1/auth/) keep the strict limit, and applications (/api/v1/forms/) get their own, so a
# class of students submitting does not eat the login allowance. A request whose key is empty is not counted by the zone.
map $uri $fermi_auth_key {
    default "";
    ~^/api/v1/auth/ $binary_remote_addr;
}
map $uri $fermi_forms_key {
    default "";
    ~^/api/v1/forms/ $binary_remote_addr;
}
limit_req_zone $fermi_auth_key zone=fermi_sensitive:10m rate=5r/m;
limit_req_zone $fermi_forms_key zone=fermi_forms:10m rate=120r/m;
EOF

sed -e 's/limit_conn fermi_per_ip 25;/limit_conn fermi_per_ip 400;/' \
    -e 's/limit_req zone=fermi_general burst=60 nodelay;/limit_req zone=fermi_general burst=400 nodelay;/' \
    -e 's/^\([[:space:]]*\)limit_req zone=fermi_sensitive burst=10 nodelay;/&\n\1limit_req zone=fermi_forms burst=60 nodelay;/' \
    "$VHOST_FILE" > "$work/vhost"

say "MODE: $MODE"
say "=== $ZONES_FILE"
diff -u "$ZONES_FILE" "$work/zones" || true
say
say "=== $VHOST_FILE"
diff -u "$VHOST_FILE" "$work/vhost" || true
say

if [ "$MODE" = "dry" ]; then
  say "DRY RUN: nothing was changed. Run again with MODE=apply to put these in place."
  exit 0
fi

stamp="$(date +%Y%m%d-%H%M%S)"
backup="$BACKUP_ROOT/$stamp"
mkdir -p "$backup"
cat "$ZONES_FILE" > "$backup/fermi-rate-limits.conf"
cat "$VHOST_FILE" > "$backup/fermi-django-frontend"
say "backup: $backup"

cat "$work/zones" > "$ZONES_FILE"
cat "$work/vhost" > "$VHOST_FILE"

if ! nginx_ok; then
  restore_from "$backup"
  say "ROLLED BACK: nginx -t failed with the new limits, the old files are back and nginx was NOT reloaded."
  exit 1
fi

$RELOAD_CMD
say "DONE: nginx reloaded with the campus-friendly limits."
say "(to put the old limits back: MODE=undo bash deploy/nginx/campus-limits.sh)"
