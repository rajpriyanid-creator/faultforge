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
from datetime import datetime, timezone

def audit_forbidden_patterns() -> List[str]:
    violations = []
    zero_sha_pattern = r"\b" + ("0" * 40) + r"\b"
    forbidden_tokens = [
        (r"\|\|\s*true", "Masked failure (|| true)"),
        (r"\|\|\s*echo", "Masked failure (|| echo)"),
        (r"default-hash", "Hardcoded stub hash (default-hash)"),
        (zero_sha_pattern, "Zero-SHA fallback (0{40})"),
        (r"rev-candidate", "Mock candidate revision (rev-candidate)"),
        (r"rev-stable", "Mock stable revision (rev-stable)"),
        (r"faultforge/pipeline/local", "Fake pipeline URL (faultforge/pipeline/local)"),
        (r"duo_" + r"orchestrator", "Deleted mock orchestrator reference (" + "duo_" + "orchestrator)"),
    ]

    hardcoded_metric_literals = [
        (r"\b3557\.22\b", "Hardcoded fallback metric literal (3557.22)"),
        (r"\b487\.12\b", "Hardcoded fallback metric literal (487.12)"),
        (r"\b808\.95\b", "Hardcoded fallback metric literal (808.95)"),
        (r"\b812\.51\b", "Hardcoded fallback metric literal (812.51)"),
        (r"\b810\.06\b", "Hardcoded fallback metric literal (810.06)"),
        (r"\b164\.17\b", "Hardcoded fallback metric literal (164.17)"),
        (r"\b3558\.46\b", "Hardcoded fallback metric literal (3558.46)"),
        (r"\b484\.27\b", "Hardcoded fallback metric literal (484.27)"),
        (r"\b806\.79\b", "Hardcoded fallback metric literal (806.79)"),
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
            if path.startswith("scripts") and path.endswith(".py"):
                for pattern, desc in hardcoded_metric_literals:
                    if re.search(pattern, cleaned):
                        violations.append(f"{path}:{idx} - {desc}: '{cleaned}' (must read dynamically from replay evaluation)")

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

    # Audit app/ codebase to guarantee zero evidence field synthesis or defaulting and zero evidence write routes
    for root, _, files in os.walk("app"):
        for f in files:
            if f.endswith(".py"):
                app_path = os.path.join(root, f)
                with open(app_path, "r", encoding="utf-8", errors="ignore") as apf:
                    for idx, line in enumerate(apf, 1):
                        cl = line.strip()
                        if cl.startswith("#"):
                            continue
                        if re.search(r"@app\.(?:post|put|patch|delete)\(.*evidence", cl, re.IGNORECASE) or re.search(r"@app\.route\(.*methods=.*(?:post|put|patch|delete).*evidence", cl, re.IGNORECASE):
                            violations.append(f"{app_path}:{idx} - Forbidden evidence write route detected: '{cl}' (/api/v1/evidence must be read-only)")
                        if "_RUNTIME_EVIDENCE_RECEIPT" in cl:
                            violations.append(f"{app_path}:{idx} - Forbidden runtime evidence mutable storage: '{cl}'")
                        if "setdefault" in cl and any(k in cl for k in ("probe_", "approval_", "duo_", "identical_")):
                            violations.append(f"{app_path}:{idx} - Forbidden evidence synthesis pattern: setdefault on receipt key: '{cl}'")
                        if "data[" in cl and any(k in cl for k in ("probe_count", "probe_results", "approval_timestamp", "identical_replay_confirmed")):
                            violations.append(f"{app_path}:{idx} - Forbidden evidence synthesis pattern: mutating receipt data: '{cl}'")
                        if "CONFIRMED" in cl and ("COMPLETED" in cl or "duo_execution" in cl):
                            violations.append(f"{app_path}:{idx} - Forbidden evidence synthesis pattern: rewriting duo status to CONFIRMED: '{cl}'")

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
        incomplete_tag = "TO" + "DO"
        if "when: manual" in cleaned and incomplete_tag in cleaned:
            violations.append(f"{ci_file}:{idx} - Incomplete stage marked 'when: manual' with incomplete task: '{cleaned}'")

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
    with open(path, "rb") as f:
        content = f.read()
    # Normalize CRLF -> LF for line-ending-proof determinism across Windows/Linux/git archive
    normalized = content.replace(b"\r\n", b"\n")
    return hashlib.sha256(normalized).hexdigest()

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

def audit_report_consistency(final_mode: bool = False, reports_dir: str = "reports") -> List[str]:
    violations = []
    sample_dir = os.path.join("docs", "sample_reports")

    # If reports/ is empty or missing evidence, fallback to verified sample reports
    if not os.path.exists(os.path.join(reports_dir, "evidence_receipt.json")) and not os.path.exists(os.path.join(reports_dir, "stage_ledger.json")):
        sample_receipt = os.path.join(sample_dir, "evidence_receipt.json")
        sample_ledger = os.path.join(sample_dir, "stage_ledger.json")
        if os.path.exists(sample_receipt) and os.path.exists(sample_ledger):
            print(f"[*] Active '{reports_dir}/' is empty. Auditing verified sample reports in '{sample_dir}/'.")
            reports_dir = sample_dir

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
            elif reports_dir == "reports" and first_commit_ts is not None and sha and sha != "UNKNOWN_NO_GIT":
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

            # Enforce app tree parity between replay and deployment
            if receipt.get("final_status") == "RECOVERED_AND_VERIFIED":
                if receipt.get("app_tree_matches_deployed") is False:
                    violations.append("Evidence receipt claims RECOVERED_AND_VERIFIED but app_tree_matches_deployed is false")
            replay_tree = receipt.get("replay_tree_sha")
            deployed_tree = receipt.get("deployed_tree_sha")
            if replay_tree and deployed_tree and replay_tree != deployed_tree:
                violations.append(f"Evidence receipt tree SHA mismatch: replay '{replay_tree}' vs deployed '{deployed_tree}'")

            # Audit promotion_gate vs approval_timestamp integrity
            appr_ts = receipt.get("approval_timestamp")
            prom_gate = receipt.get("promotion_gate") or receipt.get("governance", {}).get("promotion_gate", "")
            if appr_ts is not None and str(prom_gate).startswith("BLOCKED"):
                violations.append(
                    f"Evidence receipt integrity violation: approval_timestamp ({appr_ts}) is recorded but promotion_gate is '{prom_gate}' (must be null while blocked)"
                )

            # Enforce consistency between duo_run.json and evidence_receipt.json
            duo_run_file = os.path.join(reports_dir, "duo_run.json")
            if not os.path.exists(duo_run_file):
                duo_run_file = os.path.join(sample_dir, "duo_run.json")
            if os.path.exists(duo_run_file):
                try:
                    with open(duo_run_file, "r", encoding="utf-8") as drf:
                        duo_run_data = json.load(drf)
                    if duo_run_data.get("executed") is True and duo_exec.get("executed") is False:
                        violations.append("duo_run.json records executed: true, but evidence_receipt.json records duo_execution.executed: false")
                except Exception:
                    pass
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
                        if reports_dir != "reports":
                            disk_path = os.path.join(reports_dir, os.path.basename(art_path))
                        else:
                            disk_path = art_path

                        if not os.path.exists(disk_path):
                            violations.append(f"Ledger stage '{stg_name}' verified artifact missing on disk: {art_path}")
                        elif art_sha:
                            actual_sha = hash_file_sha256(disk_path)
                            if actual_sha != art_sha:
                                violations.append(f"Ledger stage '{stg_name}' verified artifact checksum mismatch for {art_path}: expected {art_sha}, got {actual_sha}")

            # Audit stage timestamps spacing and chronology
            if stage_timestamps:
                violations.extend(audit_timestamps(stage_timestamps, first_commit_ts))

        except Exception as exc:
            violations.append(f"Could not parse stage_ledger.json: {exc}")

    # Audit duo_evidence.json completeness when found=True and consistency with hardened replay
    duo_ev_file = os.path.join(reports_dir, "duo_evidence.json")
    hardened_file = os.path.join(reports_dir, "fault_run_hardened.json")
    hardened_sha = None
    if os.path.exists(hardened_file):
        try:
            with open(hardened_file, "r", encoding="utf-8") as hf:
                h_data = json.load(hf)
                hardened_sha = h_data.get("git_sha")
        except Exception:
            pass

    if os.path.exists(duo_ev_file):
        try:
            with open(duo_ev_file, "r", encoding="utf-8") as df:
                duo_data = json.load(df)
            if duo_data.get("found") is True:
                if not str(duo_data.get("diff_stat") or "").strip():
                    violations.append(f"{duo_ev_file} - diff_stat must not be empty when found=True")
                if not str(duo_data.get("explanation") or "").strip():
                    violations.append(f"{duo_ev_file} - explanation must not be empty when found=True")
                eval_sha = duo_data.get("evaluated_sha")
                if hardened_sha and eval_sha and eval_sha != hardened_sha:
                    violations.append(
                        f"{duo_ev_file} evaluated_sha ({eval_sha}) differs from replay's git_sha in {hardened_file} ({hardened_sha})"
                    )
        except Exception as exc:
            violations.append(f"Could not parse {duo_ev_file}: {exc}")

    # Verify docs/sample_reports/* byte-identical check
    if reports_dir != sample_dir and os.path.exists(sample_dir) and os.path.exists(reports_dir):
        sample_readme_path = os.path.join(sample_dir, "README.md")
        sample_readme_content = ""
        if os.path.exists(sample_readme_path):
            with open(sample_readme_path, "r", encoding="utf-8") as srf:
                sample_readme_content = srf.read()
        
        # Check if sample README names a real pipeline (does not have template <ID> or <SHA>)
        has_real_pipeline = ("<ID>" not in sample_readme_content and "<SHA>" not in sample_readme_content and "pipeline" in sample_readme_content.lower())
        
        if not has_real_pipeline:
            for s_file in os.listdir(sample_dir):
                s_path = os.path.join(sample_dir, s_file)
                r_path = os.path.join(reports_dir, s_file)
                if os.path.isfile(s_path) and os.path.isfile(r_path) and s_file != "README.md":
                    if hash_file_sha256(s_path) == hash_file_sha256(r_path):
                        violations.append(f"docs/sample_reports/{s_file} is byte-identical to reports/{s_file} but sample README has not named the producing pipeline")

    return violations

def audit_sample_reports_provenance(sample_dir: str = "docs/sample_reports") -> List[str]:
    violations = []
    if not os.path.exists(sample_dir):
        return violations

    readme_path = os.path.join(sample_dir, "README.md")
    if not os.path.exists(readme_path):
        return violations

    with open(readme_path, "r", encoding="utf-8") as f:
        readme_content = f.read()

    # 1. Discover declared pipeline execution windows
    pipeline_windows = {}
    current_pid = None
    for line in readme_content.splitlines():
        if line.strip().startswith("|"):
            continue
        pid_match = re.search(r"pipeline[^\d]*(\d{8,})", line, re.IGNORECASE)
        if pid_match:
            current_pid = pid_match.group(1)
        win_match = re.search(
            r"[`\"]?([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?)[`\"]?\s*to\s*[`\"]?([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?)[`\"]?",
            line,
            re.IGNORECASE
        )
        if win_match and current_pid:
            s_str, e_str = win_match.group(1), win_match.group(2)
            try:
                s_iso = s_str if s_str.endswith("Z") else s_str + "Z"
                e_iso = e_str if e_str.endswith("Z") else e_str + "Z"
                start_dt = datetime.fromisoformat(s_iso.replace("Z", "+00:00"))
                end_dt = datetime.fromisoformat(e_iso.replace("Z", "+00:00"))
                pipeline_windows[current_pid] = (start_dt, end_dt, s_str, e_str)
                current_pid = None
            except Exception:
                pass

    # 2. Blanket pipeline window check across fault run files
    window_match = re.search(
        r"Pipeline Execution Window:\s*[`\"]?([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?)[`\"]?\s*to\s*[`\"]?([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}Z?)[`\"]?",
        readme_content,
        re.IGNORECASE
    )
    if window_match:
        start_str, end_str = window_match.group(1), window_match.group(2)
        try:
            start_iso = start_str if start_str.endswith("Z") else start_str + "Z"
            end_iso = end_str if end_str.endswith("Z") else end_str + "Z"
            start_dt = datetime.fromisoformat(start_iso.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(end_iso.replace("Z", "+00:00"))

            for fname in ["fault_run_baseline.json", "fault_run_hardened.json"]:
                fpath = os.path.join(sample_dir, fname)
                if os.path.exists(fpath):
                    with open(fpath, "r", encoding="utf-8") as fp:
                        fdata = json.load(fp)
                    ts = fdata.get("timestamp")
                    if isinstance(ts, (int, float)):
                        fdt = datetime.fromtimestamp(ts, tz=timezone.utc)
                        if not (start_dt <= fdt <= end_dt):
                            violations.append(
                                f"docs/sample_reports/README.md claims pipeline window {start_str} to {end_str}, "
                                f"which does not contain {fname} timestamp {fdt.strftime('%Y-%m-%dT%H:%M:%SZ')}"
                            )
        except Exception as e:
            violations.append(f"Failed parsing claimed pipeline window in sample README: {e}")

    # 3. Parse and validate every table row in Section 2
    in_table = False
    for line in readme_content.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [c.strip() for c in stripped.split("|")[1:-1]]
        if len(cells) < 5:
            continue
        if cells[0].startswith("---") or cells[0].lower() in ["artifact file", "file"]:
            in_table = True
            continue
        if not in_table:
            continue

        file_name = re.sub(r"[`*]", "", cells[0]).strip()
        source_context = cells[3]
        time_str = cells[4]

        # Check if row attributes to a pipeline
        pipe_refs = re.findall(r"\b(29\d{8})\b", source_context)
        if pipe_refs:
            for pid in pipe_refs:
                if pid not in pipeline_windows:
                    violations.append(
                        f"docs/sample_reports/README.md table row '{file_name}' references pipeline {pid} "
                        f"which has no declared execution window in the README"
                    )
                    continue

                start_dt, end_dt, s_str, e_str = pipeline_windows[pid]
                time_match = re.search(r"([0-9]{4}-[0-9]{2}-[0-9]{2}[T\s][0-9]{2}:[0-9]{2}:[0-9]{2})", time_str)
                if time_match:
                    try:
                        row_ts_str = time_match.group(1).replace(" ", "T") + "Z"
                        row_dt = datetime.fromisoformat(row_ts_str.replace("Z", "+00:00"))
                        if not (start_dt <= row_dt <= end_dt):
                            violations.append(
                                f"docs/sample_reports/README.md table row '{file_name}' attributes generation to "
                                f"pipeline {pid} (window {s_str} to {e_str}), but generation time {time_str} "
                                f"falls outside this window"
                            )
                    except Exception as e:
                        violations.append(f"Failed parsing timestamp '{time_str}' in row for '{file_name}': {e}")
                else:
                    violations.append(
                        f"docs/sample_reports/README.md table row '{file_name}' references pipeline {pid} "
                        f"but has no valid generation timestamp in column 5 ('{time_str}')"
                    )
        else:
            if "local run" not in source_context.lower() and "platform session" not in source_context.lower():
                violations.append(
                    f"docs/sample_reports/README.md table row '{file_name}' does not name a pipeline "
                    f"and does not disclose 'Local run (pipeline not recorded)'"
                )

        # Check evidence_receipt.json specific attribution rule
        if file_name == "evidence_receipt.json":
            if "job 17392416795" in source_context.lower() and "not an artifact" not in source_context.lower():
                violations.append(
                    "docs/sample_reports/README.md attributes evidence_receipt.json to job 17392416795, "
                    "but it was sealed locally on 2026-10-23 03:44 UTC"
                )

    sample_rcpt = os.path.join(sample_dir, "evidence_receipt.json")
    if os.path.exists(sample_rcpt):
        try:
            with open(sample_rcpt, "r", encoding="utf-8") as rf:
                rcpt_data = json.load(rf)
            appr_ts = rcpt_data.get("approval_timestamp")
            prom_gate = rcpt_data.get("promotion_gate") or rcpt_data.get("governance", {}).get("promotion_gate", "")
            if appr_ts is not None and str(prom_gate).startswith("BLOCKED"):
                violations.append(
                    f"{sample_rcpt} integrity violation: approval_timestamp ({appr_ts}) is recorded but promotion_gate is '{prom_gate}' (must be null while blocked)"
                )
        except Exception:
            pass

    sample_hardened = os.path.join(sample_dir, "fault_run_hardened.json")
    sample_duo = os.path.join(sample_dir, "duo_evidence.json")
    if os.path.exists(sample_hardened) and os.path.exists(sample_duo):
        try:
            with open(sample_hardened, "r", encoding="utf-8") as shf, open(sample_duo, "r", encoding="utf-8") as sdf:
                s_hard_data = json.load(shf)
                s_duo_data = json.load(sdf)
            s_hard_sha = s_hard_data.get("git_sha")
            s_duo_sha = s_duo_data.get("evaluated_sha")
            if s_hard_sha and s_duo_sha and s_hard_sha != s_duo_sha:
                violations.append(
                    f"{sample_duo} evaluated_sha ({s_duo_sha}) differs from replay's git_sha in {sample_hardened} ({s_hard_sha})"
                )
        except Exception:
            pass

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

    core_doc_files = [
        "README.md",
        "AGENTS.md",
        "docs/architecture.md",
        "docs/measurement-method.md",
        "docs/safety-policy.md",
        "docs/hackathon-submission.md",
        "docs/demo-script.md",
    ]
    # Dynamically scan all markdown files under docs/ for stale figures
    all_markdown_files = list(core_doc_files)
    if os.path.exists("docs"):
        for root, _, files in os.walk("docs"):
            for f in files:
                if f.endswith(".md"):
                    full_p = os.path.join(root, f).replace("\\", "/")
                    if full_p not in all_markdown_files:
                        all_markdown_files.append(full_p)

    expected_stages = 9
    expected_budget = 1500
    expected_culprit = "974035c"

    # Canonical sample reports contain the documented replay evaluation referenced by README.md
    sample_replay_path = "docs/sample_reports/replay_evaluation.json"
    if not os.path.exists(sample_replay_path) and os.path.exists("reports/replay_evaluation.json"):
        sample_replay_path = "reports/replay_evaluation.json"

    replay_data = {}
    if os.path.exists(sample_replay_path):
        try:
            with open(sample_replay_path, "r", encoding="utf-8") as rf:
                replay_data = json.load(rf)
        except Exception as e:
            violations.append(f"Could not load {sample_replay_path} for claims audit: {e}")

    raw_metrics = replay_data.get("raw_metrics", {})
    reductions = replay_data.get("latency_reduction", {})

    # For live candidate replay run (when executed in CI), verify resilience gate passed
    live_replay_path = "reports/replay_evaluation.json"
    if os.path.exists(live_replay_path) and live_replay_path != sample_replay_path:
        try:
            with open(live_replay_path, "r", encoding="utf-8") as lrf:
                live_data = json.load(lrf)
            live_gates = live_data.get("gates", {})
            if not live_gates.get("candidate_resilience", {}).get("passed", False):
                violations.append("Runtime candidate replay failed resilience gate")
        except Exception as e:
            violations.append(f"Could not load {live_replay_path}: {e}")

    stale_figures = [
        (r"3446(?:\.08)?", "Stale reference baseline latency (3446/3446.08 ms)"),
        (r"246(?:\.18)?\s*ms", "Stale reference hardened latency (246/246.18 ms)"),
        (r"3653(?:\.06)?", "Stale reference p95 latency (3653/3653.06 ms)"),
        (r"3558(?:\.46)?\s*ms", "Stale reference baseline latency (3558/3558.46 ms)"),
        (r"484(?:\.27)?\s*ms", "Stale reference candidate mean latency (484/484.27 ms)"),
        (r"806(?:\.79)?\s*ms", "Stale reference candidate p95 latency (806/806.79 ms)"),
        (r"804(?:\.86)?\s*ms", "Stale reference candidate p50 latency (804/804.86 ms)"),
        (r"3540(?:\.65)?\s*ms", "Stale reference baseline p50 latency (3540/3540.65 ms)"),
        (r"3738(?:\.16)?\s*ms", "Stale reference baseline p95 latency (3738/3738.16 ms)"),
        (r"92\.9\s*%", "Stale reference mean latency reduction (92.9%)"),
        (r"86\.4\s*%", "Stale reference mean latency reduction (86.4%)"),
        (r"78\.4\s*%", "Stale reference p95 latency reduction (78.4%)"),
        (r"99\.9\s*%", "Stale reference p50 latency reduction (99.9%)"),
        (r"2\.88\s*ms", "Stale reference candidate p50 latency (2.88 ms)"),
        (r"within\s+820\s*ms", "Stale reference candidate bound (within 820 ms)"),
        (r"issues/29\b", "Stale incident issue URL (issues/29, expected work_items/42)"),
        (r"\b4212(?:\.32)?\b", "Stale baseline mean latency (4212/4212.32 ms)"),
        (r"825(?:\.56)?\s*ms", "Stale candidate mean latency (825/825.56 ms)"),
        (r"\b1472(?:\.12)?\b", "Stale candidate p95 latency (1472/1472.12 ms)"),
        (r"\b4349(?:\.98)?\b", "Stale baseline p95 latency (4349/4349.98 ms)"),
        (r"\b4219(?:\.23)?\b", "Stale baseline p50 latency (4219/4219.23 ms)"),
        (r"\b1331(?:\.90)?\b", "Stale candidate p50 latency (1331/1331.90 ms)"),
        (r"\b3454(?:\.97)?\b", "Stale baseline mean latency (3454/3454.97 ms)"),
        (r"124(?:\.24)?\s*ms", "Stale candidate mean latency (124/124.24 ms)"),
        (r"\b817\.61\b", "Stale candidate p95 latency (817.61 ms)"),
        (r"27\.88\s*ms", "Stale safety margin (27.88 ms)"),
        (r"80\.4\s*%", "Stale reduction percentage (80.4%)"),
        (r"66\.2\s*%", "Stale reduction percentage (66.2%)"),
        (r"68\.4\s*%", "Stale reduction percentage (68.4%)"),
        (r"96\.4\s*%", "Stale reduction percentage (96.4%)"),
        (r"\b3572(?:\.47)?\b", "Stale reference baseline mean latency (3572/3572.47 ms)"),
        (r"\b3678(?:\.92)?\b", "Stale reference baseline p95 latency (3678/3678.92 ms)"),
        (r"\b77\.2\s*%", "Stale reference p50 latency reduction (77.2%)"),
        (r"\b3652(?:\.0)?\b", "Stale reference baseline latency (3652/3652.0 ms)"),
        (r"\b488\.75\b", "Stale reference candidate mean latency (488.75 ms)"),
        (r"\b815\.41\b", "Stale reference candidate p95 latency (815.41 ms)"),
        (r"\b811\.5\b", "Stale reference candidate p50 latency (811.5 ms)"),
        (r"\b3312\.60\b", "Stale reference baseline min latency (3312.60 ms)"),
        (r"\b3718\.82\b", "Stale reference baseline max latency (3718.82 ms)"),
        (r"\b2\.32\s*ms\b", "Stale reference candidate min latency (2.32 ms)"),
        (r"\b26844(?:\.03)?\b", "Stale reference baseline variance (26844.03 ms²)"),
        (r"\b162902(?:\.09)?\b", "Stale reference candidate variance (162902.09 ms²)"),
        (r"163\.84\s*ms", "Stale reference baseline std dev (163.84 ms)"),
        (r"403\.61\s*ms", "Stale reference candidate std dev (403.61 ms)"),
        (r"\b78\.1\s*%", "Stale reference max latency reduction (78.1%)"),
    ]

    # 1. Enforce zero stale figures across all markdown files
    for doc in all_markdown_files:
        if not os.path.exists(doc):
            continue
        with open(doc, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        for pattern, desc in stale_figures:
            if re.search(pattern, content):
                violations.append(f"{doc} - Stale metric detected: {desc}")

    # 1.5 Dynamically collect all valid evidence numbers and verify metric lines
    evidence_nums = {
        0.0, 10.0, 90.0, 100.0, 1500.0, 800.0, 3500.0, 250.0,
        60.0, 80.0, 685.95, 1496.73, 686.68, 1497.65, 5.0, 6.0
    }

    def add_evidence_numbers_from_file(file_path: str):
        if not os.path.exists(file_path):
            return
        import math
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                d = json.load(f)
        except Exception:
            return

        # raw_metrics and reductions (from replay_evaluation)
        for v in d.get("raw_metrics", {}).values():
            if isinstance(v, (int, float)):
                evidence_nums.add(round(float(v), 2))
        for v in d.get("latency_reduction", {}).values():
            if isinstance(v, dict):
                for sub_v in v.values():
                    if isinstance(sub_v, (int, float)):
                        evidence_nums.add(round(float(sub_v), 2))
                        evidence_nums.add(round(float(sub_v), 1))
        for v in d.get("gates", {}).values():
            if isinstance(v, dict):
                for sub_v in v.values():
                    if isinstance(sub_v, (int, float)):
                        evidence_nums.add(round(float(sub_v), 2))

        # latencies from fault runs
        lats = d.get("metrics", {}).get("latencies_ms", [])
        if not lats and "per_request_results" in d:
            lats = [r.get("latency_ms") for r in d["per_request_results"] if isinstance(r.get("latency_ms"), (int, float))]

        if lats:
            evidence_nums.add(round(min(lats), 2))
            evidence_nums.add(round(max(lats), 2))
            mean_v = sum(lats) / len(lats)
            evidence_nums.add(round(mean_v, 2))
            if len(lats) > 1:
                var_v = sum((x - mean_v) ** 2 for x in lats) / (len(lats) - 1)
                evidence_nums.add(round(var_v, 2))
                evidence_nums.add(round(math.sqrt(var_v), 2))
            if len(lats) >= 12:
                p_a = lats[:12]
                evidence_nums.add(round(sum(p_a) / len(p_a), 2))
                evidence_nums.add(round(sorted(p_a)[math.floor(len(p_a) * 0.95)], 2))
            if len(lats) >= 20:
                p_b = lats[12:]
                evidence_nums.add(round(sum(p_b) / len(p_b), 2))
                evidence_nums.add(round(sorted(p_b)[math.floor(len(p_b) * 0.95)], 2))

    for base_dir in ["docs/sample_reports", "reports"]:
        for report_name in ["replay_evaluation.json", "fault_run_baseline.json", "fault_run_hardened.json"]:
            add_evidence_numbers_from_file(os.path.join(base_dir, report_name))

    for doc in all_markdown_files:
        if not os.path.exists(doc):
            continue
        with open(doc, "r", encoding="utf-8", errors="ignore") as f:
            lines = f.readlines()
        for idx, line in enumerate(lines, 1):
            lower_line = line.lower()
            is_metric_line = False
            if line.strip().startswith("|") and any(k in lower_line for k in ["metric", "latency", "p50", "p95", "mean", "variance", "std dev", "breaches", "phase"]):
                is_metric_line = True
            elif any(k in lower_line for k in ["latency reduction", "mean reduction", "p50 reduction", "p95 reduction", "sla budget", "averaging", "p95:", "short-circuit"]):
                is_metric_line = True

            if is_metric_line:
                matches = re.finditer(r"(\b\d{1,3}(?:,\d{3})*(?:\.\d+)?|\b\d+(?:\.\d+)?)\s*(ms²|ms|%)", line)
                for m in matches:
                    val = float(m.group(1).replace(",", ""))
                    if not any(abs(val - ev) <= 0.01 for ev in evidence_nums):
                        violations.append(f"{doc}:{idx} - Quoted metric {m.group(0)} ({val}) has no matching evidence field")

    # 2. Enforce core doc claims on primary architecture/submission docs
    for doc in core_doc_files:
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

        # Verify exact numerical match with replay_evaluation.json when present
        if raw_metrics and doc == "README.md":
            expected_base_mean = str(raw_metrics.get("baseline_avg_ms"))
            expected_hard_mean = str(raw_metrics.get("hardened_avg_ms"))
            expected_hard_p95 = str(raw_metrics.get("hardened_p95_ms"))
            if expected_base_mean and expected_base_mean not in content:
                violations.append(f"{doc} - Baseline mean {expected_base_mean}ms from replay_evaluation.json missing in README")
            if expected_hard_mean and expected_hard_mean not in content:
                violations.append(f"{doc} - Hardened mean {expected_hard_mean}ms from replay_evaluation.json missing in README")
            if expected_hard_p95 and expected_hard_p95 not in content:
                violations.append(f"{doc} - Hardened P95 {expected_hard_p95}ms from replay_evaluation.json missing in README")

        # Check quoted reduction percentages against replay_evaluation.json
        if reductions:
            expected_mean_red = str(reductions.get("mean_basis", {}).get("percent"))
            expected_p95_red = str(reductions.get("p95_basis", {}).get("percent"))
            expected_p50_red = str(reductions.get("p50_basis", {}).get("percent"))

            if expected_mean_red:
                for m in re.finditer(r"(\d+\.\d+)\s*%\s*(?:mean\s+latency\s+reduction|mean\s+reduction)", content, re.IGNORECASE):
                    if m.group(1) != expected_mean_red:
                        violations.append(f"{doc} - Quoted mean latency reduction '{m.group(0)}' does not match replay_evaluation.json ({expected_mean_red}%)")

            if expected_p95_red:
                for m in re.finditer(r"(\d+\.\d+)\s*%\s*(?:p95\s+latency\s+reduction|p95\s+reduction|tail\s+latency\s+reduction)", content, re.IGNORECASE):
                    if m.group(1) != expected_p95_red:
                        violations.append(f"{doc} - Quoted P95 latency reduction '{m.group(0)}' does not match replay_evaluation.json ({expected_p95_red}%)")

            if expected_p50_red:
                for m in re.finditer(r"(\d+\.\d+)\s*%\s*(?:p50\s+latency\s+reduction|p50\s+reduction|median\s+reduction)", content, re.IGNORECASE):
                    if m.group(1) != expected_p50_red:
                        violations.append(f"{doc} - Quoted P50 latency reduction '{m.group(0)}' does not match replay_evaluation.json ({expected_p50_red}%)")

        # For live runtime baseline, verify that real_avg genuinely breached the SLA budget
        if baseline_data:
            metrics = baseline_data.get("metrics", {})
            real_avg = metrics.get("avg_ms")
            if real_avg is not None and real_avg <= expected_budget:
                violations.append(f"Runtime baseline failure not established: avg latency {real_avg}ms <= {expected_budget}ms budget")

    return violations

def audit_cloud_run_claims(readme_path: str = "README.md", reports_dir: str = "reports") -> List[str]:
    violations = []
    if not os.path.exists(readme_path):
        return violations

    with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
        readme_content = f.read()

    sample_dir = os.path.join("docs", "sample_reports")
    rel_path = os.path.join(reports_dir, "release.json")
    if not os.path.exists(rel_path):
        rel_path = os.path.join(sample_dir, "release.json")

    live_path = os.path.join(reports_dir, "live_verification.json")
    if not os.path.exists(live_path):
        live_path = os.path.join(sample_dir, "live_verification.json")

    release_status = None
    if os.path.exists(rel_path):
        try:
            with open(rel_path, "r", encoding="utf-8") as rf:
                release_status = json.load(rf).get("status")
        except Exception:
            pass

    traffic_split_verified = False
    if os.path.exists(live_path):
        try:
            with open(live_path, "r", encoding="utf-8") as lf:
                live_data = json.load(lf)
                traffic_split_verified = bool(live_data.get("traffic_split", {}).get("verified", False))
        except Exception:
            pass

    verified_claim_match = re.search(r"verified.*cloud\s*run", readme_content, re.IGNORECASE)
    is_skipped = (release_status is not None and "SKIPPED" in str(release_status).upper())

    if verified_claim_match:
        if is_skipped or not traffic_split_verified:
            violations.append(
                f"README claims '{verified_claim_match.group(0)}' but Cloud Run deployment is not verified: "
                f"release.json status is '{release_status}' and traffic_split.verified is {traffic_split_verified}."
            )

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
    violations.extend(audit_sample_reports_provenance())
    violations.extend(audit_docs_claims())
    violations.extend(audit_cloud_run_claims())

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

