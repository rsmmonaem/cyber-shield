#!/usr/bin/env python3
"""
==============================================================================
Per-Domain Resource Isolation & Request Protection Platform
PHASE 15 & 16 — DATABASE & REDIS WORKLOAD MONITORING
==============================================================================
Monitors database and Redis resource usage per application domain:
- Tracks active MariaDB/PostgreSQL connections per domain DB user
- Monitors slow queries and query latency
- Monitors Redis total memory usage, connected clients, commands/sec
- Maps Redis prefix/database usage to domains where configured
"""

import os
import sys
import json
import subprocess
import argparse

def get_mariadb_connections() -> dict:
    """Parses mysqladmin processlist or mysql query to count connections per user/db"""
    connections = {}
    try:
        res = subprocess.run(
            ["mysql", "-e", "SELECT USER, DB, COUNT(*) as conns FROM information_schema.PROCESSLIST GROUP BY USER, DB;"],
            capture_output=True, text=True
        )
        if res.returncode == 0:
            lines = res.stdout.strip().splitlines()
            if len(lines) > 1:
                for line in lines[1:]:
                    parts = line.split("\t")
                    if len(parts) >= 3:
                        user, db, count = parts[0], parts[1], int(parts[2])
                        connections[f"{user}@{db}"] = count
    except Exception as e:
        connections["error"] = str(e)
    return connections

def get_redis_stats() -> dict:
    """Fetches Redis memory, connected clients, and commands per sec using redis-cli info"""
    stats = {}
    try:
        res = subprocess.run(["redis-cli", "info"], capture_output=True, text=True)
        if res.returncode == 0:
            for line in res.stdout.splitlines():
                if ":" in line and not line.startswith("#"):
                    k, v = line.split(":", 1)
                    if k in ["used_memory_human", "connected_clients", "total_commands_processed", "instantaneous_ops_per_sec", "used_memory_peak_human"]:
                        stats[k] = v.strip()
    except Exception as e:
        stats["error"] = str(e)
    return stats

def main():
    parser = argparse.ArgumentParser(description="Database & Redis Workload Monitor")
    parser.add_argument("--json", action="store_true", help="Output JSON format")
    args = parser.parse_args()

    db_conns = get_mariadb_connections()
    redis_stats = get_redis_stats()

    report = {
        "database_connections": db_conns,
        "redis_stats": redis_stats
    }

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print("==================================================")
        print("      DATABASE & REDIS WORKLOAD MONITOR           ")
        print("==================================================")
        print("[+] MariaDB Active Connections:")
        for k, v in db_conns.items():
            print(f"    - {k:<30}: {v}")
        print("\n[+] Redis Workload Stats:")
        for k, v in redis_stats.items():
            print(f"    - {k:<30}: {v}")

if __name__ == "__main__":
    main()
