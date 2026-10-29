#!/usr/bin/env bash
# Nightly backup: database + private uploads. Run from cron as the 'pe' user, e.g.:
#   30 2 * * * /srv/professional_edge/deploy/backup.sh >> /var/log/pe-backup.log 2>&1
# Then COPY /srv/professional_edge/backups OFF this server (second location / cloud storage). A backup on the same
# machine is not enough. Test a restore regularly (docs/DEPLOYMENT.md).
set -euo pipefail
APP=/srv/professional_edge
set -a; source "$APP/.env"; set +a
STAMP=$(date +%Y%m%d-%H%M%S)
DEST="$APP/backups/$STAMP"
mkdir -p "$DEST"; chmod 700 "$APP/backups" "$DEST"

if [ -n "${DB_NAME:-}" ]; then
  PGPASSWORD="$DB_PASSWORD" pg_dump -h "${DB_HOST:-localhost}" -p "${DB_PORT:-5432}" -U "$DB_USER" "$DB_NAME" | gzip > "$DEST/db.sql.gz"
else
  cp "$APP/db.sqlite3" "$DEST/db.sqlite3"
fi
tar -czf "$DEST/private_media.tar.gz" -C "$APP" private_media 2>/dev/null || echo "no private_media yet"
find "$APP/backups" -mindepth 1 -maxdepth 1 -type d -mtime +14 -exec rm -rf {} +   # keep 14 days
echo "Backup complete: $DEST"
