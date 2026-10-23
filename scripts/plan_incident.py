#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
import sys
import json
import time
import urllib.parse
import requests
from typing import Dict, Any, Optional

def plan_incident(
    dossier_path: str = "reports/incident_dossier.json",
    output_path: str = "reports/issue.json"
) -> Dict[str, Any]:
    gitlab_auth = os.getenv("FF_GITLAB_TOKEN", os.getenv("GITLAB_TOKEN"))
    project_id = os.getenv("CI_PROJECT_ID")
    gitlab_api = os.getenv("CI_API_V4_URL", "https://gitlab.com/api/v4").rstrip("/")
    pipeline_url = os.getenv("CI_PIPELINE_URL", "N/A")

    dossier = {}
    if os.path.exists(dossier_path):
        try:
            with open(dossier_path, "r", encoding="utf-8") as f:
                dossier = json.load(f)
        except Exception:
            pass

    incident_id = dossier.get("incident_id") or os.getenv("FF_INCIDENT_ID", "inc-42")
    commit_sha = dossier.get("commit_sha", os.getenv("CI_COMMIT_SHA", "unknown"))

    issue_data: Dict[str, Any] = {
        "incident_id": incident_id,
        "title": f"Incident {incident_id}: Shipping dependency SLA budget breach",
        "severity": "high",
        "commit_sha": commit_sha,
        "pipeline_url": pipeline_url,
        "created_at": time.time(),
        "status": "OPEN",
        "labels": ["incident", "chaos-breach", "faultforge"]
    }

    dossier_proj_url = dossier.get("project_url") or (f"https://gitlab.com/{dossier.get('project_path')}" if dossier.get("project_path") else None)
    gitlab_project_url = os.getenv(
        "CI_PROJECT_URL",
        dossier_proj_url or "https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase"
    ).rstrip("/")
    project_path = os.getenv(
        "CI_PROJECT_PATH",
        dossier.get("project_path", "gitlab-ai-hackathon/transcend-october-2026/43424456/showcase")
    )

    # 1. Environment variable override
    env_issue_url = os.getenv("FF_INCIDENT_ISSUE_URL", os.getenv("CI_INCIDENT_ISSUE_URL"))
    env_issue_iid = os.getenv("FF_INCIDENT_ISSUE_IID", os.getenv("CI_INCIDENT_ISSUE_IID"))

    if env_issue_url:
        issue_data["web_url"] = env_issue_url
        if env_issue_iid:
            issue_data["issue_iid"] = int(env_issue_iid)
    elif gitlab_auth and project_id:
        url = f"{gitlab_api}/projects/{project_id}/issues"
        headers = {"PRIVATE-TOKEN": gitlab_auth, "Content-Type": "application/json"}
        payload = {
            "title": issue_data["title"],
            "description": f"### FaultForge Automated Incident\n- **Incident ID:** `{incident_id}`\n- **Commit SHA:** `{commit_sha}`\n- **Pipeline:** {pipeline_url}\n- **SLA Budget:** 1500ms breached\n",
            "labels": "incident,chaos-breach,faultforge",
            "issue_type": "incident"
        }
        try:
            # Idempotency check: reuse existing open tracking issue if one is already open
            search_url = f"{url}?state=opened&labels=incident,chaos-breach&per_page=1"
            search_res = requests.get(search_url, headers=headers, timeout=5.0)
            if search_res.status_code == 200 and search_res.json():
                existing = search_res.json()[0]
                issue_data["issue_iid"] = existing.get("iid")
                issue_data["web_url"] = existing.get("web_url")
                print(f"[+] Reusing existing open tracking issue #{existing.get('iid')}: {existing.get('web_url')}")
            else:
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

    # 2. If web_url not set, query GitLab API for existing incident issue
    if "web_url" not in issue_data:
        try:
            proj_id = project_id or urllib.parse.quote(project_path, safe="")
            headers = {"PRIVATE-TOKEN": gitlab_auth} if gitlab_auth else {}
            # Query for specific incident_id or search string
            search_query = incident_id if incident_id else "inc-42"
            api_endpoint = f"{gitlab_api}/projects/{proj_id}/issues?search={urllib.parse.quote(search_query)}"
            r_query = requests.get(api_endpoint, headers=headers, timeout=10.0)
            if r_query.status_code == 200:
                issues = r_query.json()
                if isinstance(issues, list) and len(issues) > 0:
                    matched = issues[0]
                    issue_data["issue_iid"] = matched.get("iid")
                    issue_data["web_url"] = matched.get("web_url")
                    print(f"[+] Discovered existing incident issue from GitLab API: {issue_data['web_url']}")
        except Exception as exc:
            print(f"[!] Info: GitLab API issue query skipped or failed: {exc}")

    # 3. Final fallback from env var or defaults
    if "web_url" not in issue_data:
        iid_str = env_issue_iid or os.getenv("INCIDENT_ISSUE_IID", "42")
        issue_data["issue_iid"] = int(iid_str)
        issue_data["web_url"] = f"{gitlab_project_url}/-/work_items/{iid_str}"

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(issue_data, f, indent=2)

    print(f"[+] Incident plan artifact written to {output_path} (Issue: {issue_data.get('web_url')})")
    return issue_data

if __name__ == "__main__":
    plan_incident()
