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
3. **Proves Baseline Failure:** Proves checkout service breaches the 1500ms SLA budget (observed 5/5 breaches, 3,558.46ms avg latency, 3,738.16ms max).
4. **Diagnoses Weakness:** Discovers the regression boundary via deterministic `git bisect` and AST call-site inspection, pinpointing commit `974035c6`.
5. **Remediates with Duo:** GitLab Duo Agent Platform custom flow (`flows/faultforge-flow.yaml`, [Session 9909079](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079), CI Job `17391324956`, Model `claude_sonnet_5_5_vertex`) diagnosed [Issue #42](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/42), synthesized a bounded 0.8s timeout, circuit breaker, and graceful fallback in `app/clients/shipping_client.py`, and opened [Merge Request !3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) (Commit `f8aa9d98` authored by `FaultForge, Supervised, Resilience, Healer`).
6. **Replays Exact Fault (0/20 SLA Breaches — Degraded but Available):** Re-runs the identical Toxiproxy fault profile hash (`644a89784316`) against the candidate code across consecutive probes. All probes pass the SLA budget (0% breaches vs 100% baseline failure; -86.4% mean reduction (3,558.46ms down to 484.27ms, p95 806.79ms)). The bimodal distribution reflects timeout probes exercising the 0.8s deadline within budget, followed by breaker-tripped probes short-circuiting locally in ~2.27–2.99ms to return deterministic fallback rate quotes (`$7.50 + $1.25 * weight_kg`) without dropped checkouts.
7. **Signs Cryptographic Audit Receipt:** Generates a tamper-evident SHA-256 sealed Evidence Receipt with full run history across all 9 GitLab stages.
8. **Supervised Human Gate:** Enforces risk policy and requires human developer approval before promoting Cloud Run candidate revisions to live traffic.

### Evidence Receipt Status & Verified Duo Execution
The final signed cryptographic Evidence Receipt records status `RECOVERED_AND_VERIFIED`.
- **GitLab Duo Flow Execution:** **ESTABLISHED & VERIFIED** live on GitLab SaaS ([Session 9909079](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079), [MR !3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3), Commit `f8aa9d98`, `candidate_source: commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token`).
- **Candidate Cloud Run Deployment in Public CI:** Stage `release` is actively verified (`SUCCESS`) via masked CI credentials (`GCP_SA_KEY`), deploying candidate revision `faultforge-checkout-00026-sam` with 10% canary traffic routing.
- **Live Canary Traffic Split Verification:** Probed endpoint confirms candidate revision `faultforge-checkout-00026-sam` is healthy (HTTP 200) with verified 10% canary traffic split (status `VERIFIED` in `reports/live_verification.json`).

FaultForge proves that honest status reporting beats impressive simulated green checkmarks.

### Duo Execution & Provenance Tracking
GitLab Duo custom flow execution on GitLab SaaS runners is tracked with complete provenance. When the flow runs, `duo_run.json` confirms `executed: true` with session URL, and `duo_evidence.json` confirms `candidate_source: commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token`. In offline local evaluation without tokens, the pipeline falls back cleanly and reports `reference-fix (not Duo-authored)`.

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
