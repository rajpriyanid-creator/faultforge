#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
import re
import sys
import time
import json
import hashlib
import subprocess
from typing import List, Tuple, Optional

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

def hash_file_sha256(path: str) -> str:
    if not os.path.exists(path):
        return ""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def get_repo_first_commit_info() -> Tuple[Optional[float], Optional[str]]:
    is_ci = os.getenv("CI") == "true" or os.getenv("GITLAB_CI") == "true"
    try:
        out = subprocess.check_output(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            text=True, stderr=subprocess.DEVNULL
        ).strip().splitlines()
        if out:
            root_sha = out[0]
            ts_str = subprocess.check_output(
                ["git", "show", "-s", "--format=%ct", root_sha],
                text=True, stderr=subprocess.DEVNULL
            ).strip()
            return float(ts_str), root_sha
    except Exception:
        pass
    if is_ci:
        return None, "CI_GIT_MISSING"
    print("WARNING: no git history available, history-based checks SKIPPED")
    return None, None

def audit_timestamps(timestamps: List[float], first_commit_ts: Optional[float]) -> List[str]:
    violations = []
    now = time.time()
    for ts in timestamps:
        if first_commit_ts and ts < first_commit_ts:
            violations.append(f"Timestamp {ts} is before repository's first commit date ({first_commit_ts})")
        if ts > now + 60.0:
            violations.append(f"Timestamp {ts} is in the future (current time: {now})")

    # Check exact multiples of 30 or 60 across 3+ consecutive stages
    mult30_count = 0
    for ts in timestamps:
        if int(ts) > 0 and int(ts) % 30 == 0:
            mult30_count += 1
            if mult30_count >= 3:
                violations.append("Stale/fabricated timestamps detected: exact multiples of 30/60s across 3+ consecutive stages")
                break
        else:
            mult30_count = 0

    # Check evenly spaced across 3+ consecutive stages (diffs identical within 0.01s)
    if len(timestamps) >= 3:
        for i in range(2, len(timestamps)):
            diff1 = round(timestamps[i] - timestamps[i-1], 2)
            diff2 = round(timestamps[i-1] - timestamps[i-2], 2)
            if diff1 > 0 and abs(diff1 - diff2) < 0.01:
                violations.append(f"Stale/fabricated timestamps detected: evenly spaced intervals ({diff1}s) across consecutive stages")
                break
    return violations

