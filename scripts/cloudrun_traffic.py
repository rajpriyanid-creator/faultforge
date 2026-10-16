#!/usr/bin/env python3
import os
import sys
import time
import argparse
import subprocess
import requests
from typing import Dict, Any

def run_cmd(cmd: list) -> str:
    print(f"[*] Running: {' '.join(cmd)}")
    try:
        res = subprocess.check_output(cmd, stderr=subprocess.STDOUT, text=True)
        return res.strip()
    except subprocess.CalledProcessError as e:
        print(f"[-] Command failed ({e.returncode}): {e.output}")
        sys.exit(e.returncode if e.returncode != 0 else 1)

def verify_live_health(service_url: str, max_retries: int = 5) -> bool:
    print(f"[*] Verifying health at {service_url}/health ...")
    for i in range(max_retries):
        try:
            r = requests.get(f"{service_url.rstrip('/')}/health", timeout=3.0)
            if r.status_code == 200:
                print(f"[+] Health probe passed (HTTP 200)")
                return True
        except Exception as exc:
            print(f"[-] Attempt {i+1}/{max_retries} failed: {exc}")
        time.sleep(2)
    return False

def route_traffic(service: str, region: str, revisions_and_percents: str):
    """
    Updates Cloud Run traffic split.
    Example: --to-revisions=v1=90,v2=10
    """
    cmd = [
        "gcloud", "run", "services", "update-traffic", service,
        "--region", region,
        f"--to-revisions={revisions_and_percents}"
    ]
    return run_cmd(cmd)

def rollback_to_stable(service: str, region: str, stable_revision: str, verify_url: Optional[str] = None) -> Dict[str, Any]:
    print(f"\n[!] ALERT: Initiating immediate traffic rollback to known-good revision: {stable_revision}")
    cmd = [
        "gcloud", "run", "services", "update-traffic", service,
        "--region", region,
        f"--to-revisions={stable_revision}=100"
    ]
    out = run_cmd(cmd)

    healthy = True
    if verify_url:
        print(f"[*] Re-verifying health after rollback at {verify_url}...")
        healthy = verify_live_health(verify_url)

    rollback_record = {
        "rollback_executed": True,
        "target_service": service,
        "region": region,
        "restored_revision": stable_revision,
        "traffic_allocation": {stable_revision: 100},
        "health_reverified": healthy,
        "timestamp": time.time(),
        "command_output": out
    }

    os.makedirs("reports", exist_ok=True)
    with open("reports/rollback.json", "w", encoding="utf-8") as f:
        json.dump(rollback_record, f, indent=2)

    print(f"[+] Rollback executed successfully. Saved to reports/rollback.json\n")
    if not healthy:
        sys.exit(1)
    return rollback_record

def main():
    parser = argparse.ArgumentParser(description="FaultForge Cloud Run Traffic & Rollback Manager")
    parser.add_argument("--action", choices=["route", "rollback", "verify"], required=True)
    parser.add_argument("--service", default=os.getenv("K_SERVICE", "faultforge-checkout"))
    parser.add_argument("--region", default=os.getenv("GCP_REGION", "us-central1"))
    parser.add_argument("--revisions", help="e.g. rev-stable=90,rev-candidate=10")
    parser.add_argument("--stable-revision", default=os.getenv("KNOWN_GOOD_REVISION", "faultforge-checkout-00001"))
    parser.add_argument("--url", default=os.getenv("DEPLOYED_URL", "http://127.0.0.1:8080"))
    args = parser.parse_args()

    if args.action == "verify":
        success = verify_live_health(args.url)
        sys.exit(0 if success else 1)
    elif args.action == "route":
        if not args.revisions:
            print("[-] --revisions required for action 'route'")
            sys.exit(1)
        route_traffic(args.service, args.region, args.revisions)
    elif args.action == "rollback":
        rollback_to_stable(args.service, args.region, args.stable_revision, verify_url=args.url)

if __name__ == "__main__":
    main()
