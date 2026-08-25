#!/usr/bin/env python3
"""
==============================================================================
Per-Domain Resource Isolation & Request Protection Platform
PHASE 3 — SYSTEMD CGROUP V2 SLICE GENERATOR
==============================================================================
Creates hierarchical systemd slices for multi-tenant hosting:
  server.slice
      └── hosting.slice
            ├── package-basic.slice
            │     ├── domain-a.slice
            │     └── domain-b.slice
            ├── package-business.slice
            └── package-enterprise.slice
"""

import os
import sys
import json
import argparse
from pathlib import Path

SYSTEMD_DIR = Path("/etc/systemd/system")

def create_slice_file(slice_name: str, parent_slice: str = None, properties: dict = None, dry_run: bool = False):
    filename = f"{slice_name}.slice"
    file_path = SYSTEMD_DIR / filename
    
    content = ["[Unit]", f"Description=Domain Isolation Slice - {slice_name}", "Documentation=https://github.com/cyberpanel/openlitespeed"]
    
    if parent_slice:
        content.append(f"Slice={parent_slice}.slice")
        
    content.append("\n[Slice]")
    if properties:
        for key, value in properties.items():
            content.append(f"{key}={value}")
            
    content_str = "\n".join(content) + "\n"
    
    if dry_run:
        print(f"[+] Slice Config for {filename}:")
        print("--------------------------------------------------")
        print(content_str)
        print("--------------------------------------------------")
    
    if not dry_run:
        SYSTEMD_DIR.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content_str)
        print(f"[✓] Written to {file_path}")

def main():
    parser = argparse.ArgumentParser(description="Generate systemd slices for domain isolation")
    parser.add_argument("--domain-report", default="/tmp/domain_discovery_report.json", help="Path to domain discovery JSON")
    default_profiles = os.path.join(os.path.dirname(os.path.abspath(__file__)), "package_profiles.json")
    parser.add_argument("--profiles", default=default_profiles, help="Path to package profiles JSON")
    parser.add_argument("--dry-run", action="store_true", help="Print slice unit configurations without writing to /etc/systemd/system")
    args = parser.parse_args()

    # Load package profiles
    if os.path.exists(args.profiles):
        with open(args.profiles, 'r') as f:
            profiles = json.load(f).get("packages", {})
    else:
        print(f"[!] Warning: Profiles file {args.profiles} not found. Using defaults.")
        profiles = {}

    # 1. Base hosting slice
    create_slice_file("hosting", parent_slice=None, properties={
        "MemoryAccounting": "yes",
        "CPUAccounting": "yes",
        "IOAccounting": "yes",
        "TasksAccounting": "yes"
    }, dry_run=args.dry_run)

    # 2. Package Slices
    for pkg_id, pkg_data in profiles.items():
        slice_id = f"package-{pkg_id}"
        props = {
            "CPUWeight": pkg_data.get("cpu_weight", 100),
            "TasksMax": pkg_data.get("tasks_max", 50),
            "MemoryHigh": pkg_data.get("memory_high", "1.8G"),
            "MemoryMax": pkg_data.get("memory_max", "2G")
        }
        create_slice_file(slice_id, parent_slice="hosting", properties=props, dry_run=args.dry_run)

    # 3. Domain Slices
    if os.path.exists(args.domain_report):
        with open(args.domain_report, 'r') as f:
            data = json.load(f)
            domains = data.get("domains", [])
            for item in domains:
                dom_name = item.get("domain")
                sanitized_name = dom_name.replace(".", "-").replace("_", "-")
                slice_name = f"domain-{sanitized_name}"
                # Default assign to package-business slice
                create_slice_file(slice_name, parent_slice="package-business", properties={
                    "MemoryHigh": "1.8G",
                    "MemoryMax": "2G",
                    "CPUQuota": "200%",
                    "TasksMax": 50
                }, dry_run=args.dry_run)

    print("\n[+] Slice generation completed.")
    if not args.dry_run:
        print("[!] Run 'systemctl daemon-reload' to load the new slices on the server.")

if __name__ == "__main__":
    main()
