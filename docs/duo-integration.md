# GitLab Duo Agent Platform Integration Guide

This guide documents the configuration, trigger options, API integration, and fallback procedures for running the FaultForge custom flow on GitLab.

---

## 1. Flow Registration in GitLab UI

1. In your GitLab project or group, navigate to **Automate** > **Flows**.
2. Click **New flow**.
3. Import the flow YAML specification from [`flows/faultforge-flow.yaml`](../flows/faultforge-flow.yaml).
4. Save the flow with identifier `faultforge_resilience_flow`.
5. Grant the flow permissions to create Merge Requests and read repository files.

---

## 2. Trigger Mechanisms

### Method A: Direct CI / Script Invocation via Flows API (Recommended)
The CI/CD pipeline triggers the custom flow directly using the official GitLab Flows API:
```bash
python scripts/trigger_duo_flow.py
```
- **Requirements:**
  - `FF_GITLAB_TOKEN`: Project Access Token or Personal Access Token with `api` and `read_repository` scopes.
  - `CI_PROJECT_ID`: GitLab project numerical ID.
  - `FF_DUO_FLOW_ID`: Identifier of the registered flow (default: `faultforge_resilience_flow`).

### Method B: Work Item / Issue Assignment Trigger (Fallback)
If direct API access is restricted by tier permissions:
1. The `plan:incident_tracking` CI job generates [`reports/incident_dossier.json`](../reports/incident_dossier.json) and creates an Incident Work Item.
2. In the GitLab Issue, mention the flow bot `@gitlab-duo` or assign the issue to the flow service account.
3. The flow triggers on the `issue_assigned` or `mention` event, ingests the Incident Dossier attached to the issue, and opens the remediation Merge Request.

---

## 3. Strict Authenticity Rule
In accordance with Rule 7 of the FaultForge specification:
- Duo must execute real diagnosis and code synthesis.
- If tokens or credits are exhausted, the script halts with a clear error; it does not fabricate a synthetic MR response.
