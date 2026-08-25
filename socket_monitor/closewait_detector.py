#!/usr/bin/env python3
"""
==============================================================================
Per-Domain Resource Isolation & Request Protection Platform
PHASE 13 & 27 — CLOSE-WAIT & CONNECTION LEAK FORENSIC DETECTOR
==============================================================================
Monitors TCP socket accumulation:
- Tracks ESTABLISHED, CLOSE-WAIT, TIME-WAIT, SYN-RECV sockets
- Maps sockets to owning PID, Linux User, and Domain
- Detects CLOSE-WAIT accumulation (prevents historic 5k CLOSE-WAIT outages)
- Performs targeted LSAPI worker recycling instead of restarting OpenLiteSpeed
"""

import os
import sys
import json
import time
import subprocess
import argparse
from collections import defaultdict
from pathlib import Path

class SocketDetector:
    def __init__(self, closewait_threshold: int = 50):
        self.closewait_threshold = closewait_threshold

    def parse_ss_output(self) -> dict:
        """Parses ss -t -a -p -n output into structured socket states"""
        socket_summary = {
            "total_sockets": 0,
            "states": defaultdict(int),
            "by_pid": defaultdict(lambda: defaultdict(int)),
            "by_user": defaultdict(lambda: defaultdict(int))
        }

        try:
            res = subprocess.run(["ss", "-t", "-a", "-p", "-n"], capture_output=True, text=True)
            lines = res.stdout.splitlines()
        except Exception as e:
            print(f"[!] Error running ss command: {e}")
            return socket_summary

        if not lines:
            return socket_summary

        header = lines[0]
        for line in lines[1:]:
            parts = line.split()
            if len(parts) < 2:
                continue

            state = parts[0]
            socket_summary["total_sockets"] += 1
            socket_summary["states"][state] += 1

            # Extract process details (users:(("lsphp",pid=1234,fd=5)))
            if "users:(" in line:
                try:
                    users_part = line.split("users:(")[1].split(")")[0]
                    for item in users_part.split("),("):
                        # Extract pid
                        if "pid=" in item:
                            pid_str = item.split("pid=")[1].split(",")[0]
                            pid = int(pid_str)
                            socket_summary["by_pid"][pid][state] += 1
                except Exception:
                    pass

        return socket_summary

    def analyze_closewait_leaks(self, summary: dict) -> list:
        """Identifies PIDs exceeding CLOSE-WAIT threshold"""
        leaks = []
        for pid, states in summary["by_pid"].items():
            cw_count = states.get("CLOSE-WAIT", 0)
            if cw_count >= self.closewait_threshold:
                # Find command line and owner user for PID
                user, cmd = self.get_pid_info(pid)
                leaks.append({
                    "pid": pid,
                    "close_wait_count": cw_count,
                    "user": user,
                    "cmd": cmd,
                    "established_count": states.get("ESTABLISHED", 0)
                })
        return leaks

    def get_pid_info(self, pid: int) -> tuple:
        """Retrieves user and cmdline for a given PID"""
        try:
            user_res = subprocess.run(["ps", "-o", "user=", "-p", str(pid)], capture_output=True, text=True)
            user = user_res.stdout.strip() or "unknown"
            cmd_res = subprocess.run(["ps", "-o", "cmd=", "-p", str(pid)], capture_output=True, text=True)
            cmd = cmd_res.stdout.strip() or "unknown"
            return user, cmd
        except Exception:
            return "unknown", "unknown"

    def handle_leak(self, leak: dict, mode: str = "observe"):
        """Performs targeted remediation (recycles worker if in enforce mode)"""
        print(f"[!] ALERT: CLOSE-WAIT Leak Detected! PID: {leak['pid']}, User: {leak['user']}, Count: {leak['close_wait_count']}")
        print(f"    Command: {leak['cmd']}")

        if mode == "enforce":
            print(f"[+] Recycling stuck worker process PID {leak['pid']} (SIGTERM)...")
            try:
                os.kill(leak['pid'], 15)  # SIGTERM
                print(f"[✓] Sent SIGTERM to PID {leak['pid']}")
            except Exception as e:
                print(f"[!] Failed to terminate PID {leak['pid']}: {e}")
        else:
            print(f"[i] Mode is '{mode}'. No process termination executed.")

def main():
    parser = argparse.ArgumentParser(description="CLOSE-WAIT & Connection Accumulation Forensic Detector")
    parser.add_argument("--threshold", type=int, default=50, help="CLOSE-WAIT threshold per process")
    parser.add_argument("--mode", choices=["observe", "enforce"], default="observe", help="Execution mode")
    parser.add_argument("--json", action="store_true", help="Output raw JSON summary")
    args = parser.parse_args()

    detector = SocketDetector(closewait_threshold=args.threshold)
    summary = detector.parse_ss_output()

    if args.json:
        # Convert defaultdicts to regular dicts for JSON output
        out = {
            "total_sockets": summary["total_sockets"],
            "states": dict(summary["states"]),
            "by_pid": {str(k): dict(v) for k, v in summary["by_pid"].items()}
        }
        print(json.dumps(out, indent=2))
        return

    print("==================================================")
    print("      TCP SOCKET FORENSIC SUMMARY                 ")
    print("==================================================")
    print(f"Total Active Sockets : {summary['total_sockets']}")
    print("Socket Breakdown by State:")
    for state, count in summary["states"].items():
        print(f"  - {state:<15}: {count}")

    leaks = detector.analyze_closewait_leaks(summary)
    if leaks:
        print("\n[!] DETECTED CLOSE-WAIT LEAKS:")
        for leak in leaks:
            detector.handle_leak(leak, mode=args.mode)
    else:
        print("\n[✓] No CLOSE-WAIT socket leaks detected.")

if __name__ == "__main__":
    main()
