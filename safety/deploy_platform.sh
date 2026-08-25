#!/usr/bin/env bash
# ==============================================================================
# Per-Domain Resource Isolation & Request Protection Platform
# PHASE 25 — PRODUCTION DEPLOYMENT & ROLLOUT RUNNER
# ==============================================================================
set -euo pipefail

MODE="${1:-observe}"

echo "=================================================="
echo "   DEPLOYING DOMAIN ISOLATION PLATFORM            "
echo "   MODE: ${MODE^^}                                "
echo "=================================================="

BASE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Step 1: Pre-flight Safety Backup
echo "[1/5] Running Safety Backup..."
"$BASE_DIR/safety/backup_manager.sh"

# Step 2: System & Domain Discovery
echo "[2/5] Running Environment & Domain Discovery..."
"$BASE_DIR/discovery/discover_system.sh" /tmp/system_discovery_report.json
"$BASE_DIR/discovery/discover_domains.sh" /tmp/domain_discovery_report.json

# Step 3: Generate Systemd Slices
echo "[3/5] Generating Systemd cgroup v2 Slices..."
python3 "$BASE_DIR/cgroups/slice_generator.py" --domain-report /tmp/domain_discovery_report.json --dry-run

# Step 4: Generate OLS Security & Endpoint Protection
echo "[4/5] Generating OpenLiteSpeed Security Rules..."
python3 "$BASE_DIR/ols_protection/ols_rule_generator.py" --output-dir /tmp/ols_protection

# Step 5: Start Domain Guardian Daemon
echo "[5/5] Launching Domain Guardian Daemon in MODE=${MODE}..."
python3 "$BASE_DIR/daemon/domain_guardian.py" --mode "$MODE" --once

echo "=================================================="
echo "[✓] DEPLOYMENT STAGE COMPLETED IN MODE: ${MODE^^}"
echo "=================================================="
