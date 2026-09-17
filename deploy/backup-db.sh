#!/usr/bin/env bash
# Nightly Postgres backup for the FerMI database. Normally run via
# deploy/systemd/fermi-django-backup.timer (see DEPLOYMENT.md), which uses
# the service unit's own EnvironmentFile= to hand this script its DB_*
# variables (that unit runs as www-data, which -- like this script run
# standalone -- can't read the root-owned, chmod 600 env file directly).
#
# For a manual test run, either `sudo systemctl start
# fermi-django-backup.service` (goes through the same EnvironmentFile= path),
# or `sudo deploy/backup-db.sh` as root, which *can* read the env file and
# will source it itself below.
#
# Writes timestamped pg_dump custom-format archives to BACKUP_DIR and deletes
# ones older than RETENTION_DAYS.
set -euo pipefail

ENV_FILE="${FERMI_ENV_FILE:-/etc/fermi-django.env}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/fermi-django}"
RETENTION_DAYS="${RETENTION_DAYS:-14}"

# Only needed when DB_* isn't already in the environment (i.e. not launched
# via the systemd unit's EnvironmentFile=) -- skip it rather than fail when
# running as a user that can't read the root-only env file.
if [ -z "${DB_NAME:-}" ] && [ -r "$ENV_FILE" ]; then
    set -a
    # shellcheck disable=SC1090
    source "$ENV_FILE"
    set +a
fi

for var in DB_NAME DB_USER DB_PASSWORD DB_HOST DB_PORT; do
    if [ -z "${!var:-}" ]; then
        echo "backup-db.sh: $var is not set in $ENV_FILE" >&2
        exit 1
    fi
done

mkdir -p "$BACKUP_DIR"

timestamp="$(date -u +%Y%m%dT%H%M%SZ)"
dest="$BACKUP_DIR/${DB_NAME}_${timestamp}.dump"
tmp_dest="${dest}.in-progress"

export PGPASSWORD="$DB_PASSWORD"
pg_dump -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -F c -f "$tmp_dest"
mv "$tmp_dest" "$dest"
echo "backup-db.sh: wrote $dest"

# Prune anything past retention. -mtime +N means "older than N days", so
# yesterday's dump always survives even with RETENTION_DAYS=1.
find "$BACKUP_DIR" -maxdepth 1 -name "${DB_NAME}_*.dump" -mtime "+${RETENTION_DAYS}" -print -delete
