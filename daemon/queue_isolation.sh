#!/usr/bin/env bash
# ==============================================================================
# Per-Domain Resource Isolation & Request Protection Platform
# PHASE 14 — QUEUE WORKER & BACKGROUND PROCESS ISOLATION SCRIPT
# ==============================================================================
set -euo pipefail

echo "[+] Scanning for domain background workers (Laravel Queue, Horizon, Scheduler, Cron)..." >&2

# Helper function to move a process into a systemd domain slice
move_pid_to_slice() {
    local pid="$1"
    local domain="$2"
    local sanitized_domain
    sanitized_domain=$(echo "$domain" | tr '.' '-' | tr '_' '-')
    local slice_name="domain-${sanitized_domain}.slice"
    local cgroup_path="/sys/fs/cgroup/hosting.slice/package-business.slice/${slice_name}/cgroup.procs"

    if [ -f "$cgroup_path" ]; then
        echo "$pid" > "$cgroup_path" 2>/dev/null || true
        echo "[✓] Moved PID $pid to $slice_name" >&2
    fi
}

# Scan running artisan queue processes
ps aux | grep -v grep | grep "artisan queue:work\|horizon" | while read -r line; do
    user=$(echo "$line" | awk '{print $1}')
    pid=$(echo "$line" | awk '{print $2}')
    cmd=$(echo "$line" | awk '{for(i=11;i<=NF;i++) printf "%s ", $i}')
    
    # Infer domain from user or document root path in cmd
    domain=$(echo "$cmd" | grep -o '/home/[^/]*' | cut -d'/' -f3 || echo "")
    if [ -z "$domain" ]; then
        domain="$user"
    fi
    
    if [ -n "$domain" ]; then
        echo "[+] Found background worker process: PID=$pid, User=$user, Domain=$domain" >&2
        move_pid_to_slice "$pid" "$domain"
    fi
done

echo "[+] Queue worker isolation scan complete." >&2
