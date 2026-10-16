#!/usr/bin/env python3
import os
import re
import sys
import json
import subprocess
from typing import List, Tuple

def audit_forbidden_patterns() -> List[str]:
    violations = []
    zero_sha_pattern = r"\b" + ("0" * 40) + r"\b"
    forbidden_tokens = [
        (r"\|\|\s*true", "Masked failure (|| true)"),
        (r"\|\|\s*echo", "Masked failure (|| echo)"),
        (r"default-hash", "Hardcoded placeholder hash (default-hash)"),
        (zero_sha_pattern, "Zero-SHA fallback (0{40})"),
        (r"rev-candidate", "Placeholder candidate revision (rev-candidate)"),
        (r"rev-stable", "Placeholder stable revision (rev-stable)"),
        (r"faultforge/pipeline/local", "Fake pipeline URL (faultforge/pipeline/local)"),
        (r"duo_" + r"orchestrator", "Deleted mock orchestrator reference (" + "duo_" + "orchestrator)"),
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
            cleaned = line.strip()
            if cleaned.startswith("#") or cleaned.startswith("//") or "help=" in cleaned or "forbidden_tokens" in cleaned:
                continue
            for pattern, desc in forbidden_tokens:
                if re.search(pattern, cleaned):
                    violations.append(f"{path}:{idx} - {desc}: '{cleaned}'")

    collect_evidence_path = "scripts/collect_evidence.py"
    if os.path.exists(collect_evidence_path):
        with open(collect_evidence_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                cleaned = line.strip()
                if cleaned.startswith("#"):
                    continue
                if re.search(r'["\']latency_ms["\']\s*:\s*3500', cleaned) or re.search(r'\blatency_ms\s*=\s*3500', cleaned):
                    violations.append(f"{collect_evidence_path}:{idx} - Hardcoded latency_ms: 3500 (must be dynamically read from profile)")

    run_fault_path = "scripts/run_fault.py"
    if os.path.exists(run_fault_path):
        with open(run_fault_path, "r", encoding="utf-8") as f:
            for idx, line in enumerate(f, 1):
                if "time.sleep(" in line and not line.strip().startswith("#"):
                    violations.append(f"{run_fault_path}:{idx} - Forbidden time.sleep simulation: '{line.strip()}'")

    return violations

def audit_flow_yaml() -> List[str]:
    violations = []
    flow_path = "flows/faultforge-flow.yaml"
    if not os.path.exists(flow_path):
        return violations

    with open(flow_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for idx, line in enumerate(lines, 1):
        cleaned = line.strip()
        if cleaned.startswith("#"):
            continue
        if re.search(r"^\s*model\s*:", line) or "claude-3-5-sonnet" in line or "claude-" in line or "gpt-" in line:
            violations.append(f"{flow_path}:{idx} - Model ID specified in flow YAML: '{cleaned}' (platform manages model selection)")

    return violations

def audit_gitlab_ci_todos(final_mode: bool = False) -> List[str]:
    violations = []
    ci_file = ".gitlab-ci.yml"
    if not os.path.exists(ci_file):
        return violations

    if not final_mode and os.getenv("FINAL_AUDIT") != "1":
        return violations

    with open(ci_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    for idx, line in enumerate(lines, 1):
        cleaned = line.strip()
        if "when: manual" in cleaned and "TODO" in cleaned:
            violations.append(f"{ci_file}:{idx} - Incomplete stage marked 'when: manual' with TODO: '{cleaned}'")

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
                res = subprocess.run(["git", "cat-file", "-e", sha], capture_output=True)
                if res.returncode != 0:
                    violations.append(f"reports/evidence_receipt.json commit_sha '{sha}' does not exist in git history")
        except Exception as exc:
            violations.append(f"Could not parse evidence_receipt.json: {exc}")

    return violations

def main():
    final_audit = ("--final-audit" in sys.argv) or (os.getenv("FINAL_AUDIT") == "1")
    print("=================================================================")
    print(f" FaultForge Truth Audit (Anti-Fake Guard) {'[FINAL MODE]' if final_audit else ''}")
    print("=================================================================")

    violations = []
    violations.extend(audit_forbidden_patterns())
    violations.extend(audit_flow_yaml())
    violations.extend(audit_gitlab_ci_todos(final_mode=final_audit))
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
