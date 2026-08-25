#!/usr/bin/env bash
# ==============================================================================
# Per-Domain Resource Isolation & Request Protection Platform
# PHASE 2 — DOMAIN & RESOURCE OWNERSHIP DISCOVERY SCRIPT
# ==============================================================================
set -euo pipefail

OUTPUT_FILE="${1:-/tmp/domain_discovery_report.json}"
VHOST_DIR="/usr/local/lsws/conf/vhosts"
CYBERPANEL_DB="/var/lib/mysql/cyberpanel"

echo "[+] Starting Phase 2 Domain Inventory & Ownership Mapping..." >&2

DOMAINS_JSON="[]"

# Helper to find Linux user for a vHost
get_domain_user() {
    local domain="$1"
    local doc_root
    doc_root=$(grep -i "docRoot" "$VHOST_DIR/$domain/vhconf.conf" 2>/dev/null | head -n1 | awk '{print $2}' || echo "")
    if [ -n "$doc_root" ]; then return 0; fi
    # Fallback to checking owner of /home/$domain
    if [ -d "/home/$domain" ]; then
        stat -c '%U' "/home/$domain" 2>/dev/null || echo "nobody"
    else
        echo "nobody"
    fi
}

# Scan CyberPanel vHosts if directory exists
if [ -d "$VHOST_DIR" ]; then
    DOMAINS_LIST=$(ls -1 "$VHOST_DIR" 2>/dev/null || echo "")
else
    # Fallback to scan /home
    DOMAINS_LIST=$(ls -1 /home 2>/dev/null | grep '\.' || echo "")
fi

# Build array of domain objects
DOMAINS_ARRAY=()
for domain in $DOMAINS_LIST; do
    [ -z "$domain" ] && continue
    # Skip non-domain folders
    if [[ "$domain" == "cyberpanel" || "$domain" == "vmail" ]]; then continue; fi

    VHOST_CONF="$VHOST_DIR/$domain/vhconf.conf"
    DOC_ROOT="/home/$domain/public_html"
    
    # Extract owner user
    LINUX_USER=$(stat -c '%U' "$DOC_ROOT" 2>/dev/null || echo "$domain")

    # Extract PHP version from vhost conf or default
    LSPHP_VER=$(grep -i "lsphp" "$VHOST_CONF" 2>/dev/null | grep -o 'lsphp[0-9]*' | head -n1 || echo "lsphp81")

    # Detect Laravel installation
    IS_LARAVEL="false"
    if [ -f "/home/$domain/public_html/artisan" ] || [ -f "/home/$domain/artisan" ]; then
        IS_LARAVEL="true"
    fi

    # Detect running queue workers for user
    QUEUE_WORKERS=$(ps aux | grep -v grep | grep "$LINUX_USER" | grep "queue:work\|horizon" | wc -l || echo "0")

    # Detect active cron jobs for user
    CRON_COUNT=$(crontab -u "$LINUX_USER" -l 2>/dev/null | grep -v '^#' | grep -v '^$' | wc -l || echo "0")

    # Construct JSON snippet
    DOMAIN_ENTRY=$(cat <<EOF
{
  "domain": "$domain",
  "linux_user": "$LINUX_USER",
  "document_root": "$DOC_ROOT",
  "vhost_config": "$VHOST_CONF",
  "lsphp_version": "$LSPHP_VER",
  "is_laravel": $IS_LARAVEL,
  "queue_workers_active": $QUEUE_WORKERS,
  "cron_jobs_active": $CRON_COUNT
}
EOF
)
    DOMAINS_ARRAY+=("$DOMAIN_ENTRY")
done

# Output formatted JSON report
{
  echo "{"
  echo "  \"timestamp\": \"$(date -u +"%Y-%m-%dT%H:%M:%SZ")\","
  echo "  \"total_domains\": ${#DOMAINS_ARRAY[@]},"
  echo "  \"domains\": ["
  first=1
  for entry in "${DOMAINS_ARRAY[@]}"; do
      if [ $first -eq 1 ]; then
          first=0
      else
          echo ","
      fi
      echo "$entry"
  done
  echo ""
  echo "  ]"
  echo "}"
} > "$OUTPUT_FILE"

chmod +x "$OUTPUT_FILE" 2>/dev/null || true
echo "[+] Phase 2 Domain Inventory completed. Report written to $OUTPUT_FILE" >&2
cat "$OUTPUT_FILE"
