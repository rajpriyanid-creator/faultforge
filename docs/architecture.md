# FaultForge Architecture & Technical Design

**Revision:** 2.0 (Verified Implementation)  
**Track:** Path A — Start Fresh  
**Autonomy Model:** Supervised Autonomy  

---

## 1. System Overview

FaultForge is an AI-assisted resilience engineering platform built for **GitLab Transcend 2026: Life After Code**. It replaces traditional unit-test mock assumptions with empirical network fault injection, deterministic diagnosis, automated GitLab Duo Agent Platform remediation, exact-fault replay verification, and risk-gated deployment governance.

```
+-------------------------------------------------------------------------------------------------------------+
|                                    GitLab CI/CD Pipeline (9 Covered Stages)                                 |
|                                                                                                             |
|  [1. PLAN]               [2. CREATE]             [3. CONFIGURE]          [4. VERIFY]                        |
|  Incident Dossier &      GitLab Duo Flow &       Toxiproxy Topology &    Baseline Chaos Run                 |
|  Git Bisect Culprit  --> Remediation MR      --> Latency Profile     --> (Breaches 1500ms SLA)              |
|                                                                                 |                           |
|  [9. GOVERN]             [8. MONITOR]            [7. RELEASE]            [6. PACKAGE]        [5. SECURE]    |
|  Evidence Receipt &      Replay Evaluation &     Cloud Run Staging       Multi-stage Docker  Bandit AST &   |
|  Human Approval Gate <-- Live Telemetry      <-- (0% Live Traffic)   <-- Non-root Build  <-- Secret Scanner |
+-------------------------------------------------------------------------------------------------------------+
                                      |
                                      v
              +---------------------------------------------------------------+
              |         GitLab Duo Agent Platform Flow (v1 Schema)            |
              |                                                               |
              |  +--------------------+             +----------------------+  |
              |  | Diagnostician      | ----------> | Resilience Healer    |  |
              |  | (AST Call Site &   |             | (0.8s Timeout, CB &  |  |
              |  |  Bisect Ingestion) |             |  Fallback Quote)     |  |
              |  +--------------------+             +----------------------+  |
              |                                                |              |
              |                                                v              |
              |                                     +----------------------+  |
              |                                     | Chaos Hardener       |  |
              |                                     | (Regression Tests)   |  |
              |                                     +----------------------+  |
              +---------------------------------------------------------------+
                                      |
                                      v
              +---------------------------------------------------------------+
              |                  Candidate Verification Loop                  |
              | 1. Identical Toxiproxy fault profile re-injected              |
              | 2. 10 consecutive candidate probe passes required             |
              | 3. Average latency drops from 3742.46ms to <850ms (>60%)      |
              | 4. Deterministic fallback marked with is_estimate: true       |
              +---------------------------------------------------------------+
                                      |
                                      v
              +---------------------------------------------------------------+
              |                 Supervised Governance Gate                    |
              | - LOW risk tier permits staging candidate deployment          |
              | - Live traffic promotion requires explicit human authorization|
              | - Automated instantaneous rollback via cloudrun_traffic.py    |
              | - Cryptographic SHA-256 sealed Evidence Receipt emitted       |
              +---------------------------------------------------------------+
```

---

## 2. Component Specifications

### A. Core Application Service (`app/`)
- **`app/main.py`**: FastAPI checkout microservice exposing `/api/v1/checkout`, `/api/v1/shipping/rate`, `/health`, and `/metrics`.
- **`app/clients/shipping_client.py`**: Outbound HTTP client interacting with the downstream shipping dependency. Supports bounded connect/read timeouts (0.8s), circuit breaker trip checks, and fallback quote generation.
- **`app/resilience/policy.py`**: Stateful circuit breaker (`CLOSED` -> `OPEN` -> `HALF_OPEN`) tracking sliding failure windows and deterministic fallback generation.
- **`app/resilience/metrics.py`**: Real-time sliding window telemetry tracking latencies (p50, p95, p99), error rates, and circuit breaker trip events.
- **`app/health.py`**: Liveness, readiness, and metrics endpoints returning the active `X-Service-Revision` header for canary verification.

### B. Downstream Carrier Dependency Stub (`stub/`)
- **`stub/mock_shipping_api.py`**: Independent carrier microservice providing real-time rate calculations and simulation endpoints (`/v1/rates`, `/v1/rates/slow`, `/health`) running on port 8081.

### C. Chaos Layer (`chaos/`)
- **`chaos/docker-compose.chaos.yml`**: Compose definition with strict container healthchecks running `shipping-stub` (port 8081), official Shopify Toxiproxy `ghcr.io/shopify/toxiproxy:2.9.0` (ports 8082, 8474), and the `app` (port 8090).
- **`chaos/toxiproxy_helper.py`**: Dual-engine proxy controller supporting Shopify Toxiproxy REST API with live version and toxic read-back, alongside a standalone fallback proxy for Docker-less local environments.
- **`chaos/profiles/latency_cascading_hang.json`**: Version-controlled toxic profile defining a 3500ms latency with 250ms jitter.
- **`chaos/criteria.json`**: SLA criteria defining 1500ms max latency budget, 80% baseline breach threshold, and 10 consecutive candidate passes.

### D. GitLab Duo Custom Flow (`flows/faultforge-flow.yaml`)
Conforms strictly to the official GitLab Duo Custom Flows Schema v1:
- `environment: ambient` and `coding_environment: full`.
- Decoupled `prompts:` block with strict anti-hallucination guidelines.
- Components:
  - `diagnostician`: Identifies the vulnerable call site without guessing or blaming unrelated modules.
  - `resilience_healer`: Synthesizes bounded timeouts, circuit breakers, and fallback mechanisms.
  - `chaos_hardener`: Generates regression test cases and opens a structured Merge Request.
- Model selection is platform-managed (no hardcoded model identifiers).

### E. Pipeline Automation Engine (`scripts/`)
- **`scripts/plan_incident.py`**: Initial lifecycle planning job generating initial incident context.
- **`scripts/collect_evidence.py`**: Compiles sanitized Incident Dossier validated against `schemas/dossier.schema.json`.
- **`scripts/diagnose_and_bisect.py`**: Executes deterministic AST inspection and automated `git bisect` isolating culprit commit `974035c6`.
- **`scripts/trigger_duo_flow.py`**: Invokes GitLab Duo Custom Flows API with fallback to Issue Mention/Assignment.
- **`scripts/configure_chaos.py`**: Configures Toxiproxy network chaos topology in CI pipelines.
- **`scripts/run_fault.py`**: Executes labeled (`baseline` or `candidate`) probe sequences, recording individual probe latencies and read-back toxic parameters.
- **`scripts/evaluate_replay.py`**: Verifies exact-fault profile equivalence and validates the 10 consecutive candidate passes.
- **`scripts/classify_risk.py`**: Evaluates proposed code diff against `chaos/risk-policy.json`.
- **`scripts/monitor_service.py`**: Gathers service telemetry during staging lifecycle.
- **`scripts/cloudrun_traffic.py`**: Manages Google Cloud Run revision canary traffic splitting and instantaneous rollback.
- **`scripts/generate_receipt.py`**: Synthesizes the final machine-readable Evidence Receipt with cryptographic SHA-256 seal.
- **`scripts/truth_audit.py`**: Enforces strict anti-fake rules (zero masked failures, no zero-SHAs, no fake URLs, verified claims).
