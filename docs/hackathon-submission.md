# GitLab Transcend 2026: Life After Code — Submission Guide

**Project:** FaultForge ("Break It, Heal It")  
**Track:** Path A — Start Fresh  
**Deadline:** 27 Oct 2026, 1:00 PM UTC (6:30 PM IST)  
**Submission Portal:** Devpost  

---

## 1. Project Overview

- **Project Name:** FaultForge
- **Tagline:** Rehearse a failure. Recover safely. Prove the service is stronger.
- **Track Selection:** **Path A — Start Fresh** (Inception: October 16, 2026, commit `b22d2e8`)
- **Primary Prize Category:** **Best Supervised Agent ($4,000)**
  - Full automation for chaos injection, AST bisecting, MR generation, and staging deployment, paired with a mandatory human approval gate for live traffic.
- **Secondary Prize Category:** **Most Stages Covered ($5,000)**
  - Executes 11 agent quality checks across all 9 GitLab lifecycle stages (`plan`, `create`, `configure`, `verify`, `secure`, `package`, `release`, `monitor`, `govern`) actively with verifiable machine-readable artifacts.
- **Additional Prize Opportunity:** **Most Creative ($4,000)**
  - First closed-loop system combining chaos engineering, GitLab Duo custom flows, and empirical exact-fault replay verification.
- **Google Cloud Deployment Bonus:** (+0.2 Points)
  - Live Google Cloud Run Service: [`https://faultforge-checkout-136942862703.us-central1.run.app`](https://faultforge-checkout-136942862703.us-central1.run.app) (Revision `faultforge-checkout-00002-kpl`, HTTP 200 OK)
  - Interactive Dashboard: [`https://faultforge-checkout-136942862703.us-central1.run.app/dashboard`](https://faultforge-checkout-136942862703.us-central1.run.app/dashboard)
  - Knative deployment spec (`infra/cloudrun/service.yaml`) and automated canary traffic splitting / instant rollback automation (`scripts/cloudrun_traffic.py`).
- **Autonomy Model:** Supervised Autonomy (Autonomous staging, testing, and replay; mandatory human sign-off for live production traffic).

---

## 2. Devpost Submission Copy

### One-Sentence Pitch
FaultForge injects controlled network chaos into an isolated dependency, proves the service breaches its SLA, uses GitLab Duo Agent Platform to diagnose and open a fix merge request, replays the identical fault to prove recovery from machine-readable data, and enforces human-supervised promotion to live traffic.

### The Problem It Solves
Standard CI pipelines test that unit tests pass, but unit tests usually mock outbound HTTP dependencies. In production, when an external API experiences transient network degradation or slow responses, services suffer thread starvation, cascading timeouts, and unhandled 5xx errors. AI coding tools can suggest code changes, but cannot verify whether the patch actually survives live network failure.

### What FaultForge Does
FaultForge closes the loop between chaos engineering, AI-assisted diagnosis, and empirical verification:
1. **Tracks Incident Issue:** Monitors SLA budget breaches and opens a structured Incident Issue with sanitized logs.
2. **Injects Chaos:** Routes outbound calls through Shopify Toxiproxy and injects a 3500ms delay (±250ms jitter).
3. **Proves Baseline Failure:** Proves checkout service breaches the 1500ms SLA budget (observed 5/5 breaches, 3742.46ms avg).
4. **Diagnoses Weakness:** Discovers the regression boundary via deterministic `git bisect` and AST call-site inspection, pinpointing commit `974035c6`.
5. **Remediates with Duo:** GitLab Duo custom flow (`flows/faultforge-flow.yaml`) plans a scoped resilience fix (0.8s timeout, circuit breaker, and observable fallback) and opens a Merge Request. In CI without Duo API access, CI falls back cleanly to reference code and explicitly records candidate source as `reference-fix (not Duo-authored)` in the cryptographic receipt.
6. **Replays Exact Fault:** Re-runs the identical Toxiproxy fault profile hash (`644a89784316`) against the candidate code across 10 consecutive probes.
7. **Signs Audit Receipt:** Generates a cryptographic SHA-256 sealed Evidence Receipt with full run history.
8. **Supervised Gate:** Enforces risk policy and requires human developer approval before promoting Cloud Run candidate revisions to live traffic.

### Duo Execution & Fallback Wording
If GitLab Duo custom flow did not execute on the cloud runner due to namespace credit or environment constraints, the Duo flow (`flows/faultforge-flow.yaml`) is described as implemented and verified for specification validity, and the pipeline operates as agent-agnostic verification of any candidate fix. The candidate fix is truthfully reported as `reference-fix (not Duo-authored)` unless `duo_run.json` confirms `executed: true`.

### Limitations & Honest Boundaries
- Evaluated on a focused FastAPI checkout microservice with an external shipping carrier dependency.
- Primary fault scenario is a 3500ms dependency latency toxic (hash `644a89784316`); secondary scenario is connection reset.
- Fallback quotes are deterministically generated estimates clearly flagged with `is_fallback: true` and `is_estimate: true` to avoid misrepresenting live carrier data.
- Does not modify database schemas, payment processing, or authorization code.
- GitLab Duo flow execution in CI requires instance-level Duo Agent Platform credentials; otherwise records honest `NOT_EXECUTED_NO_CREDENTIALS` and uses reference fix.
- Orbit dependency is unused.

---

## 3. Technology Stack

- **Agent Platform:** GitLab Duo Agent Platform Custom Flow Schema v1 (`flows/faultforge-flow.yaml`)
- **Backend Service:** Python 3.12 + FastAPI (`app/main.py`)
- **Chaos Engine:** Shopify Toxiproxy (`v2.9.0`) & `chaos/toxiproxy_helper.py`
- **Testing:** pytest & pytest-asyncio (`tests/unit`, `tests/integration`, `tests/chaos`)
- **Deployment:** Google Cloud Run Knative spec (`infra/cloudrun/service.yaml`) & `scripts/cloudrun_traffic.py`
- **Governance:** Cryptographic SHA-256 sealed receipts (`scripts/generate_receipt.py`)

---

## 4. Video Demonstration Outline (< 3 Minutes)

- **0:00 – 0:35:** Incident Issue & Baseline Failure (Toxiproxy 3500ms delay, 1500ms SLA budget breach).
- **0:35 – 1:05:** Deterministic Regression Discovery (`git bisect` isolates commit `974035c`).
- **1:05 – 1:45:** GitLab Duo Agent Platform Custom Flow (Diagnostician, Healer, Hardener MR).
- **1:45 – 2:20:** 9-Stage CI/CD Pipeline & Exact-Fault Replay (10/10 passes under hash `644a89784316`, <850ms latency).
- **2:20 – 2:50:** Supervised Governance Gate, Cloud Run Rollback & Tamper-Evident Evidence Receipt.
