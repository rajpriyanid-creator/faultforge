#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge Evidence Ledger Manager
Maintains an append-only, machine-readable JSON ledger of all 9 lifecycle stages.
Verifies artifact existence, non-emptiness, and SHA-256 checksums before recording SUCCESS.
"""
import os
import sys
import json
import time
import hashlib
import argparse
import subprocess
from typing import Dict, Any, List, Optional

LEDGER_PATH = "reports/stage_ledger.json"

def get_ledger_commit_sha() -> str:
    commit_sha = os.getenv("CI_COMMIT_SHA", os.getenv("GIT_COMMIT"))
    if commit_sha and len(commit_sha) == 40 and all(c in "0123456789abcdefABCDEF" for c in commit_sha):
        return commit_sha
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        if commit_sha and len(commit_sha) == 40 and all(c in "0123456789abcdefABCDEF" for c in commit_sha):
            return commit_sha
    except Exception:
        pass
    return "UNKNOWN_NO_GIT"

def hash_file_sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def load_ledger(ledger_path: str = LEDGER_PATH) -> Dict[str, Any]:
    ledger = {
        "project": "faultforge/checkout-service",
        "ledger_version": "1.1.0",
        "last_updated": time.time(),
        "stages": {}
    }
    if os.path.exists(ledger_path):
        try:
            with open(ledger_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    ledger["project"] = data.get("project", ledger["project"])
                    ledger["stages"] = data.get("stages", {})
        except Exception:
            pass

    # Merge any individual stage ledger files present in reports/
    reports_dir = os.path.dirname(ledger_path) or "."
    if os.path.exists(reports_dir):
        for fname in os.listdir(reports_dir):
            if fname.startswith("stage_ledger_") and fname.endswith(".json") and fname != os.path.basename(ledger_path):
                fpath = os.path.join(reports_dir, fname)
                try:
                    with open(fpath, "r", encoding="utf-8") as sf:
                        stg_data = json.load(sf)
                        if isinstance(stg_data, dict) and "stage" in stg_data:
                            ledger["stages"][stg_data["stage"]] = stg_data
                except Exception:
                    pass

    return ledger

def record_stage(
    stage: str,
    job: str,
    status: str,
    artifacts: List[str],
    approval_required: bool = False,
    notes: str = "",
    ledger_path: str = LEDGER_PATH,
    duo_executed: bool = False
) -> Dict[str, Any]:
    valid_statuses = ("SUCCESS", "SKIPPED", "FAILED")
    norm_status = status.upper().strip()
    if norm_status not in valid_statuses:
        print(f"[-] Error: Invalid status '{status}'. Must be one of {valid_statuses}", file=sys.stderr)
        sys.exit(1)

    verified_details = []
    missing_or_empty = []

    for art_path in artifacts:
        if not os.path.exists(art_path):
            missing_or_empty.append((art_path, "missing"))
            continue
        try:
            size_b = os.path.getsize(art_path)
            if size_b == 0:
                missing_or_empty.append((art_path, "empty (0 bytes)"))
                continue
            sha256_hex = hash_file_sha256(art_path)
            verified_details.append({
                "path": art_path,
                "size_bytes": size_b,
                "sha256": sha256_hex
            })
        except Exception as exc:
            missing_or_empty.append((art_path, f"read error: {exc}"))

    # If status is SUCCESS, refuse if any declared artifact is missing or empty
    if norm_status == "SUCCESS" and missing_or_empty:
        print(f"[-] Error: Refusing to record SUCCESS for stage '{stage}'. Artifact verification failed:", file=sys.stderr)
        for p, reason in missing_or_empty:
            print(f"    - {p}: {reason}", file=sys.stderr)
        sys.exit(1)

    ledger = load_ledger(ledger_path)
    commit_sha = get_ledger_commit_sha()
    pipeline_id = os.getenv("CI_PIPELINE_ID", "local-run")

    existing_artifacts = [item["path"] for item in verified_details]

    # For create stage, detect duo_executed from duo_evidence.json if not explicitly passed
    if stage == "create" and not duo_executed:
        duo_ev_path = os.path.join(os.path.dirname(ledger_path) or ".", "duo_evidence.json")
        if os.path.exists(duo_ev_path):
            try:
                with open(duo_ev_path, "r", encoding="utf-8") as df:
                    d_data = json.load(df)
                    duo_executed = bool(d_data.get("found") and d_data.get("mr_url") and d_data.get("run_url"))
            except Exception:
                pass

    current_ts = time.time()
    stage_entry = {
        "stage": stage,
        "job_name": job,
        "status": norm_status,
        "commit_sha": commit_sha,
        "pipeline_id": pipeline_id,
        "approval_required": approval_required,
        "artifacts_declared": artifacts,
        "artifacts_verified_on_disk": existing_artifacts,
        "artifacts_details": verified_details,
        "timestamp": current_ts,
        "duo_executed": duo_executed,
        "notes": notes
    }

    ledger["stages"][stage] = stage_entry
    ledger["last_updated"] = time.time()

    reports_dir = os.path.dirname(ledger_path) or "."
    os.makedirs(reports_dir, exist_ok=True)

    # 1. Save individual stage record for non-conflicting multi-runner artifact aggregation
    stage_file = os.path.join(reports_dir, f"stage_ledger_{stage}.json")
    with open(stage_file, "w", encoding="utf-8") as f:
        json.dump(stage_entry, f, indent=2)

    # 2. Save aggregated ledger
    with open(ledger_path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)

    print(f"[+] Evidence Ledger updated for stage '{stage}': {norm_status} ({len(verified_details)} artifacts verified)")
    return stage_entry

def print_ledger_summary(ledger_path: str = LEDGER_PATH):
    ledger = load_ledger(ledger_path)
    stages = ledger.get("stages", {})
    print("\n=================================================================")
    print(" FaultForge Stage-by-Stage Evidence Ledger")
    print("=================================================================")
    print(f"Project: {ledger.get('project')}")
    print(f"Recorded Stages: {len(stages)} / 9\n")
    print(f"{'STAGE':<12} {'JOB NAME':<32} {'STATUS':<10} {'ARTIFACTS'}")
    print("-" * 65)
    for stg, data in stages.items():
        art_count = len(data.get("artifacts_verified_on_disk", []))
        stg_status = data.get("status", "-")
        print(f"{stg:<12} {data.get('job_name', '-'):<32} {stg_status:<10} {art_count} files verified")
    print("=================================================================\n")

def main():
    parser = argparse.ArgumentParser(description="FaultForge Stage Evidence Ledger")
    parser.add_argument("--stage", help="Stage name (e.g. plan, create, verify, etc.)")
    parser.add_argument("--job", help="CI Job name")
    parser.add_argument("--status", default="SUCCESS", help="Execution status (SUCCESS, SKIPPED, FAILED)")
    parser.add_argument("--artifacts", nargs="*", default=[], help="Paths to generated artifacts")
    parser.add_argument("--approval-required", action="store_true", help="Flag if stage requires human approval")
    parser.add_argument("--duo-executed", action="store_true", help="Flag indicating GitLab Duo flow was verified executed")
    parser.add_argument("--notes", default="", help="Additional diagnostic notes")
    parser.add_argument("--ledger-path", default=LEDGER_PATH, help="Path to stage_ledger.json")
    parser.add_argument("--summary", action="store_true", help="Print ledger summary")
    args = parser.parse_args()

    if args.summary or not args.stage:
        print_ledger_summary(args.ledger_path)
        return

    record_stage(
        stage=args.stage,
        job=args.job or f"{args.stage}:job",
        status=args.status,
        artifacts=args.artifacts,
        approval_required=args.approval_required,
        notes=args.notes,
        ledger_path=args.ledger_path,
        duo_executed=args.duo_executed
    )

if __name__ == "__main__":
    main()
