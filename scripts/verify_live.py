#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Verify live Google Cloud Run service health and traffic distribution.
Records /health payload, revision identity, and traffic split percentages.
Never invents evidence: if gcloud is unauthenticated, marks gcloud_traffic as UNVERIFIED_NO_GCP_AUTH.
"""
import os
import sys
import json
import time
import argparse
import subprocess
import urllib.request
from typing import Dict, Any

def verify_live_service(
    service_url: str = "https://faultforge-checkout-136942862703.us-central1.run.app",
    service_name: str = "faultforge-checkout",
    region: str = "us-central1",
    output_path: str = "reports/live_verification.json"
) -> Dict[str, Any]:
    record: Dict[str, Any] = {
        "timestamp": time.time(),
        "service_name": service_name,
        "region": region,
        "production_url": service_url,
        "health": {
            "status_code": None,
            "body": None,
            "verified": False
        },
        "traffic_split": {
            "verified": False,
            "status": "UNVERIFIED_NO_GCP_AUTH",
            "traffic": [],
            "candidate_percent": None,
            "production_percent": None
        }
    }

    # 1. Probe Live Production Service /health (warmup + retries for container cold start)
    health_url = f"{service_url.rstrip('/')}/health"
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            req = urllib.request.Request(health_url, headers={"User-Agent": f"FaultForge-Verifier/attempt-{attempt}"})
            # Use generous 12.0s timeout to allow Cloud Run cold start instance provisioning
            with urllib.request.urlopen(req, timeout=12.0) as resp:
                record["health"]["status_code"] = resp.status
                body_bytes = resp.read()
                try:
                    record["health"]["body"] = json.loads(body_bytes.decode("utf-8"))
                except Exception:
                    record["health"]["body"] = body_bytes.decode("utf-8")[:500]
                record["health"]["verified"] = (resp.status == 200)
                record["health"].pop("error", None)
                if record["health"]["verified"]:
                    break
        except Exception as exc:
            record["health"]["error"] = str(exc)
            record["health"]["verified"] = False
            if attempt < max_retries:
                time.sleep(2.0 * attempt)

    # 2. Check Cloud Run Traffic Split via gcloud if available
    try:
        cmd = [
            "gcloud", "run", "services", "describe", service_name,
            "--region", region,
            "--format=json"
        ]
        res = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            svc_data = json.loads(res.stdout)
            traffic = svc_data.get("status", {}).get("traffic", [])
            record["traffic_split"]["traffic"] = traffic
            record["traffic_split"]["status"] = "VERIFIED"
            record["traffic_split"]["verified"] = True

            cand_pct = 0
            prod_pct = 0
            cand_url = None
            cand_rev = None
            prod_rev = None
            best_prod_pct = -1
            for t in traffic:
                pct = t.get("percent", 0)
                tag = t.get("tag")
                rev = t.get("revisionName")
                if tag == "candidate":
                    cand_pct += pct
                    cand_url = t.get("url")
                    cand_rev = rev
                else:
                    prod_pct += pct
                    if pct > best_prod_pct:
                        best_prod_pct = pct
                        prod_rev = rev
            record["traffic_split"]["candidate_percent"] = cand_pct
            record["traffic_split"]["production_percent"] = prod_pct
            record["traffic_split"]["candidate_tag"] = "candidate"
            record["traffic_split"]["candidate_url"] = cand_url
            record["traffic_split"]["candidate_revision"] = cand_rev
            record["traffic_split"]["production_revision"] = prod_rev
        else:
            record["traffic_split"]["status"] = "GCLOUD_DESCRIBE_FAILED"
            record["traffic_split"]["error"] = res.stderr.strip()[:300]
    except Exception as exc:
        record["traffic_split"]["status"] = "UNVERIFIED_NO_GCP_AUTH"
        record["traffic_split"]["error"] = f"gcloud invocation failed or uninstalled: {exc}"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(record, f, indent=2)

    print(f"[+] Live verification record written to: {output_path}")
    print(f"    - Production /health: HTTP {record['health']['status_code']} (Verified: {record['health']['verified']})")
    print(f"    - Traffic Status: {record['traffic_split']['status']}")
    return record

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify live Google Cloud Run deployment.")
    parser.add_argument("--url", default="https://faultforge-checkout-136942862703.us-central1.run.app")
    parser.add_argument("--service", default="faultforge-checkout")
    parser.add_argument("--region", default="us-central1")
    parser.add_argument("--output", default="reports/live_verification.json")
    args = parser.parse_args()

    verify_live_service(args.url, args.service, args.region, args.output)
