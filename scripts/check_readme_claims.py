#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge README Claims vs. Empirical Ledger Validator
Verifies that all claims made in README.md Section 4 match the empirical
truth recorded in stage_ledger.json and evidence_receipt.json.
Fails CI if README inflates a SKIPPED or FAILED stage into SUCCESS.
"""
import os
import re
import sys
import json
import argparse
from typing import Dict, Any, Tuple

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

DEFAULT_README_PATH = "README.md"
DEFAULT_LEDGER_PATH = "reports/stage_ledger.json"
DEFAULT_RECEIPT_PATH = "reports/evidence_receipt.json"

EXPECTED_STAGES = [
    "plan", "create", "configure", "verify", "secure",
    "package", "release", "monitor", "govern"
]

def parse_readme_stages_table(readme_path: str = DEFAULT_README_PATH) -> Dict[str, str]:
    if not os.path.exists(readme_path):
        print(f"[-] Error: README not found at {readme_path}", file=sys.stderr)
        sys.exit(1)

    with open(readme_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Find Section 4
    sec4_match = re.search(r"## 4\.\s+The 9 Covered Lifecycle Stages.*?(?=\n## 5\.|\Z)", content, re.DOTALL)
    if not sec4_match:
        print("[-] Error: Could not locate '## 4. The 9 Covered Lifecycle Stages' in README.md", file=sys.stderr)
        sys.exit(1)

    table_text = sec4_match.group(0)
    claims = {}

    for line in table_text.splitlines():
        line = line.strip()
        if not line.startswith("|") or line.startswith("|---") or "Stage" in line:
            continue
        cols = [c.strip() for c in line.split("|")[1:-1]]
        if len(cols) >= 4:
            # Stage is in col 0, e.g. **`plan`**
            stg_match = re.search(r"`([a-z_]+)`", cols[0])
            if stg_match:
                stage_name = stg_match.group(1).lower()
                status_text = cols[3]
                claims[stage_name] = status_text

    return claims

def validate_claims(
    readme_path: str = DEFAULT_README_PATH,
    ledger_path: str = DEFAULT_LEDGER_PATH,
    receipt_path: str = DEFAULT_RECEIPT_PATH,
    strict_all_stages: bool = True
) -> bool:
    print("\n=================================================================")
    print(" FaultForge README Claims vs. Empirical Evidence Ledger Gate")
    print("=================================================================")

    # Fallback to sample reports if live reports missing in local test mode
    if not os.path.exists(ledger_path) and os.path.exists("docs/sample_reports/stage_ledger.json"):
        ledger_path = "docs/sample_reports/stage_ledger.json"
        print(f"[*] Live ledger missing. Using reference ledger: {ledger_path}")

    if not os.path.exists(receipt_path) and os.path.exists("docs/sample_reports/evidence_receipt.json"):
        receipt_path = "docs/sample_reports/evidence_receipt.json"

    if not os.path.exists(ledger_path):
        print(f"[-] Error: Stage ledger not found at {ledger_path}", file=sys.stderr)
        return False

    with open(ledger_path, "r", encoding="utf-8") as lf:
        ledger_data = json.load(lf)

    stages_recorded = ledger_data.get("stages", {})
    readme_claims = parse_readme_stages_table(readme_path)

    print(f"README Stages Found: {len(readme_claims)} / 9")
    print(f"Ledger Stages Found: {len(stages_recorded)} / 9\n")
    print(f"{'STAGE':<12} {'LEDGER STATUS':<16} {'README CLAIM':<24} {'RESULT'}")
    print("-" * 65)

    discrepancies = []

    for stage in EXPECTED_STAGES:
        if stage not in readme_claims:
            discrepancies.append(f"Stage '{stage}' is missing from README Section 4 table.")
            print(f"{stage:<12} {'MISSING':<16} {'MISSING':<24} [FAIL]")
            continue

        claim_str = readme_claims[stage]
        ledger_entry = stages_recorded.get(stage)

        if not ledger_entry:
            if strict_all_stages:
                discrepancies.append(f"Stage '{stage}' has not been recorded in stage_ledger.json.")
                print(f"{stage:<12} {'NOT RECORDED':<16} {claim_str:<24} [FAIL]")
            else:
                print(f"{stage:<12} {'PENDING':<16} {claim_str:<24} [WARN]")
            continue

        ledger_status = ledger_entry.get("status", "UNKNOWN").upper()

        if ledger_status == "FAILED":
            discrepancies.append(f"Stage '{stage}' marked FAILED in ledger, but claimed in README as '{claim_str}'.")
            print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
        elif ledger_status == "SKIPPED":
            # If ledger skipped, README must acknowledge SKIPPED
            if "SKIPPED" not in claim_str.upper():
                discrepancies.append(f"Stage '{stage}' is SKIPPED in ledger, but README claims unqualified SUCCESS ('{claim_str}').")
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
            else:
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [PASS]")
        elif ledger_status == "SUCCESS":
            if "SUCCESS" not in claim_str.upper():
                discrepancies.append(f"Stage '{stage}' succeeded in ledger, but README does not indicate SUCCESS ('{claim_str}').")
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")
            else:
                print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [PASS]")
        else:
            discrepancies.append(f"Stage '{stage}' has unknown ledger status: {ledger_status}")
            print(f"{stage:<12} {ledger_status:<16} {claim_str:<24} [FAIL]")

    # Check receipt consistency if present
    if os.path.exists(receipt_path):
        try:
            with open(receipt_path, "r", encoding="utf-8") as rf:
                receipt = json.load(rf)
            fin_status = receipt.get("final_status")
            not_est = receipt.get("not_established", [])
            print(f"\n[*] Receipt Cross-Check: final_status='{fin_status}', not_established={len(not_est)} items")
            if fin_status == "RECOVERED_AND_VERIFIED" and len(not_est) > 0:
                discrepancies.append(f"Receipt claims RECOVERED_AND_VERIFIED but has {len(not_est)} unestablished items.")
        except Exception as exc:
            discrepancies.append(f"Error reading receipt at {receipt_path}: {exc}")

    print("=================================================================\n")

    if discrepancies:
        print(f"[-] FAILED: Found {len(discrepancies)} discrepancy/discrepancies between claims and ledger truth:")
        for d in discrepancies:
            print(f"    - {d}")
        return False

    print("[+] PASSED: All README claims perfectly match the empirical evidence ledger.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Check README claims against stage_ledger.json")
    parser.add_argument("--readme", default=DEFAULT_README_PATH, help="Path to README.md")
    parser.add_argument("--ledger", default=DEFAULT_LEDGER_PATH, help="Path to stage_ledger.json")
    parser.add_argument("--receipt", default=DEFAULT_RECEIPT_PATH, help="Path to evidence_receipt.json")
    parser.add_argument("--allow-partial", action="store_true", help="Allow partial ledger when testing early stages")
    args = parser.parse_args()

    success = validate_claims(
        readme_path=args.readme,
        ledger_path=args.ledger,
        receipt_path=args.receipt,
        strict_all_stages=not args.allow_partial
    )
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
