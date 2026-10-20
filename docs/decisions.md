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

---

## 5. Toxiproxy Architecture & CI Runner Networking

### Context & Problem
In GitLab CI/CD shared runner environments with standard Docker executor, containers declared under `services:` run in independent network namespaces. While the job container can reach the Toxiproxy service on `http://toxiproxy:8474`, the Toxiproxy service container cannot reach `127.0.0.1:8081` (where the mock carrier stub runs inside the job container).

### Evaluated Architectural Options
1. **Multi-Container Services:** Package and publish the shipping stub as a container image and run both stub and Toxiproxy as CI services.
   - *Trade-off:* High build and pull latency; tight coupling to external image registries; complex inter-service DNS configuration.
2. **Docker-in-Docker (DinD) with Docker Compose:** Run the entire test stack inside a `docker:dind` container.
   - *Trade-off:* Adds 2-3 minutes of Docker daemon bootstrap overhead per pipeline job; requires privileged runner modes; introduces Docker-layer cache misses.
3. **Official Shopify `toxiproxy-server` Binary in Job Container:** Bootstrap the official Shopify Toxiproxy `v2.9.0` Linux binary directly in the job container via `scripts/start_toxiproxy.py`.
   - *Trade-off:* Requires downloading the official 7.7MB binary on cache-miss (takes ~1-2 seconds).

### Decision
**Adopt Option 3 (Official `toxiproxy-server` Binary via Bootstrapper).**
Running the official Shopify Toxiproxy binary directly within the job container provides:
- **100% Deterministic Loopback Networking:** The mock carrier (`127.0.0.1:8081`), Toxiproxy proxy (`127.0.0.1:8082`), and application service (`127.0.0.1:8090`) all communicate over local loopback (`127.0.0.1`), eliminating inter-container network failure modes.
- **Official Shopify Engine Integrity:** The daemon runs the exact official Shopify Toxiproxy `2.9.0` release binary, returning real API version `2.9.0` and supporting live toxic read-backs.
- **Sub-Second Job Startup:** Avoids heavy container orchestration overhead on shared SaaS runners.
- **Zero Standalone Proxy in CI:** Enables complete removal of `--allow-standalone-proxy` from all CI jobs (`create`, `configure`, `verify`). All CI evidence receipts reflect real Toxiproxy verification.
