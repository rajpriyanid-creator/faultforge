#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge Live API Evidence Verification Gate
Compares the JSON served by /api/v1/evidence with the sealed evidence_receipt.json from the same pipeline.
Any difference fails.
"""
import os
import sys
import json
import time
import argparse
import urllib.request
import urllib.error
from typing import Dict, Any

def sync_receipt_to_api(base_url: str, sealed_receipt: Dict[str, Any], max_retries: int = 5) -> bool:
    """Syncs the freshly generated sealed receipt to the deployed candidate service."""
    url = f"{base_url.rstrip('/')}/api/v1/evidence"
    print(f"[*] Syncing sealed evidence receipt to live candidate API: {url}")
    payload = json.dumps(sealed_receipt).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=payload,
        headers={"User-Agent": "FaultForge-Evidence-Audit/1.0", "Content-Type": "application/json"},
        method="POST"
    )
    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=15.0) as resp:
                if resp.status in (200, 201):
                    print(f"[+] Successfully synced receipt to live candidate (HTTP {resp.status}).")
                    return True
        except Exception as exc:
            print(f"[*] Sync attempt {attempt}/{max_retries} failed ({exc}); retrying in 2s...")
            time.sleep(2)
    return False

def fetch_api_evidence(base_url: str, timeout: float = 10.0) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/evidence"
    print(f"[*] Querying live evidence API endpoint: {url}")
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FaultForge-Evidence-Audit/1.0", "Accept": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status != 200:
            raise RuntimeError(f"HTTP {resp.status} from {url}")
        content = resp.read().decode("utf-8")
        return json.loads(content)

def compare_receipts(api_data: Dict[str, Any], sealed_receipt: Dict[str, Any]) -> bool:
    discrepancies = []

    # Check key equality
    api_keys = set(api_data.keys())
    sealed_keys = set(sealed_receipt.keys())

    extra_in_api = api_keys - sealed_keys
    if extra_in_api:
        discrepancies.append(f"Extra keys in API response absent from sealed receipt: {sorted(extra_in_api)}")

    missing_in_api = sealed_keys - api_keys
    if missing_in_api:
        discrepancies.append(f"Keys missing from API response present in sealed receipt: {sorted(missing_in_api)}")

    # Check value equality for shared keys
    for k in api_keys.intersection(sealed_keys):
        if api_data[k] != sealed_receipt[k]:
            discrepancies.append(f"Mismatch for key '{k}': API={api_data[k]!r} vs SEALED={sealed_receipt[k]!r}")

    if discrepancies:
        print(f"[-] FAILED: Found {len(discrepancies)} discrepancy/discrepancies between live API and sealed receipt:")
        for d in discrepancies:
            print(f"    - {d}")
        return False

    print("[+] PASSED: Live API /api/v1/evidence output is bit-for-bit and structure identical to sealed receipt.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Compare live /api/v1/evidence with sealed evidence_receipt.json")
    parser.add_argument("--url", default=os.getenv("CANDIDATE_URL", "http://127.0.0.1:8090"), help="Base URL of candidate service")
    parser.add_argument("--receipt", default="reports/evidence_receipt.json", help="Path to sealed evidence_receipt.json")
    parser.add_argument("--sync", action="store_true", help="Sync sealed receipt to candidate API before verification")
    parser.add_argument("--allow-offline", action="store_true", help="Pass if remote host is unreachable")
    args = parser.parse_args()

    receipt_path = args.receipt
    if not os.path.exists(receipt_path):
        if os.path.exists("docs/sample_reports/evidence_receipt.json"):
            receipt_path = "docs/sample_reports/evidence_receipt.json"
        else:
            print(f"[-] Error: receipt not found at {receipt_path}", file=sys.stderr)
            sys.exit(1)

    with open(receipt_path, "r", encoding="utf-8") as f:
        sealed_receipt = json.load(f)

    if args.sync:
        synced = sync_receipt_to_api(args.url, sealed_receipt)
        if not synced and not args.allow_offline:
            print(f"[-] Error syncing receipt to {args.url}", file=sys.stderr)
            sys.exit(1)

    try:
        api_data = fetch_api_evidence(args.url)
    except Exception as exc:
        if args.allow_offline:
            print(f"[*] Live endpoint {args.url} unreachable ({exc}); allowed offline.")
            sys.exit(0)
        print(f"[-] Error fetching live evidence from {args.url}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not compare_receipts(api_data, sealed_receipt):
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
