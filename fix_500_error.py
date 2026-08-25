import os
import subprocess

def remove_duplicates(filepath, string_to_remove):
    if not os.path.exists(filepath):
        return
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    with open(filepath, 'w') as f:
        for line in lines:
            if string_to_remove not in line:
                f.write(line)

print("Fixing CyberPanel 500 Error...")
remove_duplicates('/usr/local/CyberCP/CyberCP/settings.py', 'domainIsolationPlugin')
remove_duplicates('/usr/local/CyberCP/CyberCP/urls.py', 'domainIsolationPlugin')

print("Reinstalling Domain Isolation Plugin cleanly...")
os.chdir('/usr/local/CyberCP/pluginInstaller')
subprocess.run(['python3', 'pluginInstaller.py', 'install', '--pluginName', 'domainIsolationPlugin'])

print("Restarting CyberPanel Daemon...")
subprocess.run(['systemctl', 'restart', 'lscpd'])
print("Done! You can now check CyberPanel!")
