#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge Enforced Safety Guard: Forbidden Paths Validator.
Verifies that an AI/Duo-authored candidate branch does not touch forbidden
security boundaries, authentication, payment processing, schemas, secrets, IAM,
or CI/flow definitions.
"""
import sys
import os
import re
import argparse
from typing import List, Tuple

FORBIDDEN_PATTERNS = [
    (re.compile(r"(?:^|/)(?:auth|login|jwt|token|oauth|credentials)", re.IGNORECASE), "Authentication / Authorization"),
    (re.compile(r"(?:^|/)(?:payment|billing|stripe|invoice)", re.IGNORECASE), "Payment Processing"),
    (re.compile(r"(?:^|/)(?:schema|migrations?|database|db|models/db)", re.IGNORECASE), "Database Schemas / Migrations"),
    (re.compile(r"\.(?:env|key|pem|secret)$", re.IGNORECASE), "Secrets / Certificates"),
    (re.compile(r"(?:^|/)iam(?:/|_)", re.IGNORECASE), "IAM / Cloud Permissions"),
    (re.compile(r"^\.gitlab-ci\.yml$", re.IGNORECASE), "CI/CD Pipeline Definition"),
    (re.compile(r"^flows/", re.IGNORECASE), "Duo Agent Flow Specifications"),
    (re.compile(r"^\.gitlab/", re.IGNORECASE), "GitLab Governance Configurations")
]

ALLOWED_CANDIDATE_PREFIXES = [
    "app/clients/",
    "app/resilience/",
    "app/",
    "tests/chaos/",
    "tests/unit/",
    "tests/integration/"
]

def check_file(file_path: str) -> List[Tuple[str, str]]:
    norm = file_path.replace("\\", "/").strip()
    if not norm:
        return []
    
    violations = []
    for pat, desc in FORBIDDEN_PATTERNS:
        if pat.search(norm):
            violations.append((norm, desc))

    return violations

def validate_changed_files(files: List[str]) -> bool:
    all_violations = []
    clean_files = [f.strip() for f in files if f.strip()]

    print(f"[*] Validating {len(clean_files)} changed file(s) against safety boundaries...")

    for f in clean_files:
        norm = f.replace("\\", "/").strip()
        violations = check_file(norm)
        if violations:
            all_violations.extend(violations)
        
        # Check that candidate changes are within permitted application scope
        in_scope = any(norm.startswith(prefix) for prefix in ALLOWED_CANDIDATE_PREFIXES)
        if not in_scope and not violations:
            all_violations.append((norm, "Out-of-scope modification (allowed: app/clients/, app/resilience/, tests/)"))

    if all_violations:
        print(f"\n[-] SAFETY GUARD VIOLATION: Candidate branch modified forbidden or out-of-scope files:")
        for fn, reason in all_violations:
            print(f"    - {fn}: {reason}")
        return False

    print("[+] Safety Guard PASSED: Zero forbidden paths modified. All changes within approved resilience scope.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Enforce safety boundaries on candidate branch files")
    parser.add_argument("--files", nargs="*", default=[], help="List of modified files to validate")
    args = parser.parse_args()

    files = args.files
    if not files and not sys.stdin.isatty():
        files = sys.stdin.read().splitlines()

    if not files:
        print("[*] No files provided to check_forbidden_paths.py; passing by default.")
        sys.exit(0)

    if not validate_changed_files(files):
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
