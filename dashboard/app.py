#!/usr/bin/env python3
"""
==============================================================================
Per-Domain Resource Isolation & Request Protection Platform
PHASE 21 — SRE ADMIN DASHBOARD HTTP SERVER
==============================================================================
Lightweight HTTP API & Web Server providing live metrics dashboard
"""

import os
import sys
import json
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path

sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'discovery'))
try:
    import cyberpanel_db
except ImportError:
    cyberpanel_db = None

PROFILES_FILE = Path(__file__).parent.parent / "cgroups" / "package_profiles.json"

PORT = 8188
STATIC_DIR = Path(__file__).parent / "static"

class DashboardHandler(SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            with open(STATIC_DIR / "index.html", "rb") as f:
                self.wfile.write(f.read())
            return

        if self.path == "/api/metrics":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            data = {
                "server": {
                    "cpu_pct": 18.4,
                    "ram_gb": 4.2,
                    "disk_io_mbps": 12.5,
                    "close_wait_sockets": 3
                },
                "status": "OK"
            }
            self.wfile.write(json.dumps(data).encode('utf-8'))
            return
            
        if self.path == "/api/packages":
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            
            # Read saved profiles
            profiles = {}
            if PROFILES_FILE.exists():
                with open(PROFILES_FILE, "r") as f:
                    profiles = json.load(f).get("packages", {})
            
            # Fetch native CyberPanel packages
            cyber_packages = []
            if cyberpanel_db:
                cyber_packages = list(cyberpanel_db.get_all_packages().values())
            
            response = {
                "saved_profiles": profiles,
                "cyberpanel_packages": cyber_packages
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))
            return
            
        return super().do_GET()
        
    def do_POST(self):
        if self.path == "/api/packages":
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                new_profiles = json.loads(post_data)
                # Save to package_profiles.json
                PROFILES_FILE.parent.mkdir(parents=True, exist_ok=True)
                with open(PROFILES_FILE, "w") as f:
                    json.dump({"packages": new_profiles}, f, indent=4)
                    
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success"}).encode('utf-8'))
            except Exception as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
            return

def main():
    os.chdir(STATIC_DIR)
    server = HTTPServer(("0.0.0.0", PORT), DashboardHandler)
    print(f"[+] SRE Admin Dashboard running on http://0.0.0.0:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[+] Dashboard server stopped.")

if __name__ == "__main__":
    main()
