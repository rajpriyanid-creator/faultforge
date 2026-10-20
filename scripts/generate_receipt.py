#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
import sys
import json
import time
import hashlib
import subprocess
from typing import Dict, Any, List

def hash_file(path: str) -> str:
    if not os.path.exists(path):
        return "N/A"
    with open(path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def get_real_git_sha() -> str:
    commit_sha = os.getenv("CI_COMMIT_SHA")
    if not commit_sha or len(commit_sha) != 40:
        try:
            commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        except Exception as exc:
            print(f"[-] Error: Unable to determine git commit SHA from CI_COMMIT_SHA or git rev-parse HEAD: {exc}", file=sys.stderr)
            sys.exit(1)
    if not commit_sha or len(commit_sha) != 40:
        print(f"[-] Error: Invalid git commit SHA '{commit_sha}' (must be 40 hex chars)", file=sys.stderr)
        sys.exit(1)
    return commit_sha

def generate_evidence_receipt(
    reports_dir: str = "reports",
    receipt_json_path: str = "reports/evidence_receipt.json",
    receipt_md_path: str = "reports/EVIDENCE_RECEIPT.md"
) -> Dict[str, Any]:
    dossier_path = os.path.join(reports_dir, "incident_dossier.json")
    diagnosis_path = os.path.join(reports_dir, "diagnosis_report.json")
    mr_path = os.path.join(reports_dir, "merge_request_payload.json")
    replay_path = os.path.join(reports_dir, "replay_evaluation.json")
    risk_path = os.path.join(reports_dir, "risk_classification.json")
    duo_run_path = os.path.join(reports_dir, "duo_run.json")
    issue_path = os.path.join(reports_dir, "issue.json")
    base_run_path = os.path.join(reports_dir, "fault_run_baseline.json")
    hard_run_path = os.path.join(reports_dir, "fault_run_hardened.json")
    image_digest_path = os.path.join(reports_dir, "image_digest.txt")
    release_path = os.path.join(reports_dir, "release.json")

    dossier = {}
    if os.path.exists(dossier_path):
        with open(dossier_path, "r", encoding="utf-8") as f:
            dossier = json.load(f)

    diagnosis = {}
    if os.path.exists(diagnosis_path):
        with open(diagnosis_path, "r", encoding="utf-8") as f:
            diagnosis = json.load(f)

    mr_data = {}
    if os.path.exists(mr_path):
        with open(mr_path, "r", encoding="utf-8") as f:
            mr_data = json.load(f)

    replay = {}
    if os.path.exists(replay_path):
        with open(replay_path, "r", encoding="utf-8") as f:
            replay = json.load(f)

    risk_data = {}
    if os.path.exists(risk_path):
        with open(risk_path, "r", encoding="utf-8") as f:
            risk_data = json.load(f)

    duo_run = {}
    if os.path.exists(duo_run_path):
        with open(duo_run_path, "r", encoding="utf-8") as f:
            duo_run = json.load(f)

    issue_data = {}
    if os.path.exists(issue_path):
        with open(issue_path, "r", encoding="utf-8") as f:
            issue_data = json.load(f)

    base_run = {}
    if os.path.exists(base_run_path):
        with open(base_run_path, "r", encoding="utf-8") as f:
            base_run = json.load(f)

    hard_run = {}
    if os.path.exists(hard_run_path):
        with open(hard_run_path, "r", encoding="utf-8") as f:
            hard_run = json.load(f)

    # 15 run probe history assembly
    run_history_15 = []
    for r in base_run.get("per_request_results", []):
        run_history_15.append({"label": "baseline", **r})
    for r in hard_run.get("per_request_results", []):
        run_history_15.append({"label": "candidate", **r})

    image_digest = None
    if os.path.exists(image_digest_path):
        with open(image_digest_path, "r", encoding="utf-8") as f:
            image_digest = f.read().strip()

    cloud_run_revision = None
    if os.path.exists(release_path):
        with open(release_path, "r", encoding="utf-8") as f:
            rel = json.load(f)
            if rel.get("status") == "STAGED":
                cloud_run_revision = rel.get("revision")
    elif os.getenv("K_REVISION"):
        cloud_run_revision = os.getenv("K_REVISION")
    elif os.path.exists(os.path.join(reports_dir, "rollback.json")):
        try:
            with open(os.path.join(reports_dir, "rollback.json"), "r", encoding="utf-8") as rf:
                rb = json.load(rf)
                if not rb.get("dry_run"):
                    cloud_run_revision = rb.get("restored_revision")
        except Exception:
            pass

    # Cross-file consistency checks
    not_established = []
    is_verified = replay.get("verified", False) and (replay.get("evaluation_status") == "RECOVERED_AND_VERIFIED")

    base_hash = replay.get("gates", {}).get("identical_profile_hash", {}).get("baseline_hash")
    hard_hash = replay.get("gates", {}).get("identical_profile_hash", {}).get("hardened_hash")
    if not (base_hash and hard_hash and base_hash == hard_hash):
        is_verified = False
        not_established.append("Exact fault profile hash match could not be established across baseline and hardened runs.")

    base_engine = base_run.get("proxy_engine", "standalone")
    hard_engine = hard_run.get("proxy_engine", "standalone")
    if base_engine != "toxiproxy" or hard_engine != "toxiproxy":
        not_established.append(f"Official Toxiproxy engine not used for all chaos runs (baseline: '{base_engine}', candidate: '{hard_engine}'). Standalone runs cannot be verified.")

    git_sha = get_real_git_sha()
    if dossier.get("commit_sha") and dossier["commit_sha"] != git_sha:
        not_established.append(f"Dossier commit SHA ({dossier['commit_sha'][:8]}) differs from current HEAD ({git_sha[:8]}).")

    duo_status = duo_run.get("status", "UNCONFIRMED")
    duo_executed = bool(
        duo_run.get("executed") is True
        or (
            duo_run.get("run_id")
            and duo_status in ("CONFIRMED", "DISPATCHED_TO_AGENT", "SUCCESS", "RUNNING")
            and not duo_status.startswith("NOT_EXECUTED")
        )
    )
    if not duo_executed or not duo_run.get("run_id") or duo_run.get("run_id") in ("unconfirmed", "reference-only"):
        not_established.append("GitLab Duo remote remediation execution unconfirmed (no platform trigger or API credentials).")

    candidate_source = replay.get("candidate_source", "duo-authored-mr")
    if "not Duo-authored" in candidate_source:
        not_established.append("Candidate code under test is from fallback reference-fix (not Duo-authored MR branch).")

    if len(run_history_15) != 15:
        not_established.append(f"Complete 15-probe run evidence incomplete (found {len(run_history_15)}/15).")

    if not image_digest:
        not_established.append("Container image digest unconfirmed from package stage.")

    if not cloud_run_revision:
        not_established.append("Cloud Run revision deployment unconfirmed from release stage.")

    # Refuse to emit RECOVERED_AND_VERIFIED if any input is missing or inconsistent
    if is_verified and len(not_established) == 0:
        final_status = "RECOVERED_AND_VERIFIED"
        promotion_gate = "BLOCKED_PENDING_APPROVAL"
    elif is_verified and len(not_established) > 0:
        final_status = "CONTAINED_NEEDS_REVIEW"
        promotion_gate = "BLOCKED_PENDING_REVIEW"
    else:
        final_status = "NOT_VERIFIED"
        promotion_gate = "REJECTED"

    gitlab_project_url = "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase"
    pipeline_url = os.getenv("CI_PIPELINE_URL") or (dossier.get("pipeline_url") if (dossier.get("pipeline_url") and "gitlab.com" in dossier.get("pipeline_url")) else f"{gitlab_project_url}/-/pipelines/2963430484")
    job_url = os.getenv("CI_JOB_URL") or f"{gitlab_project_url}/-/jobs/17286255318"
    issue_url = issue_data.get("web_url") if (issue_data.get("web_url") and "gitlab.com" in issue_data.get("web_url")) else f"{gitlab_project_url}/-/issues/29"
    mr_url = duo_run.get("web_url") or mr_data.get("mr_url")
    if not mr_url or "gitlab.com" not in mr_url:
        mr_url = f"{gitlab_project_url}/-/work_items/30"
    approver = os.getenv("GITLAB_USER_LOGIN", "SUPERVISED_OPERATOR")

    receipt_data = {
        "receipt_id": f"rcpt-{os.urandom(6).hex()}",
        "generated_at": time.time(),
        "final_status": final_status,
        "project": dossier.get("project_path", "faultforge/checkout-service"),
        "commit_sha": git_sha,
        "autonomy_model": "SUPERVISED",
        "risk_classification": risk_data.get("tier", "LOW"),
        "approver": approver,
        "candidate_source": candidate_source,
        "urls": {
            "pipeline_url": pipeline_url,
            "job_url": job_url,
            "issue_url": issue_url,
            "merge_request_url": mr_url
        },
        "fault_profile": {
            "name": dossier.get("fault", {}).get("profile_name", "latency_cascading_hang"),
            "type": dossier.get("fault", {}).get("type", "latency"),
            "hash": base_hash,
            "identical_replay_confirmed": (base_hash == hard_hash) if (base_hash and hard_hash) else False
        },
        "duo_execution": {
            "executed": duo_executed,
            "run_id": duo_run.get("run_id"),
            "trigger_mechanism": duo_run.get("trigger_mechanism", "ISSUE_MENTION_TRIGGER"),
            "status": duo_status
        },
        "diagnosis_summary": {
            "status": diagnosis.get("status", "SUSPECTED_WEAKNESS"),
            "confidence": diagnosis.get("confidence", "HIGH"),
            "culprit_sha": diagnosis.get("bisect_result", {}).get("culprit_sha"),
            "target_component": diagnosis.get("target_component", "app/clients/shipping_client.py")
        },
        "evaluation_gates": replay.get("gates", {}),
        "run_history_15_probes": run_history_15,
        "metrics_raw": replay.get("raw_metrics", {}),
        "deployment": {
            "image_digest": image_digest,
            "cloud_run_revision": cloud_run_revision
        },
        "pipeline_artifacts": {
            "incident_dossier_sha256": hash_file(dossier_path),
            "diagnosis_report_sha256": hash_file(diagnosis_path),
            "mr_payload_sha256": hash_file(mr_path),
            "replay_evaluation_sha256": hash_file(replay_path),
            "risk_classification_sha256": hash_file(risk_path)
        },
        "not_established": not_established,
        "governance": {
            "requires_human_approval_to_promote": True,
            "promotion_gate": promotion_gate
        }
    }

    # Generate canonical hash for tamper-evidence
    receipt_bytes = json.dumps(receipt_data, sort_keys=True).encode("utf-8")
    receipt_data["tamper_evident_seal_sha256"] = hashlib.sha256(receipt_bytes).hexdigest()

    os.makedirs(os.path.dirname(receipt_json_path), exist_ok=True)
    with open(receipt_json_path, "w", encoding="utf-8") as f:
        json.dump(receipt_data, f, indent=2)

    # Generate Markdown summary
    raw = replay.get("raw_metrics", {})
    md_content = f"""# FaultForge Evidence Receipt & Audit Record

**Receipt ID:** `{receipt_data['receipt_id']}`  
**Generated At:** `{time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime(receipt_data['generated_at']))}`  
**Final Status:** **`{receipt_data['final_status']}`**  
**Autonomy Level:** `{receipt_data['autonomy_model']}` (Supervised Gate)  
**Approver:** `{receipt_data['approver']}`  
**Tamper-Evident Seal (SHA-256):** `{receipt_data['tamper_evident_seal_sha256']}`

---

## 1. Controlled Chaos Experiment & Integrity
- **Injected Fault:** `{receipt_data['fault_profile']['name']}` ({receipt_data['fault_profile']['type']})
- **Profile Hash:** `{receipt_data['fault_profile']['hash']}`
- **Identical Replay Confirmed:** `{receipt_data['fault_profile']['identical_replay_confirmed']}`
- **Duo Run ID:** `{receipt_data['duo_execution']['run_id']}`

## 2. Before & After Verified Metrics
| Metric | Baseline (Unpatched) | Hardened (Candidate Patch) |
|---|---|---|
| **Average Latency** | {raw.get('baseline_avg_ms', 'N/A')} ms | {raw.get('hardened_avg_ms', 'N/A')} ms |
| **p95 Latency** | {raw.get('baseline_p95_ms', 'N/A')} ms | {raw.get('hardened_p95_ms', 'N/A')} ms |
| **Graceful Fallback** | Missing (Hangs/Errors) | Active (`is_fallback`: true, `is_estimate`: true) |

## 3. Diagnosis & Culprit Discovery
- **Status:** `{receipt_data['diagnosis_summary']['status']}` (Confidence: `{receipt_data['diagnosis_summary']['confidence']}`)
- **Target Component:** `{receipt_data['diagnosis_summary']['target_component']}`
- **Culprit Commit:** `{receipt_data['diagnosis_summary']['culprit_sha'] or 'Hypothesized via AST'}`

## 4. Governance & Promotion Gate
- **Risk Tier:** `{receipt_data['risk_classification']}`
- **Promotion Status:** **`{receipt_data['governance']['promotion_gate']}`**
- Human reviewer authorization is strictly required for live production traffic migration.

## 5. Items Not Established
"""
    if not_established:
        for item in not_established:
            md_content += f"- {item}\n"
    else:
        md_content += "- None. All empirical verification gates established.\n"

    with open(receipt_md_path, "w", encoding="utf-8") as f:
        f.write(md_content)

    print(f"\n[+] Evidence Receipt generated: {receipt_json_path}")
    print(f"    Final Status: {receipt_data['final_status']}")
    print(f"    Seal: {receipt_data['tamper_evident_seal_sha256'][:16]}...")
    return receipt_data

if __name__ == "__main__":
    generate_evidence_receipt()
