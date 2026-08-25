#!/usr/bin/env bash
# ==============================================================================
# Per-Domain Resource Isolation & Request Protection Platform
# PHASE 24 — PRODUCTION BACKUP & ROLLBACK FRAMEWORK
# ==============================================================================
set -euo pipefail

BACKUP_DIR="/var/backups/domain_isolation_platform/$(date +%Y%m%d_%H%M%S)"
echo "[+] Creating production pre-flight backup directory: $BACKUP_DIR" >&2
mkdir -p "$BACKUP_DIR"

# 1. Backup OpenLiteSpeed configuration
if [ -d "/usr/local/lsws/conf" ]; then
    echo "[+] Backing up OpenLiteSpeed configuration..." >&2
    tar -czf "$BACKUP_DIR/openlitespeed_conf.tar.gz" -C /usr/local/lsws conf 2>/dev/null || true
fi

# 2. Backup CyberPanel configuration
if [ -d "/usr/local/CyberCP" ]; then
    echo "[+] Backing up CyberPanel configuration..." >&2
    tar -czf "$BACKUP_DIR/cyberpanel_conf.tar.gz" -C /usr/local CyberCP 2>/dev/null || true
fi

# 3. Backup systemd slices & ulimits
echo "[+] Backing up systemd units & sysctl settings..." >&2
tar -czf "$BACKUP_DIR/systemd_slices.tar.gz" /etc/systemd/system/*.slice /etc/sysctl.conf /etc/security/limits.conf /etc/security/limits.d/ 2>/dev/null || true

echo "$BACKUP_DIR" > /tmp/latest_isolation_backup.txt
echo "[✓] Safety backup complete. Stored in $BACKUP_DIR" >&2
