#!/bin/bash
# ==============================================================================
# CyberPanel Native Addon Bypass & Rollback Tool
# ==============================================================================
# This script safely modifies CyberPanel's PackagesManager to enable the 
# native "Advanced Resource Limits" (CPU/RAM) UI on the Create Package screen
# without requiring a paid CyberPanel Addon subscription.
# ==============================================================================

FILE_PATH="/usr/local/CyberCP/packages/packagesManager.py"
BACKUP_PATH="/usr/local/CyberCP/packages/packagesManager.py.bak"

if [ "$1" == "rollback" ]; then
    echo "[+] Initiating Safe Rollback..."
    if [ -f "$BACKUP_PATH" ]; then
        cp "$BACKUP_PATH" "$FILE_PATH"
        systemctl restart lscpd
        echo "[✓] Rollback successful. Original CyberPanel files restored."
    else
        echo "[!] Error: Backup file not found at $BACKUP_PATH. Cannot rollback."
    fi
    exit 0
fi

echo "[+] Starting CyberPanel Native Integration Patch..."

if [ ! -f "$FILE_PATH" ]; then
    echo "[!] Error: $FILE_PATH does not exist. Are you sure CyberPanel is installed?"
    exit 1
fi

# 1. Create a safe backup
if [ ! -f "$BACKUP_PATH" ]; then
    cp "$FILE_PATH" "$BACKUP_PATH"
    echo "[✓] Created backup at $BACKUP_PATH"
else
    echo "[i] Backup already exists at $BACKUP_PATH, skipping backup."
fi

# 2. Patch the checkAddonAccess function using Python AST or simple text replacement
# The function typically looks like:
#     @staticmethod
#     def checkAddonAccess():
#         ...
#         return (Status == 1) or (ProcessUtilities.decideServer() == ProcessUtilities.ent)

echo "[+] Patching checkAddonAccess() to always return True..."
# Use python to precisely patch the file
python3 -c "
import sys
with open('$FILE_PATH', 'r') as f:
    lines = f.readlines()

new_lines = []
in_addon_func = False
patched = False

for line in lines:
    if 'def checkAddonAccess' in line:
        in_addon_func = True
        new_lines.append(line)
        new_lines.append('        return True\\n')
        patched = True
        continue
        
    if in_addon_func:
        # Skip the original body of checkAddonAccess until we hit the next def or unindented code
        if line.strip() == '' or line.startswith('        ') or line.startswith('    \"\"\"') or line.startswith('    #'):
            continue
        else:
            in_addon_func = False
            
    new_lines.append(line)

if patched:
    with open('$FILE_PATH', 'w') as f:
        f.writelines(new_lines)
    print('[✓] Patch applied successfully.')
else:
    print('[!] Failed to locate checkAddonAccess() function.')
    sys.exit(1)
"

if [ $? -eq 0 ]; then
    echo "[+] Restarting CyberPanel Daemon (lscpd)..."
    systemctl restart lscpd
    echo "=============================================================================="
    echo " SUCCESS! CyberPanel Native Resource Limits Unlocked."
    echo " -> Go to CyberPanel -> Packages -> Create Package"
    echo " -> You will now see 'Advanced Resource Limits' natively!"
    echo " "
    echo " To rollback these changes safely, run:"
    echo " bash $0 rollback"
    echo "=============================================================================="
else
    echo "[!] Patching failed. Restoring from backup..."
    cp "$BACKUP_PATH" "$FILE_PATH"
    exit 1
fi
