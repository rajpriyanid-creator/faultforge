# FaultForge Architecture & Technical Design

**Revision:** 1.0 (Component Specifications)  
**Last Updated:** October 2026

## 1. System Overview

FaultForge is an AI-assisted resilience hardening system designed for the **GitLab Transcend 2026: Life After Code** hackathon. It automates controlled chaos rehearsal, deterministic evidence collection, GitLab Duo Agent Platform diagnosis/remediation, and exact-fault verification.

```
+-----------------------------------------------------------------------------------+
|                              GitLab CI/CD Pipeline                                |
|                                                                                   |
|  [PLAN]              [CREATE]            [CONFIGURE]         [VERIFY]             |
|  Incident Dossier -> Duo Flow Plan    -> Toxiproxy Setup  -> Chaos Probe Baseline |
|                                                              (Fails SLA / Hangs)  |
|                                                                     |             |
|  [GOVERN]            [MONITOR]           [RELEASE]           [VERIFY REPLAY]      |
|  Evidence Receipt <- Telemetry Probe  <- Cloud Run Deploy <- Exact-Fault Replay   |
|  (Supervised Gate)                                           (Passes via Fallback)|
+-----------------------------------------------------------------------------------+
                                       |
                                       v
               +-----------------------------------------------+
               |       GitLab Duo Agent Platform Flow          |
               |                                               |
               |  +----------------+      +-----------------+  |
               |  | Diagnostician  | ---> | Resilience      |  |
               |  | (Code Analysis)|      | Healer          |  |
               |  +----------------+      +-----------------+  |
               |          |                        |           |
               |          v                        v           |
               |  +----------------+      +-----------------+  |
               |  | Bisect Probe   |      | Chaos Hardener  |  |
               |  | (Git History)  |      | (Regression Tst)|  |
               |  +----------------+      +-----------------+  |
               +-----------------------------------------------+
                                       |
                                       v
              +------------------------------------------------+
              |           Remediation Merge Request            |
              | - Bounded Timeout (0.8s)                       |
              | - Circuit Breaker (3 fails, 10s cooldown)      |
              | - Graceful Fallback Quote                      |
              +------------------------------------------------+
```

---

## 2. Component Directory

### A. Checkout Service (`app/`)
- **`app/main.py`**: FastAPI application exposing `/api/v1/checkout`, `/api/v1/shipping/rate`, and health endpoints.
- **`app/clients/shipping_client.py`**: Outbound HTTP client interacting with the shipping carrier dependency. Implements timeout enforcement, circuit breaker checks, and fallback triggers.
- **`app/resilience/policy.py`**: Stateful circuit breaker (`CLOSED` -> `OPEN` -> `HALF_OPEN`) and deterministic fallback generator.
- **`app/resilience/metrics.py`**: Real-time sliding window latency percentiles (p50, p95, p99), error rates, and circuit trips.
- **`app/health.py`**: Liveness (`/health`), readiness (`/ready`), and telemetry (`/metrics`) probes.

### B. Downstream Dependency Stub (`stub/`)
- **`stub/mock_shipping_api.py`**: Standalone carrier service providing real-time rate calculations and simulation endpoints for testing delays.

### C. Chaos Layer (`chaos/`)
- **`chaos/toxiproxy_helper.py`**: Dual-engine chaos proxy supporting both Shopify Toxiproxy REST API and an in-process standalone chaos proxy for environments without external daemons.
- **`chaos/profiles/`**: Version-controlled JSON profiles defining exact toxic parameters (e.g. 3500ms latency, 250ms jitter).

### D. GitLab Duo Flow (`flows/faultforge-flow.yaml`)
- Multi-agent workflow orchestrating Diagnostician, Healer, and Hardener roles.
- Employs GitLab APIs to inspect commits, open Merge Requests, and evaluate pipeline results.

### E. Deterministic Pipeline Scripts (`scripts/`)
- **`run_fault.py`**: Injects fault and records probe latency percentiles.
- **`collect_evidence.py`**: Builds compact, sanitized Incident Dossier.
- **`diagnose_and_bisect.py`**: Analyzes code weaknesses and evaluates git bisect applicability.
- **`duo_orchestrator.py`**: Synthesizes MR payload and risk assessment.
- **`evaluate_replay.py`**: Compares baseline vs candidate under identical fault profile.
- **`generate_receipt.py`**: Emits tamper-evident Evidence Receipt with SHA-256 seal.
- **`cloudrun_traffic.py`**: Controls Google Cloud Run revision canary traffic and automated rollback.
