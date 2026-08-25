#!/usr/bin/env python3
"""
==============================================================================
Per-Domain Resource Isolation & Request Protection Platform
PHASES 5-9 — DOMAIN CGROUP V2 RUNTIME MANAGER & MONITOR
==============================================================================
Provides dynamic update and inspection of domain cgroup limits:
- CPU quota & weight
- RAM memory.low, memory.high, memory.max
- Disk I/O Bps & IOPS
- TasksMax (PIDs)
- File descriptor ulimits
"""

import os
import sys
import subprocess
import json
import argparse
from pathlib import Path

CGROUP_ROOT = Path("/sys/fs/cgroup")

class DomainCgroupManager:
    def __init__(self, domain: str, package: str = "business"):
        self.domain = domain
        self.sanitized_domain = domain.replace(".", "-").replace("_", "-")
        self.slice_name = f"domain-{self.sanitized_domain}.slice"
        self.package_slice = f"package-{package}.slice"
        self.slice_path = CGROUP_ROOT / "hosting.slice" / self.package_slice / self.slice_name

    def apply_limits(self, cpu_quota: str, cpu_weight: int, memory_low: str, memory_high: str, memory_max: str, tasks_max: int, io_read_bps: str = None, io_write_bps: str = None, dry_run: bool = False):
        """Applies dynamic systemd properties to the domain slice using systemctl set-property"""
        cmd = [
            "systemctl", "set-property", self.slice_name,
            f"CPUQuota={cpu_quota}",
            f"CPUWeight={cpu_weight}",
            f"MemoryLow={memory_low}",
            f"MemoryHigh={memory_high}",
            f"MemoryMax={memory_max}",
            f"TasksMax={tasks_max}"
        ]
        
        if io_read_bps:
            cmd.append(f"IOReadBandwidthMax={io_read_bps}")
        if io_write_bps:
            cmd.append(f"IOWriteBandwidthMax={io_write_bps}")

        print(f"[+] Executing limit update command for {self.domain}:")
        print("    " + " ".join(cmd))

        if not dry_run:
            res = subprocess.run(cmd, capture_output=True, text=True)
            if res.returncode == 0:
                print(f"[✓] Successfully applied limits to {self.slice_name}")
            else:
                print(f"[!] Error setting properties: {res.stderr}")

    def read_stats(self) -> dict:
        """Reads live cgroup v2 stats from /sys/fs/cgroup/..."""
        stats = {
            "domain": self.domain,
            "slice": self.slice_name,
            "cgroup_path": str(self.slice_path),
            "cpu": {},
            "memory": {},
            "pids": {},
            "io": {}
        }

        if not self.slice_path.exists():
            stats["status"] = "NOT_FOUND"
            return stats

        stats["status"] = "ACTIVE"

        # Memory stats
        mem_curr = self.slice_path / "memory.current"
        mem_high = self.slice_path / "memory.high"
        mem_max = self.slice_path / "memory.max"
        mem_events = self.slice_path / "memory.events"

        if mem_curr.exists():
            stats["memory"]["current_bytes"] = int(mem_curr.read_text().strip() or 0)
        if mem_high.exists():
            stats["memory"]["high"] = mem_high.read_text().strip()
        if mem_max.exists():
            stats["memory"]["max"] = mem_max.read_text().strip()
        if mem_events.exists():
            stats["memory"]["events"] = mem_events.read_text().strip().replace("\n", ", ")

        # CPU stats
        cpu_stat = self.slice_path / "cpu.stat"
        if cpu_stat.exists():
            cpu_data = {}
            for line in cpu_stat.read_text().splitlines():
                parts = line.split()
                if len(parts) == 2:
                    cpu_data[parts[0]] = int(parts[1])
            stats["cpu"] = cpu_data

        # PIDs stats
        pids_curr = self.slice_path / "pids.current"
        pids_max = self.slice_path / "pids.max"
        if pids_curr.exists():
            stats["pids"]["current"] = int(pids_curr.read_text().strip() or 0)
        if pids_max.exists():
            stats["pids"]["max"] = pids_max.read_text().strip()

        return stats

def main():
    parser = argparse.ArgumentParser(description="Domain cgroup v2 Manager")
    parser.add_argument("--domain", required=True, help="Domain name (e.g. npms.pro)")
    parser.add_argument("--package", default="business", help="Package name (basic, business, enterprise)")
    parser.add_argument("--action", choices=["apply", "stats"], default="stats", help="Action to perform")
    parser.add_argument("--cpu-quota", default="200%", help="CPU Quota percentage")
    parser.add_argument("--cpu-weight", type=int, default=200, help="CPU Weight")
    parser.add_argument("--memory-high", default="1.8G", help="Memory high threshold")
    parser.add_argument("--memory-max", default="2G", help="Memory max threshold")
    parser.add_argument("--tasks-max", type=int, default=50, help="Max PIDs")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")

    args = parser.parse_args()

    mgr = DomainCgroupManager(args.domain, args.package)

    if args.action == "apply":
        mgr.apply_limits(
            cpu_quota=args.cpu_quota,
            cpu_weight=args.cpu_weight,
            memory_low="256M",
            memory_high=args.memory_high,
            memory_max=args.memory_max,
            tasks_max=args.tasks_max,
            dry_run=args.dry_run
        )
    elif args.action == "stats":
        stats = mgr.read_stats()
        print(json.dumps(stats, indent=2))

if __name__ == "__main__":
    main()
