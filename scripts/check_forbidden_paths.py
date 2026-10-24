#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge Enforced Safety Guard: Forbidden Paths Validator.
Verifies that candidate changes do not touch forbidden security boundaries,
authentication, payment processing, schemas, secrets, IAM, or CI/flow definitions.
Enforces strict allowlisting: only automated remediation scope
(app/clients/shipping_client.py, app/resilience/, tests/) and explicitly documented
human/orchestration files are permitted.
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

from typing import List, Tuple, Any

# Automated remediation scope: Duo AI or candidate patch
ALLOWED_REMEDIATION_PATHS = [
    "app/clients/shipping_client.py",
    "app/resilience/"
]

# Documented human and platform orchestration changes (with commit authors and purpose)
DOCUMENTED_ORCHESTRATION_FILES = {
    "app/main.py": "Human/Orchestration: Evidence and health API endpoints, request timing middleware (Author: rajpriyanid)",
    "app/dashboard.html": "Human/Orchestration: Visual review dashboard (Author: FaultForge Maintainer)",
    "app/clients/orbit_client.py": "Human/Orchestration: AST + Git fallback stub for Duo Orbit (Author: FaultForge Maintainer)"
}

def is_existing_git_file(rel_path: str) -> bool:
    """Check if a file exists in the current git repository index/HEAD or workspace."""
    if os.path.exists(".git"):
        try:
            import subprocess
            res = subprocess.run(
                ["git", "ls-files", "--error-unmatch", rel_path],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
            if res.returncode == 0:
                return True
        except Exception:
            pass
    return os.path.exists(rel_path)

def parse_file_entry(entry: Any) -> Tuple[str, str]:
    """
    Parse an input file entry into (normalized_path, status).
    Status may be 'A' (added), 'M' (modified), 'D' (deleted), or '' (unspecified).
    """
    if isinstance(entry, (tuple, list)) and len(entry) >= 2:
        if len(str(entry[0])) <= 2:  # ('A', 'path')
            return str(entry[1]).replace("\\", "/").strip(), str(entry[0]).strip().upper()
        return str(entry[0]).replace("\\", "/").strip(), str(entry[1]).strip().upper()

    line = str(entry).strip()
    if not line:
        return "", ""

    # Check for git diff status prefix: e.g. "A\tpath", "M\tpath", "D\tpath", "A  path"
    match = re.match(r"^([AMDCR])\s+(.+)$", line)
    if match:
        status = match.group(1).upper()
        path = match.group(2).replace("\\", "/").strip()
        return path, status

    return line.replace("\\", "/").strip(), ""

def check_file(file_path: str) -> List[Tuple[str, str]]:
    norm = file_path.replace("\\", "/").strip()
    if not norm:
        return []
    
    violations = []
    for pat, desc in FORBIDDEN_PATTERNS:
        if pat.search(norm):
            violations.append((norm, f"Forbidden boundary violation: {desc}"))

    return violations

def validate_changed_files(files: List[Any], mode: str = "auto") -> bool:
    all_violations = []
    parsed_entries = [parse_file_entry(f) for f in files if str(f).strip()]

    print(f"[*] Validating {len(parsed_entries)} changed file(s) against safety boundaries (mode: {mode}):")

    for norm, status in parsed_entries:
        if not norm:
            continue

        violations = check_file(norm)
        if violations:
            all_violations.extend(violations)
            continue
        
        in_remediation = any(norm == p or norm.startswith(p) for p in ALLOWED_REMEDIATION_PATHS)
        in_orchestration = norm in DOCUMENTED_ORCHESTRATION_FILES

        if in_remediation:
            print(f"  [+] Allowed Remediation Scope: {norm} (status: {status or 'active'})")
        elif in_orchestration:
            print(f"  [+] Documented Orchestration: {norm} ({DOCUMENTED_ORCHESTRATION_FILES[norm]})")
        elif norm.startswith("tests/"):
            # Enforce: automated remediation may ONLY ADD files under tests/ (no edits or deletes of existing tests)
            is_addition = (status == "A") or (status == "" and mode == "automated_remediation" and not is_existing_git_file(norm))
            is_edit_or_delete = (status in ("M", "D", "R")) or (status == "" and mode == "automated_remediation" and is_existing_git_file(norm))

            if is_addition:
                print(f"  [+] Allowed Remediation Scope (New Test Addition): {norm}")
            elif is_edit_or_delete:
                v_desc = f"Automated remediation may only ADD files under tests/ (edits or deletes of existing tests are forbidden: status='{status or 'modified'}')"
                all_violations.append((norm, v_desc))
                print(f"  [-] Forbidden Test Modification: {norm} ({v_desc})")
            else:
                # In general/permissive mode without explicit modification status
                print(f"  [+] Test Suite Maintenance: {norm}")
        else:
            violation_desc = "Out-of-scope modification (allowed: app/clients/shipping_client.py, app/resilience/, additions under tests/; or documented orchestration)"
            all_violations.append((norm, violation_desc))
            print(f"  [-] Out of Scope: {norm}")

    if all_violations:
        print(f"\n[-] SAFETY GUARD VIOLATION: Found {len(all_violations)} forbidden or out-of-scope file(s):")
        for fn, reason in all_violations:
            print(f"    - {fn}: {reason}")
        return False

    print("\n[+] Safety Guard PASSED: Zero forbidden paths modified. All changes within approved scope.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Enforce safety boundaries on candidate branch files")
    parser.add_argument("--files", nargs="*", default=[], help="List of modified files to validate")
    parser.add_argument("--mode", default="auto", choices=["auto", "automated_remediation"], help="Validation mode")
    parser.add_argument("--name-status", action="store_true", help="Parse input as git diff --name-status lines")
    args = parser.parse_args()

    files = args.files
    if not files and not sys.stdin.isatty():
        files = sys.stdin.read().splitlines()

    if not files:
        print("[*] No files provided to check_forbidden_paths.py; passing by default.")
        sys.exit(0)

    if not validate_changed_files(files, mode=args.mode):
        sys.exit(1)

    sys.exit(0)

if __name__ == "__main__":
    main()
