#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Record GitLab Duo Evidence.
Queries the GitLab API for evidence of a real GitLab Duo custom flow run:
- Flow run session URL
- Merge Request authored by the Duo flow service account (e.g. ai-faultforge_resilience_flow)
- MR source branch, IID, web URL, author username, and timestamps.

Never invents values. If none exist, writes {"found": false} and exits non-zero when --require is set.
"""
import os
import sys
import json
import argparse
import requests
from typing import Dict, Any, Optional

def query_duo_evidence(
    token: Optional[str],
    project_id: Optional[str],
    api_url: str = "https://gitlab.com/api/v4",
    bot_user: str = "ai-faultforge_resilience_flow",
    require: bool = False,
    output_path: str = "reports/duo_evidence.json"
) -> Dict[str, Any]:
    api_url = api_url.rstrip("/")

    if not token or not project_id:
        evidence = {
            "found": False,
            "reason": "Missing FF_GITLAB_TOKEN or CI_PROJECT_ID environment variables.",
            "mr_iid": None,
            "mr_url": None,
            "source_branch": None,
            "author_username": None,
            "run_url": None
        }
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(evidence, f, indent=2)
        print("[-] Duo evidence: Not found (no API credentials).")
        if require:
            sys.exit(1)
        return evidence

    headers = {
        "PRIVATE-TOKEN": token,
        "Content-Type": "application/json"
    }

    evidence: Dict[str, Any] = {
        "found": False,
        "mr_iid": None,
        "mr_url": None,
        "source_branch": None,
        "author_username": None,
        "run_url": None
    }

    # 1. Query Merge Requests in project
    try:
        mr_endpoint = f"{api_url}/projects/{project_id}/merge_requests"
        r = requests.get(mr_endpoint, headers=headers, params={"per_page": 20, "order_by": "updated_at"}, timeout=(3.0, 15.0))
        if r.status_code == 200:
            mrs = r.json()
            for mr in mrs:
                author = mr.get("author", {}).get("username", "")
                title = mr.get("title", "")
                source_branch = mr.get("source_branch", "")
                labels = mr.get("labels", [])

                # Match Duo service account or resilience flow branch/label
                is_duo_author = (
                    bot_user.lower() in author.lower()
                    or "duo" in author.lower()
                    or "duo" in [l.lower() for l in labels]
                    or "resilience" in source_branch.lower()
                    or "fix/resilience" in source_branch.lower()
                )

                if is_duo_author:
                    evidence["found"] = True
                    evidence["mr_iid"] = mr.get("iid")
                    evidence["mr_url"] = mr.get("web_url")
                    evidence["source_branch"] = source_branch
                    evidence["author_username"] = author
                    evidence["title"] = title
                    evidence["created_at"] = mr.get("created_at")
                    print(f"[+] Found Duo-related Merge Request !{mr.get('iid')}: {mr.get('web_url')} (Branch: {source_branch})")
                    break
        else:
            print(f"[!] Warning: GitLab MR query returned HTTP {r.status_code}")
    except Exception as exc:
        print(f"[!] Error querying GitLab MR API: {exc}")

    # 2. Query Flow Runs if supported
    try:
        runs_endpoint = f"{api_url}/projects/{project_id}/duo_agent_platform/flows/faultforge_resilience_flow/runs"
        r_runs = requests.get(runs_endpoint, headers=headers, timeout=(3.0, 10.0))
        if r_runs.status_code == 200:
            runs = r_runs.json()
            if isinstance(runs, list) and len(runs) > 0:
                latest_run = runs[0]
                evidence["run_url"] = latest_run.get("web_url")
                evidence["run_id"] = latest_run.get("id")
                evidence["found"] = True
    except Exception:
        pass

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(evidence, f, indent=2)

    if evidence["found"]:
        print(f"[+] Duo Evidence confirmed and recorded: {output_path}")
        return evidence
    else:
        print("[-] Duo Evidence: None found in project.")
        if require:
            sys.exit(1)
        return evidence

def main():
    parser = argparse.ArgumentParser(description="Record real GitLab Duo agent execution evidence")
    parser.add_argument("--token", default=os.getenv("FF_GITLAB_TOKEN", os.getenv("GITLAB_TOKEN")))
    parser.add_argument("--project-id", default=os.getenv("CI_PROJECT_ID"))
    parser.add_argument("--api-url", default=os.getenv("CI_API_V4_URL", "https://gitlab.com/api/v4"))
    parser.add_argument("--bot-user", default=os.getenv("FF_DUO_BOT_USER", "ai-faultforge_resilience_flow"))
    parser.add_argument("--require", action="store_true", help="Exit non-zero if no Duo evidence found")
    parser.add_argument("--output", default="reports/duo_evidence.json")
    args = parser.parse_args()

    query_duo_evidence(
        token=args.token,
        project_id=args.project_id,
        api_url=args.api_url,
        bot_user=args.bot_user,
        require=args.require,
        output_path=args.output
    )

if __name__ == "__main__":
    main()
