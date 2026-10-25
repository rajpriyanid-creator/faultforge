# GitLab Duo Agent Platform Integration Guide

This guide documents the configuration, schema compliance, trigger options, API integration, and fallback procedures for running the FaultForge custom flow on GitLab.

---

## 1. Flow Registration in GitLab UI (AI Catalog / Flows)

1. In your GitLab project or group, navigate to **Automate** > **Flows** (or **AI Catalog** > **Flows**).
2. Click **New flow**.
3. Import the flow YAML specification from [`flows/faultforge-flow.yaml`](../flows/faultforge-flow.yaml).
4. Save the flow with identifier `faultforge_resilience_flow`.
5. Grant the flow permissions to create Merge Requests, commit code, and read repository files.
6. Note the generated service account username (typically `ai-faultforge_resilience_flow`).

---

## 2. Verified Trigger Mechanisms

### Method A: REST API Runs Trigger (Automated CI Path)
The pipeline dispatches an execution request directly to the GitLab Duo Agent Platform:
```bash
python scripts/trigger_duo_flow.py
```
- **Endpoint:** `POST /api/v4/projects/:id/duo_agent_platform/flows/:flow_id/runs`
- **Required Variables:**
  - `FF_GITLAB_TOKEN`: Project or Personal Access Token with `api` and `write_repository` scopes.
  - `CI_PROJECT_ID`: GitLab project numerical ID.
  - `FF_DUO_FLOW_ID`: Identifier of the registered flow (default: `faultforge_resilience_flow`).
- **Output:** Saves run record with run ID and URL to `reports/duo_run.json`.

### Method B: Issue Assignment / Mention Trigger (Documented Platform Fallback)
If group permissions or tier restrictions disallow direct REST flow execution:
1. `scripts/trigger_duo_flow.py` automatically falls back to creating an **Incident Issue** via GitLab Issues API with the complete Incident Dossier summary.
2. It assigns or mentions the flow service account (`@ai-faultforge_resilience_flow`).
3. GitLab's event router initiates the custom flow on the `mention` or `assignment` trigger.
4. The agent ingests `context:goal` containing the incident context and proceeds with diagnosis and patch creation.

### Method C: Human Interactive Fallback
If API triggers are blocked or credentials expire:
1. View the Incident Issue created by CI (`Incident inc-XXXX: Checkout dependency SLA budget breach`).
2. Add a comment: `@ai-faultforge_resilience_flow Please run resilience flow to fix checkout timeout`.
3. The Duo agent will open the Merge Request targeting `main`.

---

## 3. What Worked, What Didn't, and Platform Constraints

### What Worked:
- **Flow Registry v1 Specification:** `environment: ambient`, `coding_environment: full`, decoupled `prompts:`, modular `AgentComponent` blocks, and explicit `routers:` transitions pass GitLab Duo validation.
- **Dynamic Dossier Ingestion:** The Incident Dossier contains 0 placeholders, providing concrete AST findings, git bisect culprit SHA, and failing test node IDs.
- **Fail-Loud Enforcement:** If `FF_GITLAB_TOKEN` or `CI_PROJECT_ID` is missing, `scripts/trigger_duo_flow.py` immediately exits with code 1 instead of emitting fake run records.

### What Didn't (Platform Constraints Handled):
- **Model In Prompts:** GitLab custom flows reject explicit model identifiers (`model: claude-3-5-sonnet`) inside the flow YAML. Model selection is strictly governed by group/instance configuration.
- **Top-Level Metadata:** GitLab rejects top-level `name` and `description` in the flow YAML. Flow naming is handled when registering the flow in the UI.

---

## 4. Strict Authenticity Rule (Rule 5 & Rule 7)
In accordance with the hackathon rules:
- GitLab Duo must execute real diagnosis and code synthesis.
- Under no circumstances is a synthetic MR payload generated.
- When human assistance is needed, the human runs the flow or assigns the flow bot, linking the real MR.

---

