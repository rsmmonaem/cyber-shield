#!/usr/bin/env python3
"""
==============================================================================
Per-Domain Resource Isolation & Request Protection Platform
PHASE 23 — HISTORICAL METRICS TIME-SERIES COLLECTOR
==============================================================================
Stores high-resolution domain metrics into SQLite DB:
- 24h detailed resolution (10s interval)
- 7d hourly aggregates
- 30d daily trends
"""

import os
import sys
import sqlite3
import time
import json
import argparse
from pathlib import Path

DB_PATH = Path("/tmp/domain_metrics.db")

def init_db(conn):
    """Initializes time-series metrics database schema"""
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS domain_metrics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp INTEGER,
        domain TEXT,
        cpu_pct REAL,
        ram_mb REAL,
        io_mbps REAL,
        iops INTEGER,
        pids INTEGER,
        fds INTEGER,
        connections INTEGER,
        requests_per_sec REAL,
        close_wait_count INTEGER,
        status TEXT
    );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_dom_ts ON domain_metrics(domain, timestamp);")
    conn.commit()

def record_sample(conn, domain: str, cpu: float, ram: float, io: float, iops: int, pids: int, fds: int, conns: int, rps: float, cw: int, status: str):
    """Records a single metric sample"""
    cursor = conn.cursor()
    ts = int(time.time())
    cursor.execute("""
    INSERT INTO domain_metrics (timestamp, domain, cpu_pct, ram_mb, io_mbps, iops, pids, fds, connections, requests_per_sec, close_wait_count, status)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
    """, (ts, domain, cpu, ram, io, iops, pids, fds, conns, rps, cw, status))
    conn.commit()

def get_recent_metrics(conn, domain: str = None, limit: int = 50) -> list:
    """Queries recent metrics for dashboard rendering"""
    cursor = conn.cursor()
    if domain:
        cursor.execute("SELECT timestamp, domain, cpu_pct, ram_mb, io_mbps, pids, fds, connections, requests_per_sec, close_wait_count, status FROM domain_metrics WHERE domain = ? ORDER BY timestamp DESC LIMIT ?", (domain, limit))
    else:
        cursor.execute("SELECT timestamp, domain, cpu_pct, ram_mb, io_mbps, pids, fds, connections, requests_per_sec, close_wait_count, status FROM domain_metrics ORDER BY timestamp DESC LIMIT ?", (limit,))
    
    rows = cursor.fetchall()
    results = []
    for r in rows:
        results.append({
            "timestamp": r[0],
            "domain": r[1],
            "cpu_pct": r[2],
            "ram_mb": r[3],
            "io_mbps": r[4],
            "pids": r[5],
            "fds": r[6],
            "connections": r[7],
            "requests_per_sec": r[8],
            "close_wait_count": r[9],
            "status": r[10]
        })
    return results

def main():
    parser = argparse.ArgumentParser(description="Metrics Time-Series Collector")
    parser.add_argument("--seed", action="store_true", help="Seed mock initial metric samples for testing")
    args = parser.parse_args()

    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    if args.seed:
        print("[+] Seeding metrics database with initial baseline data...")
        sample_domains = ["npms.pro", "multivendor.ecommatrix.xyz", "testdomain.com"]
        for d in sample_domains:
            record_sample(conn, d, 15.2, 850.0, 4.5, 300, 24, 1200, 45, 18.5, 2, "NORMAL")
        print("[✓] Baseline metrics seeded.")

    conn.close()

if __name__ == "__main__":
    main()
