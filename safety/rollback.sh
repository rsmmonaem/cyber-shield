#!/usr/bin/env bash
# ==============================================================================
# Per-Domain Resource Isolation & Request Protection Platform
# PHASE 24 — PRODUCTION EMERGENCY ROLLBACK SCRIPT
# ==============================================================================
set -euo pipefail

if [ ! -f "/tmp/latest_isolation_backup.txt" ]; then
    echo "[!] Error: No backup reference found in /tmp/latest_isolation_backup.txt" >&2
    exit 1
fi

BACKUP_DIR=$(cat /tmp/latest_isolation_backup.txt)
echo "[!] EMERGENCY ROLLBACK INITIATED using backup: $BACKUP_DIR" >&2

if [ -f "$BACKUP_DIR/openlitespeed_conf.tar.gz" ]; then
    echo "[+] Restoring OpenLiteSpeed configuration..." >&2
    tar -xzf "$BACKUP_DIR/openlitespeed_conf.tar.gz" -C /usr/local/lsws/
fi

if [ -f "$BACKUP_DIR/systemd_slices.tar.gz" ]; then
    echo "[+] Restoring systemd & limits configuration..." >&2
    tar -xzf "$BACKUP_DIR/systemd_slices.tar.gz" -C /
    systemctl daemon-reload || true
fi

echo "[+] Restarting OpenLiteSpeed gracefully..." >&2
/usr/local/lsws/bin/lswsctrl restart 2>/dev/null || true

echo "[✓] Rollback completed successfully." >&2
