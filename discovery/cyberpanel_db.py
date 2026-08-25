#!/usr/bin/env python3
"""
==============================================================================
Per-Domain Resource Isolation & Request Protection Platform
CYBERPANEL DATABASE INTEGRATION MODULE
==============================================================================
Reads package and domain assignments natively from CyberPanel's MariaDB.
"""

import os
import subprocess
import json

DB_PASS_FILE = "/root/.db_password"

def get_db_password() -> str:
    """Reads the CyberPanel MySQL password"""
    if os.path.exists(DB_PASS_FILE):
        with open(DB_PASS_FILE, "r") as f:
            return f.read().strip()
    return ""

def query_db(query: str) -> list:
    """Executes a MySQL query and returns a list of dictionaries (TSV parsing)"""
    password = get_db_password()
    if not password:
        # Try running as root without password (works on some setups via unix_socket)
        cmd = ["mysql", "cyberpanel", "-e", query, "--batch"]
    else:
        cmd = ["mysql", "-u", "cyberpanel", f"-p{password}", "cyberpanel", "-e", query, "--batch"]
    
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    except subprocess.CalledProcessError as e:
        print(f"[!] Database Query Error: {e.stderr}")
        return []
    
    lines = res.stdout.strip().splitlines()
    if not lines:
        return []
    
    # First line is headers
    headers = lines[0].split("\t")
    results = []
    
    for line in lines[1:]:
        values = line.split("\t")
        row = dict(zip(headers, values))
        results.append(row)
        
    return results

def get_all_packages() -> dict:
    """Returns a dictionary of {package_id: package_name}"""
    rows = query_db("SELECT id, packageName FROM packages_package")
    return {row["id"]: row["packageName"] for row in rows}

def get_domain_package_mapping() -> dict:
    """Returns a dictionary mapping domain name to package name"""
    query = """
    SELECT w.domain, p.packageName 
    FROM websiteFunctions_websites w
    LEFT JOIN packages_package p ON w.package_id = p.id
    WHERE w.state = 1
    """
    rows = query_db(query)
    mapping = {}
    for row in rows:
        dom = row.get("domain")
        pkg = row.get("packageName")
        if dom and pkg:
            mapping[dom] = pkg
    return mapping

if __name__ == "__main__":
    print("[+] CyberPanel Packages:")
    print(json.dumps(get_all_packages(), indent=2))
    print("\n[+] Domain to Package Mapping:")
    print(json.dumps(get_domain_package_mapping(), indent=2))
