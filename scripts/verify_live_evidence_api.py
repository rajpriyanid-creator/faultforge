#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge Live API Evidence Verification Gate
Fetches the immutable sealed evidence receipt served by /api/v1/evidence from the live candidate
service and verifies that its receipt_id, tamper-evident seal, and fields match the receipt baked into
the image for the commit that built the container.
Zero write paths. Any discrepancy or unreachability fails the gate.
"""
import os
import sys
import json
import argparse
import urllib.request
import urllib.error
from typing import Dict, Any

def fetch_api_evidence(base_url: str, timeout: float = 15.0) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}/api/v1/evidence"
    print(f"[*] Querying live candidate evidence API: {url}")
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

    # 1. Essential cryptographic identities
    api_rcpt_id = api_data.get("receipt_id")
    exp_rcpt_id = sealed_receipt.get("receipt_id")
    if api_rcpt_id != exp_rcpt_id:
        discrepancies.append(f"receipt_id mismatch: live API has '{api_rcpt_id}', expected '{exp_rcpt_id}'")

    api_seal = api_data.get("tamper_evident_seal_sha256")
    exp_seal = sealed_receipt.get("tamper_evident_seal_sha256")
    if api_seal != exp_seal:
        discrepancies.append(f"tamper_evident_seal_sha256 mismatch: live API has '{api_seal}', expected '{exp_seal}'")

    api_commit = api_data.get("candidate_built_from_commit")
    exp_commit = sealed_receipt.get("candidate_built_from_commit")
    if api_commit != exp_commit:
        discrepancies.append(f"candidate_built_from_commit mismatch: live API has '{api_commit}', expected '{exp_commit}'")

    # 2. Structural key parity
    api_keys = set(api_data.keys())
    sealed_keys = set(sealed_receipt.keys())

    extra_in_api = api_keys - sealed_keys
    if extra_in_api:
        discrepancies.append(f"Extra keys in API response absent from sealed receipt: {sorted(extra_in_api)}")

    missing_in_api = sealed_keys - api_keys
    if missing_in_api:
        discrepancies.append(f"Keys missing from API response present in sealed receipt: {sorted(missing_in_api)}")

    # 3. Value parity for shared keys
    for k in api_keys.intersection(sealed_keys):
        if api_data[k] != sealed_receipt[k]:
            discrepancies.append(f"Mismatch for key '{k}': API={api_data[k]!r} vs SEALED={sealed_receipt[k]!r}")

    if discrepancies:
        print(f"\n[-] FAILED: Found {len(discrepancies)} discrepancy/discrepancies between live API and sealed receipt:")
        for d in discrepancies:
            print(f"    - {d}")
        return False

    print(f"[+] PASSED: Live API /api/v1/evidence matches baked receipt verbatim.")
    print(f"    - receipt_id: {exp_rcpt_id}")
    print(f"    - commit: {exp_commit}")
    print(f"    - tamper_evident_seal: {exp_seal[:16]}...")
    return True

def main():
    parser = argparse.ArgumentParser(description="Verify live /api/v1/evidence matches baked image receipt")
    parser.add_argument("--url", default=os.getenv("CANDIDATE_URL", "http://127.0.0.1:8090"), help="Base URL of candidate service")
    parser.add_argument("--receipt", default="docs/sample_reports/evidence_receipt.json", help="Path to baked image receipt")
    args = parser.parse_args()

    receipt_path = args.receipt
    if not os.path.exists(receipt_path):
        if os.path.exists("reports/evidence_receipt.json"):
            receipt_path = "reports/evidence_receipt.json"
        else:
            print(f"[-] Error: receipt not found at {receipt_path}", file=sys.stderr)
            sys.exit(1)

    with open(receipt_path, "r", encoding="utf-8") as f:
        sealed_receipt = json.load(f)

    try:
        api_data = fetch_api_evidence(args.url)
    except Exception as exc:
        print(f"[-] Error fetching live evidence from {args.url}: {exc}", file=sys.stderr)
        sys.exit(1)

    if not compare_receipts(api_data, sealed_receipt):
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