## 5. Future Orbit Enhancement & Fallback Diagnosis Path

### Future Orbit Capabilities
GitLab Orbit is designed for conversational, context-aware autonomous investigations. When available:
1. Orbit agents will subscribe to Toxiproxy chaos webhooks.
2. Orbit will query real-time OpenTelemetry trace spans directly from Cloud Run and local containers.
3. Orbit will correlate degraded dependency health probes with culprit commit regressions autonomously.

### Production-Ready Platform Fallback
Because Orbit is currently behind a feature flag for hackathon namespaces:
1. **Deterministic Bisect Fallback:** `scripts/diagnose_and_bisect.py` performs AST and `git bisect` boundary discovery without external dependencies.
2. **GitLab REST API Fallback:** `scripts/trigger_duo_flow.py` uses verified Issues, Notes, and Merge Request APIs to trigger and link GitLab Duo custom flows.
3. **Evidence Artifact Integration:** Findings are saved into machine-readable JSON files (`reports/incident_dossier.json`, `reports/stage_ledger.json`) rather than ephemeral chat memory.
---

## 6. Code Provenance: What Duo Authored vs. What Was Evaluated

From `git log --all --author=service_account`, six commits were authored by the GitLab Duo service account (`FaultForge, Supervised, Resilience, Healer <service_account_group_121124982_e6349fd5e8ecd6554efb712ed8e2654f@noreply.gitlab.com>`) on branch `fix/resilience-shipping-timeout`:

| Short Commit | Full Commit SHA | Date (UTC) | Subject | GitLab Agent Session / Run |
|---|---|---|---|:---:|
| `f8aa9d9` | `f8aa9d98b8617b51c15b5fa6ceda39eb43762730` | 2026-10-22 17:18:48 | fix(resilience): bound shipping client with 0.8s timeout, circuit breaker and graceful fallback | Session `9909079` |
| `d372014` | `d3720143e15c85f519a7624859541d1ce997f1a0` | 2026-10-23 15:48:38 | fix(resilience): bound shipping call to 0.8s with circuit breaker and fallback estimate | not established |
| `fafadf8` | `fafadf8bdacf311e6ae7e34b6155b76905faa7d4` | 2026-10-23 17:13:14 | fix(resilience): bound shipping client with 0.8s timeout, circuit breaker and graceful fallback | not established |
| `b57584a` | `b57584ae2517633d989506c1898611c9adb84760` | 2026-10-23 17:16:01 | fix(resilience): bound shipping client with 0.8s timeout, circuit breaker and graceful fallback | not established |
| `001055b` | `001055befef13cb190f7f380b79dd371c4cdb8a3` | 2026-10-23 18:31:09 | fix(resilience): bound shipping call to 0.8s with circuit breaker and graceful fallback | not established |
| `79348f4` | `79348f47042849465c737be2493b135a21f37e06` | 2026-10-23 18:35:09 | fix(resilience): bound shipping call to 0.8s with circuit breaker and graceful fallback | not established |

### Provenance Facts
1. **Ancestry:** None of the six service-account commits is an ancestor of `main` (`git merge-base --is-ancestor` returns `False` for all six).
2. **Merge Request !3 Status:** Merge Request `!3` is **unmerged** (confirmed on GitLab via public API: `state: opened`, `merged_at: None`).
3. **Main Code Authorship:** `main`'s `app/clients/shipping_client.py` was authored by FaultForge Agent in commit `e150fad` (`FaultForge Agent <agent@faultforge.internal>`) as an adapted copy of Duo's patch (1 file changed, 18 insertions(+), 30 deletions(-) vs `79348f4`), adding explicit `connect` timeouts and direct settings checks while preserving identical resilience behavior.
4. **Evaluated Commit:** The candidate evaluated in `fault_run_hardened.json` and in CI pipeline [#2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) at commit `d75de80a` matches the deployed Cloud Run container image `app/` tree (tree SHA `de7c0b1cc7d6b7edb90c6b3041b10885ea702492`).
