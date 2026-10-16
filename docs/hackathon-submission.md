# GitLab Transcend 2026: Life After Code — Submission Guide

## 1. Project Information

- **Project Name:** FaultForge
- **Tagline:** Rehearse a failure. Recover safely. Prove the service is stronger.
- **Track Selection:** Path A — Start Fresh (or Path B if citing an existing MIT upstream repository; default: Path A)
- **Primary Prize Category:** Best Supervised Agent ($4,000)
- **Secondary Prize Category:** Most Stages Covered ($5,000)
- **Additional Prize Opportunity:** Most Creative ($4,000)
- **Bonus Award:** Google Cloud Deployment Bonus (+0.2 Points)
- **Autonomy Level:** Supervised Autonomy (Risk-gated human promotion for live traffic)

---

## 2. Devpost Submission Copy

### One-Sentence Pitch
FaultForge uses GitLab Duo Agent Platform to inject a controlled dependency failure into an isolated application environment, diagnose the code or configuration weakness that makes the application fail, recover safely, open a resilience-hardening merge request, and prove the fix by replaying the exact same fault.

### The Problem It Solves
Standard CI pipelines test that unit tests pass, but unit tests usually mock outbound HTTP dependencies. In production, when an external API experiences transient network degradation or slow responses, services experience thread starvation, cascading timeouts, and unhandled 5xx errors. AI coding tools can suggest code changes, but cannot verify whether the patch actually survives live network failure.

### What FaultForge Does
FaultForge closes the loop between chaos engineering and AI-assisted remediation:
1. **Injects Chaos:** Routes outbound calls through Shopify Toxiproxy and injects a 3500ms delay.
2. **Proves Failure:** Captures SLA budget breaches (>1500ms) with empirical telemetry.
3. **Diagnoses Weakness:** Discovers the regression boundary via deterministic `git bisect` and AST call-site inspection.
4. **Remediates with Duo:** GitLab Duo custom flow synthesizes a minimal resilience fix (0.8s timeout, circuit breaker, and observable fallback) and opens a Merge Request.
5. **Replays Exact Fault:** Re-runs the identical Toxiproxy fault profile hash against the candidate code.
6. **Signs Audit Receipt:** Generates a cryptographic SHA-256 sealed Evidence Receipt.
7. **Supervised Gate:** Enforces risk policy and requires human developer approval before promoting Cloud Run candidate revisions.

### Limitations & Honest Boundaries
- Evaluated on a focused FastAPI microservice with an external shipping carrier dependency.
- Primary fault scenario is a 3500ms dependency latency toxic; secondary scenario is connection reset.
- Fallback quotes are deterministically generated estimates clearly flagged with `is_fallback: true` and `is_estimate: true` to avoid misrepresenting live carrier data.
- Does not modify database schemas, payment processing, or authorization code.

---

## 3. Technology Stack

- **Agent Platform:** GitLab Duo Agent Platform Custom Flow (`flows/faultforge-flow.yaml`)
- **Backend Service:** Python 3.12 + FastAPI (`app/main.py`)
- **Chaos Engine:** Shopify Toxiproxy (`ghcr.io/shopify/toxiproxy:2.9.0`) & `chaos/toxiproxy_helper.py`
- **Testing:** pytest & pytest-asyncio (`tests/unit`, `tests/integration`, `tests/chaos`)
- **Deployment:** Google Cloud Run Knative spec (`infra/cloudrun/service.yaml`) & `scripts/cloudrun_traffic.py`
