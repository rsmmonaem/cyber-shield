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
    """Returns a dictionary of package configurations from CyberPanel"""
    # Fetch native limits as well
    query = "SELECT id, packageName, memoryLimitMB, cpuCores, ioLimitMBPS, procHardLimit FROM packages_package"
    rows = query_db(query)
    packages = {}
    for row in rows:
        pkg_name = row.get("packageName")
        if not pkg_name:
            continue
            
        # Parse limits and handle 0 as 'unlimited'
        mem_limit = int(row.get('memoryLimitMB', '1024'))
        if mem_limit == 0:
            memory_high = "infinity"
            memory_max = "infinity"
        else:
            memory_high = f"{mem_limit}M"
            memory_max = f"{mem_limit + 256}M"
            
        cpu_cores = int(row.get("cpuCores", "1"))
        cpu_weight = 100 if cpu_cores == 0 else cpu_cores * 100
        
        proc_limit = int(row.get("procHardLimit", "500"))
        tasks_max = "infinity" if proc_limit == 0 else proc_limit
        
        io_limit = int(row.get("ioLimitMBPS", "10"))
        io_limit_mbps = "infinity" if io_limit == 0 else io_limit

        packages[pkg_name.lower()] = {
            "memory_high": memory_high,
            "memory_max": memory_max,
            "cpu_weight": cpu_weight,
            "tasks_max": tasks_max,
            "io_limit_mbps": io_limit_mbps
        }
    return packages

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
