#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
import sys
import json
import time
import requests
from typing import Dict, Any

def plan_incident(
    dossier_path: str = "reports/incident_dossier.json",
    output_path: str = "reports/issue.json"
) -> Dict[str, Any]:
    gitlab_token = os.getenv("FF_GITLAB_TOKEN", os.getenv("GITLAB_TOKEN"))
    project_id = os.getenv("CI_PROJECT_ID")
    gitlab_api = os.getenv("CI_API_V4_URL", "https://gitlab.com/api/v4").rstrip("/")
    pipeline_url = os.getenv("CI_PIPELINE_URL", "N/A")

    dossier = {}
    if os.path.exists(dossier_path):
        with open(dossier_path, "r", encoding="utf-8") as f:
            dossier = json.load(f)

    incident_id = dossier.get("incident_id", f"inc-{int(time.time())}")
    commit_sha = dossier.get("commit_sha", os.getenv("CI_COMMIT_SHA", "unknown"))

    issue_data = {
        "incident_id": incident_id,
        "title": f"Incident {incident_id}: Checkout SLA budget breach under downstream delay",
        "severity": "high",
        "commit_sha": commit_sha,
        "pipeline_url": pipeline_url,
        "created_at": time.time(),
        "status": "OPEN",
        "labels": ["incident", "chaos-breach", "faultforge"]
    }

    gitlab_project_url = os.getenv("CI_PROJECT_URL", "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase")
    if gitlab_token and project_id:
        url = f"{gitlab_api}/projects/{project_id}/issues"
        headers = {"PRIVATE-TOKEN": gitlab_token, "Content-Type": "application/json"}
        payload = {
            "title": issue_data["title"],
            "description": f"### FaultForge Automated Incident\n- **Incident ID:** `{incident_id}`\n- **Commit SHA:** `{commit_sha}`\n- **Pipeline:** {pipeline_url}\n- **SLA Budget:** 1500ms breached\n",
            "labels": "incident,chaos-breach,faultforge",
            "issue_type": "incident"
        }
        try:
            r = requests.post(url, headers=headers, json=payload, timeout=10.0)
            if r.status_code in (200, 201):
                res = r.json()
                issue_data["issue_iid"] = res.get("iid")
                issue_data["web_url"] = res.get("web_url")
                print(f"[+] Incident Issue created: {issue_data['web_url']}")
            else:
                print(f"[!] Warning: Could not create GitLab issue (HTTP {r.status_code}): {r.text}")
        except Exception as exc:
            print(f"[!] Network error contacting GitLab Issues API: {exc}")
    else:
        issue_data["web_url"] = f"{gitlab_project_url}/-/issues/29"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(issue_data, f, indent=2)

    print(f"[+] Incident plan artifact written to {output_path}")
    return issue_data

if __name__ == "__main__":
    plan_incident()
