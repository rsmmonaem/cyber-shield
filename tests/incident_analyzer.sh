#!/usr/bin/env bash
# ==============================================================================
# Per-Domain Resource Isolation & Request Protection Platform
# PHASE 27 — INCIDENT ANALYSIS & FORENSIC DIAGNOSTIC TOOL
# ==============================================================================
set -euo pipefail

echo "=================================================="
echo "   SYSTEM INCIDENT FORENSIC ANALYZER              "
echo "=================================================="

# 1. Inspect Socket Table & CLOSE-WAIT counts
echo "[1/4] Analyzing Active TCP Socket States..."
ss -t -a | awk '{print $1}' | sort | uniq -c | sort -nr || true

# 2. Check for OOM Kills in dmesg
echo -e "\n[2/4] Checking Out-Of-Memory (OOM) Kernel Events..."
dmesg 2>/dev/null | grep -i -E "oom|out of memory|killed process" | tail -n 10 || echo "No recent kernel OOM events recorded."

# 3. Check OpenLiteSpeed Error Logs for worker crashes or limits
echo -e "\n[3/4] Checking OpenLiteSpeed Error Log Snippets..."
if [ -f "/usr/local/lsws/logs/error.log" ]; then
    grep -i -E "error|warn|connection|limit" /usr/local/lsws/logs/error.log | tail -n 15 || echo "No critical OLS errors found."
else
    echo "OLS error log file /usr/local/lsws/logs/error.log not found."
fi

# 4. Check Top Process Resource Consumers
echo -e "\n[4/4] Top 5 Memory & CPU Processes:"
ps aux --sort=-%mem | head -n 6

echo -e "\n=================================================="
echo "[✓] Incident Forensic Audit Complete."
echo "=================================================="
