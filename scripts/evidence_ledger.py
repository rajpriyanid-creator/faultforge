#!/usr/bin/env python3
"""
FaultForge Evidence Ledger Manager
Maintains an append-only, machine-readable JSON ledger of all 9 lifecycle stages.
"""
import os
import sys
import json
import time
import argparse
from typing import Dict, Any, List

LEDGER_PATH = "reports/stage_ledger.json"

def load_ledger() -> Dict[str, Any]:
    ledger = {
        "project": "faultforge/checkout-service",
        "ledger_version": "1.0.0",
        "last_updated": time.time(),
        "stages": {}
    }
    if os.path.exists(LEDGER_PATH):
        try:
            with open(LEDGER_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    ledger["project"] = data.get("project", ledger["project"])
                    ledger["stages"] = data.get("stages", {})
        except Exception:
            pass

    # Merge any individual stage ledger files present in reports/
    reports_dir = os.path.dirname(LEDGER_PATH) or "."
    if os.path.exists(reports_dir):
        for fname in os.listdir(reports_dir):
            if fname.startswith("stage_ledger_") and fname.endswith(".json") and fname != "stage_ledger.json":
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
    notes: str = ""
) -> Dict[str, Any]:
    ledger = load_ledger()
    commit_sha = os.getenv("CI_COMMIT_SHA", os.getenv("GIT_COMMIT", "local-dev"))
    pipeline_id = os.getenv("CI_PIPELINE_ID", "local-run")

    existing_artifacts = [a for a in artifacts if os.path.exists(a)]

    stage_entry = {
        "stage": stage,
        "job_name": job,
        "status": status,
        "commit_sha": commit_sha,
        "pipeline_id": pipeline_id,
        "approval_required": approval_required,
        "artifacts_declared": artifacts,
        "artifacts_verified_on_disk": existing_artifacts,
        "timestamp": time.time(),
        "notes": notes
    }

    ledger["stages"][stage] = stage_entry
    ledger["last_updated"] = time.time()

    os.makedirs(os.path.dirname(LEDGER_PATH), exist_ok=True)
    # 1. Save individual stage record for non-conflicting multi-runner artifact aggregation
    stage_file = os.path.join(os.path.dirname(LEDGER_PATH), f"stage_ledger_{stage}.json")
    with open(stage_file, "w", encoding="utf-8") as f:
        json.dump(stage_entry, f, indent=2)

    # 2. Save aggregated ledger
    with open(LEDGER_PATH, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2)

    print(f"[+] Evidence Ledger updated for stage '{stage}': {status}")
    return stage_entry

def print_ledger_summary():
    ledger = load_ledger()
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
        print(f"{stg:<12} {data.get('job_name', '-'):<32} {data.get('status', '-'):<10} {art_count} files verified")
    print("=================================================================\n")

def main():
    parser = argparse.ArgumentParser(description="FaultForge Stage Evidence Ledger")
    parser.add_argument("--stage", help="Stage name (e.g. plan, create, verify, etc.)")
    parser.add_argument("--job", help="CI Job name")
    parser.add_argument("--status", default="SUCCESS", help="Execution status")
    parser.add_argument("--artifacts", nargs="*", default=[], help="Paths to generated artifacts")
    parser.add_argument("--approval-required", action="store_true", help="Flag if stage requires human approval")
    parser.add_argument("--notes", default="", help="Additional diagnostic notes")
    parser.add_argument("--summary", action="store_true", help="Print ledger summary")
    args = parser.parse_args()

    if args.summary or not args.stage:
        print_ledger_summary()
        return

    record_stage(
        stage=args.stage,
        job=args.job or f"{args.stage}:job",
        status=args.status,
        artifacts=args.artifacts,
        approval_required=args.approval_required,
        notes=args.notes
    )

if __name__ == "__main__":
    main()
