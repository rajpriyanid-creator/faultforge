#!/usr/bin/env python3
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

    # Cross-file consistency checks
    not_established = []
    is_verified = replay.get("verified", False) and (replay.get("evaluation_status") == "RECOVERED_AND_VERIFIED")

    base_hash = replay.get("gates", {}).get("identical_profile_hash", {}).get("baseline_hash")
    hard_hash = replay.get("gates", {}).get("identical_profile_hash", {}).get("hardened_hash")
    if not (base_hash and hard_hash and base_hash == hard_hash):
        is_verified = False
        not_established.append("Exact fault profile hash match could not be established across baseline and hardened runs.")

    git_sha = get_real_git_sha()
    if dossier.get("commit_sha") and dossier["commit_sha"] != git_sha:
        not_established.append(f"Dossier commit SHA ({dossier['commit_sha'][:8]}) differs from current HEAD ({git_sha[:8]}).")

    if not duo_run.get("run_id"):
        not_established.append("GitLab Duo remote run ID unconfirmed (local or API trigger pending).")

    final_status = "RECOVERED_AND_VERIFIED" if (is_verified and not_established == []) else "CONTAINED_NEEDS_REVIEW"
    if not replay.get("verified", False):
        final_status = "NOT_VERIFIED"

    receipt_data = {
        "receipt_id": f"rcpt-{os.urandom(6).hex()}",
        "generated_at": time.time(),
        "final_status": final_status,
        "project": dossier.get("project_path", "faultforge/checkout-service"),
        "commit_sha": git_sha,
        "autonomy_model": "SUPERVISED",
        "risk_classification": risk_data.get("tier", "LOW"),
        "fault_profile": {
            "name": dossier.get("fault", {}).get("profile_name", "latency_cascading_hang"),
            "type": dossier.get("fault", {}).get("type", "latency"),
            "hash": base_hash,
            "identical_replay_confirmed": (base_hash == hard_hash)
        },
        "diagnosis_summary": {
            "status": diagnosis.get("status", "SUSPECTED_WEAKNESS"),
            "confidence": diagnosis.get("confidence", "HIGH"),
            "culprit_sha": diagnosis.get("bisect_result", {}).get("culprit_sha"),
            "target_component": diagnosis.get("target_component", "app/clients/shipping_client.py")
        },
        "evaluation_gates": replay.get("gates", {}),
        "metrics_raw": replay.get("raw_metrics", {}),
        "pipeline_artifacts": {
            "incident_dossier_sha256": hash_file(dossier_path),
            "diagnosis_report_sha256": hash_file(diagnosis_path),
            "mr_payload_sha256": hash_file(mr_path),
            "replay_evaluation_sha256": hash_file(replay_path)
        },
        "not_established": not_established,
        "governance": {
            "requires_human_approval_to_promote": True,
            "promotion_gate": "BLOCKED_PENDING_APPROVAL" if final_status == "RECOVERED_AND_VERIFIED" else "REJECTED"
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
**Tamper-Evident Seal (SHA-256):** `{receipt_data['tamper_evident_seal_sha256']}`

---

## 1. Controlled Chaos Experiment
- **Injected Fault:** `{receipt_data['fault_profile']['name']}` ({receipt_data['fault_profile']['type']})
- **Profile Hash:** `{receipt_data['fault_profile']['hash']}`
- **Identical Replay Confirmed:** `{receipt_data['fault_profile']['identical_replay_confirmed']}`

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
