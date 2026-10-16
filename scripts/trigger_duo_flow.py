#!/usr/bin/env python3
import os
import sys
import json
import time
import requests
from typing import Dict, Any, Optional

def trigger_duo_flow(
    dossier_path: str = "reports/incident_dossier.json",
    output_path: str = "reports/duo_run.json"
) -> Dict[str, Any]:
    gitlab_token = os.getenv("FF_GITLAB_TOKEN", os.getenv("GITLAB_TOKEN"))
    project_id = os.getenv("CI_PROJECT_ID")
    gitlab_api = os.getenv("CI_API_V4_URL", "https://gitlab.com/api/v4").rstrip("/")
    flow_id = os.getenv("FF_DUO_FLOW_ID", "faultforge_resilience_flow")
    bot_username = os.getenv("FF_DUO_BOT_USER", f"ai-{flow_id}")

    if not gitlab_token or not project_id:
        print("[-] Error: FF_GITLAB_TOKEN and CI_PROJECT_ID environment variables must be configured.", file=sys.stderr)
        print("    In accordance with Rule 5 and Rule 7, GitLab Duo flow runs cannot be faked.", file=sys.stderr)
        print("    Set FF_GITLAB_TOKEN (with api/read_repository scopes) and CI_PROJECT_ID.", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(dossier_path):
        print(f"[-] Incident dossier not found at {dossier_path}. Run chaos probe and collect_evidence first.", file=sys.stderr)
        sys.exit(1)

    with open(dossier_path, "r", encoding="utf-8") as f:
        dossier = json.load(f)

    headers = {
        "PRIVATE-TOKEN": gitlab_token,
        "Content-Type": "application/json"
    }

    # Format incident description for goal context
    incident_id = dossier.get("incident_id", "inc-unknown")
    commit_sha = dossier.get("commit_sha", "unknown")
    facts_str = "\n".join([f"- {fact}" for fact in dossier.get("confirmed_facts", [])])
    goal_text = f"""Input: @{bot_username} Please diagnose and repair the dependency fragility identified in incident {incident_id}.
Context: {{Incident ID: {incident_id}, Commit SHA: {commit_sha}}}

### Incident Dossier Summary
{facts_str}

Call Site: {dossier.get('evidence', {}).get('call_site', 'app/clients/shipping_client.py:23')}
Culprit Commit: {dossier.get('evidence', {}).get('culprit_commit', 'Unknown')}
Failing Test: {dossier.get('evidence', {}).get('failed_test', 'tests/chaos/test_resilience.py')}
"""

    run_record: Optional[Dict[str, Any]] = None

    # Method A: Direct REST API trigger if supported on instance
    flow_url = f"{gitlab_api}/projects/{project_id}/duo_agent_platform/flows/{flow_id}/runs"
    payload = {
        "goal": goal_text,
        "inputs": {
            "incident_id": incident_id,
            "commit_sha": commit_sha,
            "fault": dossier.get("fault"),
            "evidence": dossier.get("evidence"),
            "observations": dossier.get("observations")
        }
    }

    print(f"[*] Attempting execution request to GitLab Duo Agent Platform Flows API...")
    print(f"    Target URL: {flow_url}")
    print(f"    Flow ID:    {flow_id}")

    try:
        r = requests.post(flow_url, headers=headers, json=payload, timeout=15.0)
        if r.status_code in (200, 201, 202):
            data = r.json()
            run_record = {
                "run_id": str(data.get("id", f"duo-run-{int(time.time())}")),
                "trigger_mechanism": "REST_API_RUNS",
                "flow_id": flow_id,
                "project_id": project_id,
                "status": data.get("status", "RUNNING"),
                "web_url": data.get("web_url", f"https://gitlab.com/projects/{project_id}/flows/{flow_id}"),
                "triggered_at": time.time(),
                "inputs_hash": dossier.get("fault", {}).get("profile_hash")
            }
            print(f"[+] GitLab Duo Custom Flow triggered via REST API.")
        else:
            print(f"[!] Flows API direct run returned HTTP {r.status_code}. Falling back to Issue Mention/Assignment trigger...")
    except Exception as exc:
        print(f"[!] Direct Flows API connection error: {exc}. Attempting Issue Mention/Assignment trigger...")

    # Method B: Issue Assignment / Mention Trigger (documented mechanism for Agent Platform flows)
    if not run_record:
        issues_url = f"{gitlab_api}/projects/{project_id}/issues"
        issue_payload = {
            "title": f"Incident {incident_id}: Checkout dependency SLA budget breach",
            "description": goal_text,
            "labels": "incident,faultforge,duo-agent"
        }
        try:
            r_issue = requests.post(issues_url, headers=headers, json=issue_payload, timeout=15.0)
            if r_issue.status_code in (200, 201):
                issue_data = r_issue.json()
                issue_iid = issue_data.get("iid")
                issue_url = issue_data.get("web_url")

                # Mention the flow bot in an issue note
                note_url = f"{issues_url}/{issue_iid}/notes"
                note_payload = {
                    "body": f"@{bot_username} Run resilience flow `{flow_id}` to synthesize fix MR."
                }
                requests.post(note_url, headers=headers, json=note_payload, timeout=10.0)

                run_record = {
                    "run_id": f"issue-{issue_iid}-{int(time.time())}",
                    "trigger_mechanism": "ISSUE_MENTION_TRIGGER",
                    "flow_id": flow_id,
                    "project_id": project_id,
                    "issue_iid": issue_iid,
                    "status": "DISPATCHED_TO_AGENT",
                    "web_url": issue_url,
                    "triggered_at": time.time(),
                    "inputs_hash": dossier.get("fault", {}).get("profile_hash")
                }
                print(f"[+] GitLab Duo Agent triggered via Issue #{issue_iid}: {issue_url}")
            else:
                print(f"[-] Issue creation trigger failed (HTTP {r_issue.status_code}): {r_issue.text}", file=sys.stderr)
                sys.exit(1)
        except Exception as exc:
            print(f"[-] Network error communicating with GitLab Issues API: {exc}", file=sys.stderr)
            sys.exit(1)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(run_record, f, indent=2)

    print(f"[+] Duo execution record saved: {output_path}")
    print(f"    Run ID:     {run_record['run_id']}")
    print(f"    Mechanism:  {run_record['trigger_mechanism']}")
    print(f"    Web URL:    {run_record['web_url']}")
    return run_record

if __name__ == "__main__":
    trigger_duo_flow()
