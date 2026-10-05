#!/usr/bin/env bash
# Nightly safety copy of the uploaded files (media/): photos, PDFs, documents.
#
# The database dump (backup-db.sh) does NOT contain the files themselves, only their names. Editors can
# delete a photo or a PDF in the admin panel and the file disappears from disk -- this keeps a second copy.
# It is an additive mirror on purpose (no --delete): a file removed from media/ later still survives here.
# That grows slowly; prune old, unwanted files by hand now and then (see DEPLOYMENT.md).
#
# Same-disk copies protect against mistakes, not against a dead disk: also copy /var/backups/fermi-django
# off the server (another machine or a cloud drive) regularly.
set -euo pipefail

MEDIA_DIR="${MEDIA_DIR:-/home/fermi-django/media}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/fermi-django}"
DEST="$BACKUP_DIR/media-mirror"

mkdir -p "$DEST"

# Safety: never let the mirror fill the disk the site itself runs on. Needs room for twice the media size.
need_kb=$(( $(du -sk "$MEDIA_DIR" | cut -f1) * 2 ))
free_kb=$(df -Pk "$BACKUP_DIR" | awk 'NR==2 {print $4}')
if [ "$free_kb" -lt "$need_kb" ]; then
    echo "backup-media.sh: not enough free disk space (${free_kb} KB free, ${need_kb} KB needed) -- skipped" >&2
    exit 1
fi

rsync -a "$MEDIA_DIR/" "$DEST/"
echo "backup-media.sh: mirrored $MEDIA_DIR -> $DEST ($(du -sh "$DEST" | cut -f1))"
