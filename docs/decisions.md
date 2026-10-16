# FaultForge Architectural & Technical Decisions Record (ADR)

**Last Updated:** 2026-10-16  
**Context:** GitLab Transcend 2026 Hackathon (Deadline: 27 Oct 2026, 1:00 PM UTC)  
**Track:** Path A (Start Fresh)  
**Autonomy Model:** Supervised Autonomy (Risk-gated human promotion for live traffic)

---

## 1. GitLab Duo Agent Platform Flow Registry v1 Schema

### Official Documentation References
- **Custom Flow YAML Schema:** `https://docs.gitlab.com/user/duo_agent_platform/flows/custom_flows_schema/` (Fetched & verified: 2026-10-16)
- **Custom Flows Guide:** `https://docs.gitlab.com/user/duo_agent_platform/flows/custom_flows/`
- **Flow Triggers:** `https://docs.gitlab.com/user/duo_agent_platform/triggers/`
- **Flow Registry Specification v1:** `https://gitlab.com/gitlab-org/modelops/applied-ml/code-suggestions/ai-assist/-/blob/main/docs/flow_registry/v1.md`

### Discovered Schema Constraints & Applied Decisions
1. **Top-Level Restricted Fields:**
   - The custom flow validator **rejects** `name`, `description`, and `product_group` at the top level of the YAML document. Flow metadata is registered directly via GitLab UI / AI Catalog.
   - Top-level fields used: `version: "v1"`, `environment: ambient`, `coding_environment: full`.
2. **Environment & Workspace:**
   - `environment: ambient` is required for background/agentic workload execution.
   - `coding_environment: full` ensures a complete repository clone, Git hooks, and dependency cache are provisioned before agent steps execute.
3. **No Model Specification in Flow YAML:**
   - The `model` field inside prompts or components is prohibited in custom flows (`model in prompts` is restricted). Model selection (e.g. Claude 3.5 Sonnet) is governed centrally by GitLab Duo group or instance configuration settings.
4. **Component Definition (`AgentComponent`):**
   - Components use `type: AgentComponent`.
   - Prompts are declared under the top-level `prompts:` dictionary and referenced via `prompt_id`.
   - Allowed toolset assigned: `read_file`, `list_dir`, `run_command`.
5. **Flow Graph & Routers:**
   - Entry point declared as `flow.entry_point: "diagnostician"`.
   - Routers control transition from `diagnostician` to `resilience_healer` to `end`.

---

## 2. Duo Flow Triggering & Execution Mechanics

### Primary Mechanism: REST API Trigger
- Endpoint: `POST {CI_API_V4_URL}/projects/{CI_PROJECT_ID}/duo_agent_platform/flows/{FLOW_ID}/runs`
- Header: `PRIVATE-TOKEN: {FF_GITLAB_TOKEN}`
- Body: Structured JSON payload containing `incident_id`, `commit_sha`, `fault`, `observations`, and `evidence`.

### Supported Human/Platform Fallback Mechanisms
If the REST endpoint is restricted or flow requires webhooks:
1. **Issue Assignment:** Flow service account (e.g. `@ai-faultforge-flow`) is assigned to the generated Incident Issue.
2. **Mention Trigger:** An issue comment mentioning `@ai-faultforge-flow` is posted with the incident dossier summary.

---

## 3. Failure Mode & Resilience Contract

### Empirical Failure Mode
- Under 3500ms ± 250ms downstream delay, the unhardened service at commit `974035c` does not crash; it hangs for ~3.7s and returns HTTP 200.
- The failure mode is an **SLA Latency Budget Breach (>1500ms)** against business requirements.

### Hardened Contract
- Bounded client timeout: `0.8s` on `httpx.AsyncClient`.
- Total roundtrip duration: `< 1500ms` SLA budget.
- Graceful fallback quote returned on timeout or downstream failure.
- Fallback schema: `is_fallback: true`, `is_estimate: true`, order status: `CONFIRMED_ESTIMATED_SHIPPING`.
- No simulated sleeping (`time.sleep`) or mocking (`patch`, `AsyncMock`) in chaos evidence.

---

## 4. Git Bisect Regression Verification
- Root commit `b22d2e8` verified resilient (bounded timeout + fallback).
- Current `HEAD` verified fragile (unbounded client call).
- Deterministic `git bisect run scripts/bisect_probe.py` isolates exact culprit:
  `974035c6e45e7c177452df260a155b6508b828e9` ("perf: reuse client, simplify error handling").
