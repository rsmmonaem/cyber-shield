#!/usr/bin/env bash
# ==============================================================================
# Per-Domain Resource Isolation & Request Protection Platform
# PHASE 1 — FULL ENVIRONMENT DISCOVERY SCRIPT
# ==============================================================================
set -euo pipefail

OUTPUT_FILE="${1:-/tmp/system_discovery_report.json}"
TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

echo "[+] Starting Phase 1 Environment Discovery..." >&2

# Helper function to capture command output safely
safe_exec() {
    local cmd="$1"
    eval "$cmd" 2>/dev/null || echo "N/A"
}

# OS & Kernel Information
OS_NAME=$(safe_exec "cat /etc/os-release | grep '^PRETTY_NAME=' | cut -d= -f2 | tr -d '\"'")
KERNEL_VER=$(safe_exec "uname -r")
SYSTEMD_VER=$(safe_exec "systemctl --version | head -n1 | awk '{print \$2}'")

# cgroup Inspection
CGROUP_TYPE="v1"
if [ -f /sys/fs/cgroup/cgroup.controllers ]; then
    CGROUP_TYPE="v2"
    ACTIVE_CONTROLLERS=$(safe_exec "cat /sys/fs/cgroup/cgroup.controllers")
    ROOT_SUBTREE=$(safe_exec "cat /sys/fs/cgroup/cgroup.subtree_control")
else
    ACTIVE_CONTROLLERS="N/A"
    ROOT_SUBTREE="N/A"
fi

# CPU Topology
CPU_MODEL=$(safe_exec "grep -m1 'model name' /proc/cpuinfo | awk -F: '{print \$2}' | xargs")
CPU_CORES=$(safe_exec "nproc")
CPU_THREADS=$(safe_exec "lscpu | grep 'Thread(s) per core' | awk '{print \$4}'")

# Memory & Swap
RAM_TOTAL_BYTES=$(safe_exec "free -b | grep Mem: | awk '{print \$2}'")
RAM_TOTAL_HUMAN=$(safe_exec "free -h | grep Mem: | awk '{print \$2}'")
SWAP_TOTAL_BYTES=$(safe_exec "free -b | grep Swap: | awk '{print \$2}'")

# OpenLiteSpeed & CyberPanel
OLS_VER=$(safe_exec "/usr/local/lsws/bin/lswsctrl -v 2>&1 | head -n1" || echo "Not Found")
CYBERPANEL_VER=$(safe_exec "cat /usr/local/CyberCP/version.txt" || safe_exec "cat /usr/local/CyberCP/CyberCP/version.txt" || echo "Unknown")

# Installed LSPHP Versions
LSPHP_VERSIONS=$(safe_exec "ls -d /usr/local/lsws/lsphp* 2>/dev/null | tr '\n' ',' | sed 's/,$//'")

# Database & Services
MARIADB_STATUS=$(safe_exec "systemctl is-active mariadb || systemctl is-active mysql || echo inactive")
POSTGRES_STATUS=$(safe_exec "systemctl is-active postgresql || echo inactive")
REDIS_STATUS=$(safe_exec "systemctl is-active redis || systemctl is-active redis-server || echo inactive")
DOCKER_STATUS=$(safe_exec "systemctl is-active docker || echo inactive")

# Limits & Sysctl
FILE_MAX=$(safe_exec "sysctl -n fs.file-max")
SOMAXCONN=$(safe_exec "sysctl -n net.core.somaxconn")
MAX_ORPHANS=$(safe_exec "sysctl -n net.ipv4.tcp_max_orphans")
TW_REUSE=$(safe_exec "sysctl -n net.ipv4.tcp_tw_reuse")

# OpenLiteSpeed Configuration Check for Cloudflare Proxy IP
OLS_CF_PROXY=$(safe_exec "grep -i 'useIpInProxyHeader' /usr/local/lsws/conf/httpd_config.conf | head -n1" || echo "Not configured")

# Construct JSON Report
cat <<EOF > "$OUTPUT_FILE"
{
  "timestamp": "$TIMESTAMP",
  "environment": {
    "os_name": "$OS_NAME",
    "kernel_version": "$KERNEL_VER",
    "systemd_version": "$SYSTEMD_VER",
    "cgroup_version": "$CGROUP_TYPE",
    "cgroup_controllers": "$ACTIVE_CONTROLLERS",
    "cgroup_subtree_control": "$ROOT_SUBTREE"
  },
  "hardware": {
    "cpu_model": "$CPU_MODEL",
    "cpu_cores": $CPU_CORES,
    "ram_total_bytes": ${RAM_TOTAL_BYTES:-0},
    "ram_total_human": "$RAM_TOTAL_HUMAN",
    "swap_total_bytes": ${SWAP_TOTAL_BYTES:-0}
  },
  "hosting_stack": {
    "openlitespeed_version": "$OLS_VER",
    "cyberpanel_version": "$CYBERPANEL_VER",
    "lsphp_versions": "$LSPHP_VERSIONS",
    "mariadb_status": "$MARIADB_STATUS",
    "postgresql_status": "$POSTGRES_STATUS",
    "redis_status": "$REDIS_STATUS",
    "docker_status": "$DOCKER_STATUS",
    "ols_cloudflare_proxy_setting": "$OLS_CF_PROXY"
  },
  "kernel_limits": {
    "fs_file_max": "$FILE_MAX",
    "net_core_somaxconn": "$SOMAXCONN",
    "net_ipv4_tcp_max_orphans": "$MAX_ORPHANS",
    "net_ipv4_tcp_tw_reuse": "$TW_REUSE"
  }
}
EOF

echo "[+] Phase 1 Discovery completed. Report written to $OUTPUT_FILE" >&2
cat "$OUTPUT_FILE"
