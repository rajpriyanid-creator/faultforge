#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
from typing import Dict, Any

def trigger_duo_flow(
    dossier_path: str = "reports/incident_dossier.json",
    output_path: str = "reports/duo_run.json"
) -> Dict[str, Any]:
    gitlab_token = os.getenv("FF_GITLAB_TOKEN", os.getenv("GITLAB_TOKEN"))
    project_id = os.getenv("CI_PROJECT_ID")
    gitlab_api = os.getenv("CI_API_V4_URL", "https://gitlab.com/api/v4").rstrip("/")
    flow_id = os.getenv("FF_DUO_FLOW_ID", "faultforge_resilience_flow")

    if not gitlab_token or not project_id:
        print("[-] Error: FF_GITLAB_TOKEN and CI_PROJECT_ID environment variables must be configured.")
        print("    In accordance with Rule 7, Duo integration cannot be faked.")
        print("    Set FF_GITLAB_TOKEN (with api/read_repository scopes) in GitLab CI or environment.")
        sys.exit(1)

    if not os.path.exists(dossier_path):
        print(f"[-] Incident dossier not found at {dossier_path}. Run chaos probe and collect_evidence first.")
        sys.exit(1)

    with open(dossier_path, "r", encoding="utf-8") as f:
        dossier = json.load(f)

    headers = {
        "PRIVATE-TOKEN": gitlab_token,
        "Content-Type": "application/json"
    }
    url = f"{gitlab_api}/projects/{project_id}/duo_agent_platform/flows/{flow_id}/runs"
    payload = {
        "inputs": {
            "incident_id": dossier.get("incident_id"),
            "commit_sha": dossier.get("commit_sha"),
            "fault": dossier.get("fault"),
            "evidence": dossier.get("evidence"),
            "observations": dossier.get("observations")
        }
    }

    print(f"[*] Dispatching execution request to GitLab Duo Agent Platform Flows API...")
    print(f"    Target URL: {url}")
    print(f"    Flow ID:    {flow_id}")

    try:
        r = requests.post(url, headers=headers, json=payload, timeout=15.0)
        if r.status_code not in (200, 201, 202):
            print(f"[-] GitLab Duo Flows API request failed (HTTP {r.status_code}): {r.text}")
            sys.exit(1)

        data = r.json()
        run_record = {
            "run_id": data.get("id", f"duo-run-{int(time.time())}"),
            "flow_id": flow_id,
            "project_id": project_id,
            "status": data.get("status", "RUNNING"),
            "web_url": data.get("web_url", f"https://gitlab.com/projects/{project_id}/flows/{flow_id}"),
            "triggered_at": time.time(),
            "inputs_hash": dossier.get("fault", {}).get("profile_hash")
        }

        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(run_record, f, indent=2)

        print(f"[+] GitLab Duo Custom Flow triggered successfully.")
        print(f"    Run ID:  {run_record['run_id']}")
        print(f"    Web URL: {run_record['web_url']}")
        return run_record

    except Exception as exc:
        print(f"[-] Network error communicating with GitLab Duo Flows API: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    trigger_duo_flow()
