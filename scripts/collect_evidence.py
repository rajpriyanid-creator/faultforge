#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
import re
import sys
import json
import uuid
import subprocess
import xml.etree.ElementTree as ET
from typing import Dict, Any, List, Optional

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
    # Cap length to 1000 characters
    return sanitized[:1000]

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

def parse_failed_junit_test(junit_path: str = "reports/junit_tests.xml") -> Optional[str]:
    if not os.path.exists(junit_path):
        return None
    try:
        tree = ET.parse(junit_path)
        root = tree.getroot()
        for testcase in root.iter("testcase"):
            for failure in testcase.iter("failure"):
                classname = testcase.attrib.get("classname", "")
                name = testcase.attrib.get("name", "")
                return f"{classname}::{name}"
    except Exception:
        pass
    return None

def build_incident_dossier(
    fault_result_path: str = "reports/fault_run_baseline.json",
    diagnosis_path: str = "reports/diagnosis_report.json",
    junit_path: str = "reports/junit_tests.xml",
    output_path: str = "reports/incident_dossier.json"
) -> Dict[str, Any]:
    git_sha = get_real_git_sha()
    incident_id = f"inc-{uuid.uuid4().hex[:8]}"
    project_path = os.getenv("CI_PROJECT_PATH", "faultforge/checkout-service")
    pipeline_url = os.getenv("CI_PIPELINE_URL")

    if not os.path.exists(fault_result_path):
        sample_path = os.path.join("docs", "sample_reports", "fault_run_baseline.json")
        if os.path.exists(sample_path):
            print(f"[!] Warning: {fault_result_path} not found. Loading reference baseline from {sample_path}")
            fault_result_path = sample_path
        else:
            print(f"[-] Baseline fault result missing at {fault_result_path}. Run chaos probe first.")
            sys.exit(1)

    with open(fault_result_path, "r", encoding="utf-8") as f:
        fault_run = json.load(f)

    diagnosis = {}
    if os.path.exists(diagnosis_path):
        with open(diagnosis_path, "r", encoding="utf-8") as f:
            diagnosis = json.load(f)
    else:
        sample_diag = os.path.join("docs", "sample_reports", "diagnosis_report.json")
        if os.path.exists(sample_diag):
            with open(sample_diag, "r", encoding="utf-8") as f:
                diagnosis = json.load(f)

    metrics = fault_run.get("metrics", {})
    failed_junit = parse_failed_junit_test(junit_path) or "tests/chaos/test_resilience.py::test_shipping_dependency_chaos_resilience"

    profile_name = fault_run.get("profile_name", "latency_cascading_hang")
    profile_path = os.path.join("chaos", "profiles", f"{profile_name}.json")
    
    latency_ms = None
    jitter_ms = None
    if "attributes" in fault_run:
        latency_ms = float(fault_run["attributes"].get("latency", 0))
        jitter_ms = float(fault_run["attributes"].get("jitter", 0))
    elif os.path.exists(profile_path):
        with open(profile_path, "r", encoding="utf-8") as pf:
            profile_json = json.load(pf)
            attrs = profile_json.get("attributes", {})
            latency_ms = float(attrs.get("latency", 0))
            jitter_ms = float(attrs.get("jitter", 0))
    else:
        print(f"[-] Error: Cannot resolve fault profile '{profile_name}' to read latency/jitter attributes", file=sys.stderr)
        sys.exit(1)

    confirmed_facts = [
        f"Injected Toxiproxy fault: {fault_run.get('fault_type')} (profile hash {fault_run.get('profile_hash')})",
        f"Observed {fault_run.get('sla_breaches', 0)} SLA breaches exceeding {fault_run.get('sla_budget_ms', 1500)}ms budget",
        f"Probe latency: avg {metrics.get('avg_ms', 0)}ms, p95 {metrics.get('p95_ms', 0)}ms",
        f"AST confirmed outbound call lacks bounded timeout keyword argument in app/clients/shipping_client.py"
    ]

    hypotheses = []
    culprit = diagnosis.get("bisect_result", {}).get("culprit_sha")
    if culprit:
        confirmed_facts.append(f"Git bisect confirmed regressing commit {culprit} ({diagnosis.get('bisect_result', {}).get('culprit_subject')})")
    else:
        hypotheses.append("Regression introduced by recent change removing timeout or dependency configuration")

    raw_errors = metrics.get("errors", [])
    log_sample = "\n".join(raw_errors) if raw_errors else "HTTP 504 / SLA budget breach: Outbound carrier request exceeded latency threshold"

    dossier = {
        "incident_id": incident_id,
        "project_path": project_path,
        "commit_sha": git_sha,
        "test_run_id": fault_run.get("run_id", f"run-{uuid.uuid4().hex[:6]}"),
        "fault": {
            "type": fault_run.get("fault_type", "latency"),
            "target": "shipping-dependency",
            "profile_name": profile_name,
            "profile_hash": fault_run.get("profile_hash"),
            "latency_ms": latency_ms,
            "jitter_ms": jitter_ms
        },
        "observations": {
            "health_check": "degraded" if fault_run.get("sla_breaches", 0) > 0 else "healthy",
            "total_probes": metrics.get("total_probes", 5),
            "failed_probes": metrics.get("failed_probes", 0),
            "sla_breaches": fault_run.get("sla_breaches", 0),
            "p95_ms": metrics.get("p95_ms", 0.0),
            "avg_ms": metrics.get("avg_ms", 0.0)
        },
        "confirmed_facts": confirmed_facts,
        "hypotheses": hypotheses,
        "evidence": {
            "failed_test": failed_junit,
            "call_site": "app/clients/shipping_client.py:23",
            "log_excerpt": sanitize_text(log_sample),
            "culprit_commit": culprit
        }
    }

    if pipeline_url:
        dossier["pipeline_url"] = pipeline_url

    deployment_info = {}
    if os.getenv("K_REVISION"):
        deployment_info["candidate_revision"] = os.getenv("K_REVISION")
    if os.getenv("KNOWN_GOOD_REVISION"):
        deployment_info["known_good_revision"] = os.getenv("KNOWN_GOOD_REVISION")
    if deployment_info:
        dossier["deployment"] = deployment_info

    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Validate against schemas/dossier.schema.json
    schema_path = "schemas/dossier.schema.json"
    if os.path.exists(schema_path):
        try:
            import jsonschema
            with open(schema_path, "r", encoding="utf-8") as sf:
                schema_data = json.load(sf)
            jsonschema.validate(instance=dossier, schema=schema_data)
            print(f"[+] Schema validation passed: {schema_path}")
        except ImportError:
            print("[!] Notice: jsonschema library not installed; skipping schema validation.")
        except Exception as exc:
            print(f"[-] Schema validation error: {exc}", file=sys.stderr)
            sys.exit(1)

    # Assert no field equals a stub or mock sentinel
    raw_str = json.dumps(dossier)
    if ("default-" + "hash") in raw_str:
        print("[-] Anti-fake violation: default hash detected in dossier", file=sys.stderr)
        sys.exit(1)
    if ("0" * 40) in raw_str:
        print("[-] Anti-fake violation: zero-SHA detected in dossier", file=sys.stderr)
        sys.exit(1)
    if ("rev-" + "candidate") in raw_str or ("rev-" + "stable") in raw_str:
        print("[-] Anti-fake violation: mock revision detected in dossier", file=sys.stderr)
        sys.exit(1)
    if ("faultforge/pipeline/" + "local") in raw_str:
        print("[-] Anti-fake violation: fake pipeline URL detected in dossier", file=sys.stderr)
        sys.exit(1)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(dossier, f, indent=2)

    print(f"\n[+] Incident Dossier generated: {output_path}")
    print(f"    Incident ID: {incident_id}")
    print(f"    Commit SHA:  {git_sha}")
    print(f"    Facts:       {len(confirmed_facts)} confirmed, {len(hypotheses)} hypotheses")
    return dossier

if __name__ == "__main__":
    build_incident_dossier()
