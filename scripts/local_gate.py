#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge Local Supervised Gate Controller
Cross-platform simulation of human sign-off and rollback without GCP.
"""
import os
import sys
import argparse
import subprocess
from pathlib import Path

GATE_DIR = Path("gate_data")
APPROVE_FILE = GATE_DIR / "APPROVE"
ROLLBACK_FILE = GATE_DIR / "ROLLBACK"

def cmd_start():
    GATE_DIR.mkdir(exist_ok=True)
    if APPROVE_FILE.exists():
        APPROVE_FILE.unlink()
    if ROLLBACK_FILE.exists():
        ROLLBACK_FILE.unlink()
    print("[+] Starting Local Supervised Staging Stack...")
    try:
        subprocess.run(["docker", "compose", "-f", "docker-compose.supervised.yml", "up", "-d"], check=True)
        print("[+] Staging candidate active at http://localhost:8080")
        print("[+] Supervised gate waiting for human approval. Run: python scripts/local_gate.py --action approve")
    except Exception as e:
        print(f"[*] Docker compose command execution note: {e}")
        print("[+] Local Supervised Gate environment ready. Awaiting human approval.")

def cmd_approve():
    GATE_DIR.mkdir(exist_ok=True)
    APPROVE_FILE.touch()
    if ROLLBACK_FILE.exists():
        ROLLBACK_FILE.unlink()
    print("[✓] Human approval detected! Candidate promoted to production (100% traffic).")

def cmd_rollback():
    GATE_DIR.mkdir(exist_ok=True)
    ROLLBACK_FILE.touch()
    if APPROVE_FILE.exists():
        APPROVE_FILE.unlink()
    print("[!] Rollback triggered! Reverting candidate container to last-known-good stable...")
    try:
        subprocess.run(["docker", "compose", "-f", "docker-compose.supervised.yml", "down"], check=False)
    except Exception:
        pass
    print("[✓] Rollback complete. Stable revision restored.")

def cmd_status():
    if APPROVE_FILE.exists():
        print("Status: PROMOTED (Human approved for 100% production traffic)")
    elif ROLLBACK_FILE.exists():
        print("Status: ROLLED_BACK (Reverted to stable)")
    else:
        print("Status: BLOCKED_PENDING_APPROVAL (Staging active, awaiting human review)")

def cmd_stop():
    GATE_DIR.mkdir(exist_ok=True)
    try:
        subprocess.run(["docker", "compose", "-f", "docker-compose.supervised.yml", "down"], check=False)
    except Exception:
        pass
    if APPROVE_FILE.exists():
        APPROVE_FILE.unlink()
    if ROLLBACK_FILE.exists():
        ROLLBACK_FILE.unlink()
    print("[+] Stopped local supervised gate.")

def main():
    parser = argparse.ArgumentParser(description="FaultForge Local Supervised Gate Controller")
    parser.add_argument("--action", choices=["start", "approve", "rollback", "status", "stop"], default="status")
    args = parser.parse_args()

    if args.action == "start":
        cmd_start()
    elif args.action == "approve":
        cmd_approve()
    elif args.action == "rollback":
        cmd_rollback()
    elif args.action == "status":
        cmd_status()
    elif args.action == "stop":
        cmd_stop()

if __name__ == "__main__":
    main()
