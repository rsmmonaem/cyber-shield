#!/usr/bin/env bash
# ==============================================================================
# Per-Domain Resource Isolation & Request Protection Platform
# AUTOMATED INSTALLER FOR CYBERPANEL (ALMALINUX 9)
# ==============================================================================
set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}====================================================================${NC}"
echo -e "${GREEN}  Installing Per-Domain Resource Isolation & Protection Platform  ${NC}"
echo -e "${GREEN}====================================================================${NC}"

# 1. Check Root Privileges
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}[!] Please run as root.${NC}"
  exit 1
fi

# 2. Check OS (AlmaLinux 9 recommended)
if [ -f /etc/os-release ]; then
    . /etc/os-release
    echo -e "${GREEN}[+] Detected OS: $PRETTY_NAME${NC}"
else
    echo -e "${YELLOW}[!] WARNING: Cannot detect OS. Proceeding anyway...${NC}"
fi

# 3. Define installation directory
INSTALL_DIR="/root/cyber-shield"
REPO_URL="https://github.com/rsmmonaem/cyber-shield.git"

echo -e "${GREEN}[+] Setting up installation directory at $INSTALL_DIR...${NC}"

# 4. Clone or update repository
if [ -d "$INSTALL_DIR" ]; then
    echo -e "${YELLOW}[+] Directory exists. Pulling latest updates...${NC}"
    cd "$INSTALL_DIR"
    git pull || true
else
    # If git is not installed, install it
    if ! command -v git &> /dev/null; then
        echo -e "${YELLOW}[+] Installing git...${NC}"
        dnf install -y git
    fi
    # Wait, for this local script to work when run locally, we just assume files are there if not cloned
    # We will provide instructions in README for curl bash installation
    if [ ! -d "/Users/rsmmonaem/.gemini/antigravity/scratch/domain-isolation-platform" ]; then
        git clone "$REPO_URL" "$INSTALL_DIR"
    else
        # Local testing: copy from workspace if running locally
        cp -r "$(pwd)" "$INSTALL_DIR" 2>/dev/null || true
    fi
fi

cd "$INSTALL_DIR"

# 5. Set executable permissions
echo -e "${GREEN}[+] Setting permissions...${NC}"
chmod +x discovery/*.sh cgroups/*.py ols_protection/*.py socket_monitor/*.py daemon/*.sh daemon/*.py dashboard/*.py safety/*.sh tests/*.sh install.sh

# 6. Run Pre-flight Discovery and Backup (Observe Mode)
echo -e "${GREEN}[+] Running Pre-Flight Backup and Discovery...${NC}"
./safety/deploy_platform.sh observe

# 7. Apply Systemd Slices
echo -e "${GREEN}[+] Applying Systemd Slices...${NC}"
python3 cgroups/slice_generator.py --domain-report /tmp/domain_discovery_report.json
systemctl daemon-reload

# 8. Configure OpenLiteSpeed
echo -e "${GREEN}[+] Configuring OpenLiteSpeed Request Protection...${NC}"
python3 ols_protection/ols_rule_generator.py --output-dir /usr/local/lsws/conf/
if ! grep -q "ols_global_security.conf" /usr/local/lsws/conf/httpd_config.conf; then
    echo "include /usr/local/lsws/conf/ols_global_security.conf" >> /usr/local/lsws/conf/httpd_config.conf
fi
echo -e "${GREEN}[+] Restarting OpenLiteSpeed gracefully...${NC}"
/usr/local/lsws/bin/lswsctrl test || true
/usr/local/lsws/bin/lswsctrl restart || true

# 9. Install Systemd Services
echo -e "${GREEN}[+] Installing Domain Guardian & Dashboard Services...${NC}"

cat <<EOF > /etc/systemd/system/domain-guardian.service
[Unit]
Description=Domain Guardian Resource Isolation & Policy Daemon
After=network.target lsws.service

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/daemon/domain_guardian.py --mode enforce --interval 10
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

cat <<EOF > /etc/systemd/system/domain-dashboard.service
[Unit]
Description=SRE Domain Isolation Admin Dashboard
After=network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 $INSTALL_DIR/dashboard/app.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

# 10. Enable and Start Services
echo -e "${GREEN}[+] Starting background services...${NC}"
systemctl daemon-reload
systemctl enable --now domain-guardian
systemctl enable --now domain-dashboard

# 11. Final Instructions
SERVER_IP=$(curl -s http://checkip.amazonaws.com || hostname -I | awk '{print $1}')
echo -e "${GREEN}====================================================================${NC}"
echo -e "${GREEN}                  INSTALLATION COMPLETE!                            ${NC}"
echo -e "${GREEN}====================================================================${NC}"
echo -e ""
echo -e "The Domain Isolation Platform is now running in ENFORCE mode."
echo -e ""
echo -e "Dashboard URL : http://$SERVER_IP:8088"
echo -e "Installation  : $INSTALL_DIR"
echo -e "Rollback CMD  : $INSTALL_DIR/safety/rollback.sh"
echo -e ""
echo -e "To test failure containment on a domain, run:"
echo -e "  $INSTALL_DIR/tests/failure_injector.sh <domain_name> cpu 15"
echo -e "${GREEN}====================================================================${NC}"
