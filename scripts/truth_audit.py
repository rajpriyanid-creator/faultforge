#!/usr/bin/env python3
import os
import re
import sys
import json
import subprocess
from typing import List, Tuple

def audit_forbidden_patterns() -> List[str]:
    violations = []
    forbidden_tokens = [
        (r"\|\|\s*true", "Masked failure (|| true)"),
        (r"\|\|\s*echo", "Masked failure (|| echo)"),
        (r"default-hash", "Hardcoded placeholder hash (default-hash)")
    ]

    target_files = [".gitlab-ci.yml"]
    for root, _, files in os.walk("scripts"):
        for f in files:
            if f.endswith(".py") and f != "truth_audit.py":
                target_files.append(os.path.join(root, f))

    for path in target_files:
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines, 1):
            # Exclude comments or docstrings explaining the rule
            cleaned = line.strip()
            if cleaned.startswith("#") or cleaned.startswith("//") or "help=" in cleaned or "forbidden_tokens" in cleaned:
                continue
            for pattern, desc in forbidden_tokens:
                if re.search(pattern, cleaned):
                    violations.append(f"{path}:{idx} - {desc}: '{cleaned}'")

    # Check for time.sleep in run_fault.py
    run_fault_path = "scripts/run_fault.py"
    if os.path.exists(run_fault_path):
        with open(run_fault_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if "time.sleep(" in line and not line.strip().startswith("#"):
                    violations.append(f"{run_fault_path}:{idx} - Forbidden time.sleep simulation: '{line.strip()}'")

    return violations

def audit_chaos_mocks() -> List[str]:
    violations = []
    chaos_test_dir = "tests/chaos"
    if not os.path.exists(chaos_test_dir):
        return violations

    for root, _, files in os.walk(chaos_test_dir):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(root, f)
                with open(path, "r", encoding="utf-8") as fh:
                    content = fh.read()
                if "patch(" in content and "httpx" in content:
                    violations.append(f"{path} - Forbidden mock of httpx in chaos tests (Rule 2)")
                if "AsyncMock" in content and "httpx" in content:
                    violations.append(f"{path} - Forbidden AsyncMock of httpx in chaos tests (Rule 2)")

    return violations

def audit_report_consistency() -> List[str]:
    violations = []
    reports_dir = "reports"
    if not os.path.exists(reports_dir):
        return violations

    receipt_file = os.path.join(reports_dir, "evidence_receipt.json")
    if os.path.exists(receipt_file):
        try:
            with open(receipt_file, "r", encoding="utf-8") as f:
                receipt = json.load(f)
            sha = receipt.get("commit_sha")
            if sha:
                # Check if SHA exists in git
                res = subprocess.run(["git", "cat-file", "-e", sha], capture_output=True)
                if res.returncode != 0:
                    violations.append(f"reports/evidence_receipt.json commit_sha '{sha}' does not exist in git history")
        except Exception as exc:
            violations.append(f"Could not parse evidence_receipt.json: {exc}")

    return violations

def main():
    print("=================================================================")
    print(" FaultForge Truth Audit (Anti-Fake Guard)")
    print("=================================================================")

    violations = []
    violations.extend(audit_forbidden_patterns())
    violations.extend(audit_chaos_mocks())
    violations.extend(audit_report_consistency())

    if violations:
        print(f"\n[-] FAILED: Found {len(violations)} truth audit violation(s):")
        for v in violations:
            print(f"    - {v}")
        print("\nFix all violations to satisfy Rule 1 (Never Fabricate Evidence).\n")
        sys.exit(1)
    else:
        print("\n[+] PASSED: Zero forbidden patterns, zero mocked chaos tests, clean audit.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()
