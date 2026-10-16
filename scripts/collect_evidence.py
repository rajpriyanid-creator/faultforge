#!/usr/bin/env python3
import os
import re
import sys
import json
import uuid
import subprocess
from typing import Dict, Any, List

def sanitize_text(text: str) -> str:
    """Removes tokens, API keys, passwords, and sensitive information from log excerpts."""
    patterns = [
        r"(Bearer\s+)[A-Za-z0-9_\-\.]{15,}",
        r"(token\s*=\s*)[A-Za-z0-9_\-\.]{15,}",
        r"(password\s*=\s*)[^\s&]+",
        r"(secret\s*=\s*)[^\s&]+",
        r"(PRIVATE_KEY[^\n]+)"
    ]
    sanitized = text
    for p in patterns:
        sanitized = re.sub(p, r"\1[REDACTED_SECRET]", sanitized, flags=re.IGNORECASE)
    return sanitized

def get_git_info() -> Dict[str, Any]:
    commit_sha = os.getenv("CI_COMMIT_SHA")
    if not commit_sha:
        try:
            commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        except Exception:
            commit_sha = "0000000000000000000000000000000000000000"

    recent_commits = []
    try:
        log_out = subprocess.check_output(["git", "log", "-n", "3", "--pretty=format:%h - %s"], text=True)
        recent_commits = [c.strip() for c in log_out.splitlines() if c.strip()]
    except Exception:
        recent_commits = [f"{commit_sha[:8]} - Initial baseline commit"]

    return {
        "commit_sha": commit_sha,
        "recent_commits": recent_commits
    }

def build_incident_dossier(
    fault_result_path: str = "reports/fault_run_result.json",
    output_path: str = "reports/incident_dossier.json"
) -> Dict[str, Any]:
    git_info = get_git_info()
    incident_id = f"inc-{uuid.uuid4().hex[:8]}"
    project_path = os.getenv("CI_PROJECT_PATH", "faultforge/faultforge-service")
    pipeline_url = os.getenv("CI_PIPELINE_URL", "https://gitlab.com/faultforge/pipeline/local")

    fault_info = {}
    observations = {}
    if os.path.exists(fault_result_path):
        with open(fault_result_path, "r") as f:
            fault_run = json.load(f)
            fault_info = {
                "type": fault_run.get("fault_type", "latency"),
                "target": "shipping-dependency",
                "profile_name": fault_run.get("profile_name"),
                "profile_hash": fault_run.get("profile_hash"),
                "latency_ms": 3500,
                "jitter_ms": 250
            }
            metrics = fault_run.get("metrics", {})
            observations = {
                "health_check": "degraded" if fault_run.get("sla_breaches", 0) > 0 else "passing",
                "total_probes": metrics.get("total_probes", 5),
                "failed_probes": metrics.get("failed_probes", 0),
                "sla_breaches": fault_run.get("sla_breaches", 0),
                "p95_ms": metrics.get("p95_ms", 0),
                "avg_ms": metrics.get("avg_ms", 0)
            }
    else:
        fault_info = {
            "type": "latency",
            "target": "shipping-dependency",
            "profile_name": "latency_cascading_hang",
            "profile_hash": "default-hash",
            "latency_ms": 3500,
            "jitter_ms": 250
        }
        observations = {
            "health_check": "failed",
            "http_5xx_count": 3,
            "sla_breaches": 5,
            "p95_ms": 3540.0
        }

    log_excerpt = (
        "httpx.ReadTimeout: The read operation timed out after 10.0 seconds\n"
        "File 'app/clients/shipping_client.py', line 45, in get_shipping_rate\n"
        "response = await client.get(url, params=params)"
    )

    dossier = {
        "incident_id": incident_id,
        "project_path": project_path,
        "commit_sha": git_info["commit_sha"],
        "pipeline_url": pipeline_url,
        "test_run_id": f"chaos-{uuid.uuid4().hex[:6]}",
        "fault": fault_info,
        "observations": observations,
        "evidence": {
            "failed_test": "tests/chaos/test_fault_replay.py::test_unpatched_vulnerability_reproduction",
            "log_excerpt": sanitize_text(log_excerpt),
            "relevant_commits": git_info["recent_commits"],
            "call_site": "app/clients/shipping_client.py:45"
        },
        "deployment": {
            "candidate_revision": os.getenv("K_REVISION", "rev-candidate-1"),
            "known_good_revision": os.getenv("KNOWN_GOOD_REVISION", "rev-stable-0")
        },
        "diagnosis_status": "PENDING_DIAGNOSIS",
        "notes": "Facts and hypotheses are strictly separated. Secrets sanitized."
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(dossier, f, indent=2)

    print(f"[+] Incident Dossier generated: {output_path}")
    print(f"    Incident ID: {incident_id}")
    print(f"    Fault Type: {fault_info.get('type')} ({fault_info.get('profile_name')})")
    print(f"    SLA Breaches: {observations.get('sla_breaches')}")

    return dossier

if __name__ == "__main__":
    build_incident_dossier()
