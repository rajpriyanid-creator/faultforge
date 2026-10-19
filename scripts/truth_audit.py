#!/usr/bin/env python3
import os
import re
import sys
import json
import hashlib
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

def audit_report_consistency(final_mode: bool = False) -> List[str]:
    violations = []
    reports_dir = "reports"
    sample_dir = os.path.join("docs", "sample_reports")

    # Verify sample reports exist for reference documentation
    required_samples = ["evidence_receipt.json", "incident_dossier.json", "stage_ledger.json"]
    for s_file in required_samples:
        p = os.path.join(sample_dir, s_file)
        if not os.path.exists(p):
            violations.append(f"Missing documentation sample report: {p}")

    receipt_file = os.path.join(reports_dir, "evidence_receipt.json")
    ledger_file = os.path.join(reports_dir, "stage_ledger.json")

    if final_mode:
        if not os.path.exists(receipt_file):
            violations.append(f"Final audit requires active {receipt_file} to exist and be generated at runtime")
        if not os.path.exists(ledger_file):
            violations.append(f"Final audit requires active {ledger_file} to exist and record pipeline stages")

    if os.path.exists(receipt_file):
        try:
            with open(receipt_file, "r", encoding="utf-8") as f:
                receipt = json.load(f)
            sha = receipt.get("commit_sha")
            if sha:
                try:
                    res = subprocess.run(["git", "cat-file", "-e", sha], capture_output=True)
                    if res.returncode != 0:
                        violations.append(f"reports/evidence_receipt.json commit_sha '{sha}' does not exist in git history")
                except FileNotFoundError:
                    pass  # Git CLI not present in minimal container image

            # Verify cryptographic seal
            seal = receipt.get("tamper_evident_seal_sha256")
            if seal:
                copied = dict(receipt)
                copied.pop("tamper_evident_seal_sha256", None)
                computed = hashlib.sha256(json.dumps(copied, sort_keys=True).encode("utf-8")).hexdigest()
                if computed != seal:
                    violations.append(f"Evidence receipt SHA-256 seal mismatch: expected {seal}, computed {computed}")
        except Exception as exc:
            violations.append(f"Could not parse evidence_receipt.json: {exc}")

    if os.path.exists(ledger_file):
        try:
            with open(ledger_file, "r", encoding="utf-8") as f:
                ledger = json.load(f)
            stages = ledger.get("stages", {})
            if final_mode and len(stages) < 1:
                violations.append("Stage ledger has no recorded stages in final mode")
        except Exception as exc:
            violations.append(f"Could not parse stage_ledger.json: {exc}")

    return violations

def audit_docs_claims() -> List[str]:
    violations = []
    baseline_path = "reports/fault_run_baseline.json"
    if not os.path.exists(baseline_path):
        baseline_path = "docs/sample_reports/fault_run_baseline.json"

    receipt_path = "reports/evidence_receipt.json"
    if not os.path.exists(receipt_path):
        receipt_path = "docs/sample_reports/evidence_receipt.json"

    baseline_data = {}
    if os.path.exists(baseline_path):
        try:
            with open(baseline_path, "r", encoding="utf-8") as bf:
                baseline_data = json.load(bf)
        except Exception as e:
            violations.append(f"Could not load {baseline_path} for claims audit: {e}")

    receipt_data = {}
    if os.path.exists(receipt_path):
        try:
            with open(receipt_path, "r", encoding="utf-8") as rf:
                receipt_data = json.load(rf)
        except Exception as e:
            violations.append(f"Could not load {receipt_path} for claims audit: {e}")

    doc_files = [
        "README.md",
        "docs/architecture.md",
        "docs/measurement-method.md",
        "docs/safety-policy.md",
        "docs/hackathon-submission.md",
        "docs/demo-script.md",
    ]

    expected_stages = 9
    expected_budget = 1500
    expected_culprit = "974035c"

    for doc in doc_files:
        if not os.path.exists(doc):
            continue
        with open(doc, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        # Check track selection: Path A
        if "Path B — Bring Your Own" in content:
            violations.append(f"{doc} - Mismatched track selection: claims Path B instead of Path A")

        # Check stage count claims: 9 lifecycle stages
        stage_matches = re.findall(r"(\d+)\s+(?:Covered\s+)?(?:Lifecycle\s+)?Stages", content, re.IGNORECASE)
        for sm in stage_matches:
            if int(sm) != expected_stages:
                violations.append(f"{doc} - Mismatched lifecycle stage claim: claims {sm} stages instead of {expected_stages}")

        # Check budget claims
        budget_matches = re.findall(r"(\d+)\s*ms\s+SLA\s+budget", content, re.IGNORECASE)
        for bm in budget_matches:
            if int(bm) != expected_budget:
                violations.append(f"{doc} - Mismatched SLA budget claim: claims {bm}ms instead of {expected_budget}ms")

        # Check culprit commit
        if "974035" not in content and "culprit" in content.lower():
            violations.append(f"{doc} - Missing or mismatched culprit commit SHA reference (expected {expected_culprit})")

        # Verify reference baseline latency claim (3742ms) against reference sample report
        sample_baseline_path = "docs/sample_reports/fault_run_baseline.json"
        if os.path.exists(sample_baseline_path):
            try:
                with open(sample_baseline_path, "r", encoding="utf-8") as sbf:
                    s_data = json.load(sbf)
                s_avg = s_data.get("metrics", {}).get("avg_ms")
                if s_avg and "3742" in content and abs(float(s_avg) - 3742.46) > 1.0:
                    violations.append(f"{doc} - Claimed reference avg latency 3742ms does not match sample report ({s_avg}ms)")
            except Exception:
                pass

        # For live runtime baseline, verify that real_avg genuinely breached the SLA budget
        if baseline_data:
            metrics = baseline_data.get("metrics", {})
            real_avg = metrics.get("avg_ms")
            if real_avg is not None and real_avg <= expected_budget:
                violations.append(f"Runtime baseline failure not established: avg latency {real_avg}ms <= {expected_budget}ms budget")

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
    violations.extend(audit_report_consistency(final_mode=final_audit))
    violations.extend(audit_docs_claims())

    if violations:
        print(f"\n[-] FAILED: Found {len(violations)} truth audit violation(s):")
        for v in violations:
            print(f"    - {v}")
        print("\nFix all violations to satisfy Rule 1 (Never Fabricate Evidence).\n")
        sys.exit(1)
    else:
        print("\n[+] PASSED: Zero forbidden patterns, zero mocked chaos tests, clean claims audit.\n")
        sys.exit(0)

if __name__ == "__main__":
    main()