def audit_report_consistency(final_mode: bool = False) -> List[str]:
    violations = []
    reports_dir = "reports"
    sample_dir = os.path.join("docs", "sample_reports")

    receipt_file = os.path.join(reports_dir, "evidence_receipt.json")
    ledger_file = os.path.join(reports_dir, "stage_ledger.json")

    is_ci = os.getenv("CI") == "true" or os.getenv("GITLAB_CI") == "true"
    first_commit_ts, root_sha = get_repo_first_commit_info()
    if root_sha == "CI_GIT_MISSING":
        violations.append("Running in CI environment but .git repository history is missing")

    if final_mode:
        if not os.path.exists(receipt_file) and not os.path.exists(ledger_file):
            violations.append("no CI evidence present (`reports/` is empty)")
        else:
            if not os.path.exists(receipt_file):
                violations.append(f"Final audit requires active {receipt_file} to exist and be generated at runtime")
            if not os.path.exists(ledger_file):
                violations.append(f"Final audit requires active {ledger_file} to exist and record pipeline stages")

    receipt_data = {}
    if os.path.exists(receipt_file):
        try:
            with open(receipt_file, "r", encoding="utf-8") as f:
                receipt = json.load(f)
            receipt_data = receipt
            sha = receipt.get("commit_sha")

            # Receipt commit SHA verification
            if is_ci:
                ci_sha = os.getenv("CI_COMMIT_SHA")
                if ci_sha and sha != ci_sha:
                    violations.append(f"Receipt commit_sha '{sha}' does not equal CI_COMMIT_SHA '{ci_sha}'")
            elif first_commit_ts is not None and sha and sha != "UNKNOWN_NO_GIT":
                try:
                    res = subprocess.run(["git", "merge-base", "--is-ancestor", sha, "HEAD"], capture_output=True)
                    if res.returncode != 0:
                        # Also check if exactly HEAD
                        head_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
                        if sha != head_sha:
                            violations.append(f"reports/evidence_receipt.json commit_sha '{sha}' is not an ancestor of HEAD")
                except Exception:
                    pass

            # Timestamp check on receipt
            gen_at = receipt.get("generated_at")
            if gen_at is not None:
                violations.extend(audit_timestamps([float(gen_at)], first_commit_ts))

            # Merge request URL check
            mr_url = receipt.get("urls", {}).get("merge_request_url")
            if mr_url:
                if not re.search(r"/-/merge_requests/\d+", mr_url):
                    violations.append(f"Invalid merge_request_url in receipt: '{mr_url}' (must match /-/merge_requests/<n> or be null/absent)")

            # Verify cryptographic seal
            seal = receipt.get("tamper_evident_seal_sha256")
            if seal:
                copied = dict(receipt)
                copied.pop("tamper_evident_seal_sha256", None)
                computed = hashlib.sha256(json.dumps(copied, sort_keys=True).encode("utf-8")).hexdigest()
                if computed != seal:
                    violations.append(f"Evidence receipt SHA-256 seal mismatch: expected {seal}, computed {computed}")

            # Enforce honest Duo execution claims
            duo_exec = receipt.get("duo_execution", {})
            if duo_exec.get("executed") is False and receipt.get("final_status") == "RECOVERED_AND_VERIFIED":
                violations.append("Evidence receipt claims RECOVERED_AND_VERIFIED despite unexecuted Duo flow (executed: false)")
        except Exception as exc:
            violations.append(f"Could not parse evidence_receipt.json: {exc}")

    if os.path.exists(ledger_file):
        try:
            with open(ledger_file, "r", encoding="utf-8") as f:
                ledger = json.load(f)
            stages = ledger.get("stages", {})
            if final_mode and len(stages) < 1:
                violations.append("Stage ledger has no recorded stages in final mode")

            stage_timestamps = []
            receipt_sha = receipt_data.get("commit_sha")

            for stg_name, stg_data in stages.items():
                stg_ts = stg_data.get("timestamp")
                if stg_ts is not None:
                    stage_timestamps.append(float(stg_ts))

                # Check ledger commit_sha matches receipt commit_sha
                stg_sha = stg_data.get("commit_sha")
                if receipt_sha and stg_sha and stg_sha != "UNKNOWN_NO_GIT" and receipt_sha != "UNKNOWN_NO_GIT":
                    if stg_sha != receipt_sha:
                        violations.append(f"Ledger stage '{stg_name}' commit_sha '{stg_sha}' does not match receipt commit_sha '{receipt_sha}'")

                # Verify declared artifact paths exist and checksum matches
                for detail in stg_data.get("artifacts_details", []):
                    art_path = detail.get("path")
                    art_sha = detail.get("sha256")
                    if art_path:
                        if not os.path.exists(art_path):
                            violations.append(f"Ledger stage '{stg_name}' verified artifact missing on disk: {art_path}")
                        elif art_sha:
                            actual_sha = hash_file_sha256(art_path)
                            if actual_sha != art_sha:
                                violations.append(f"Ledger stage '{stg_name}' verified artifact checksum mismatch for {art_path}: expected {art_sha}, got {actual_sha}")

            # Audit stage timestamps spacing and chronology
            if stage_timestamps:
                violations.extend(audit_timestamps(stage_timestamps, first_commit_ts))

        except Exception as exc:
            violations.append(f"Could not parse stage_ledger.json: {exc}")

    # Verify docs/sample_reports/* byte-identical check
    if os.path.exists(sample_dir) and os.path.exists(reports_dir):
        sample_readme_path = os.path.join(sample_dir, "README.md")
        sample_readme_content = ""
        if os.path.exists(sample_readme_path):
            with open(sample_readme_path, "r", encoding="utf-8") as srf:
                sample_readme_content = srf.read()
        
        # Check if sample README names a real pipeline (does not have placeholder <ID> or <SHA>)
        has_real_pipeline = ("<ID>" not in sample_readme_content and "<SHA>" not in sample_readme_content and "pipeline" in sample_readme_content.lower())
        
        if not has_real_pipeline:
            for s_file in os.listdir(sample_dir):
                s_path = os.path.join(sample_dir, s_file)
                r_path = os.path.join(reports_dir, s_file)
                if os.path.isfile(s_path) and os.path.isfile(r_path) and s_file != "README.md":
                    if hash_file_sha256(s_path) == hash_file_sha256(r_path):
                        violations.append(f"docs/sample_reports/{s_file} is byte-identical to reports/{s_file} but sample README has not named the producing pipeline")

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

