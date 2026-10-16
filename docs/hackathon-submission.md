# GitLab Transcend 2026: Life After Code — Submission Guide

## Project Information

- **Project Name:** FaultForge
- **Tagline:** Rehearse a failure. Recover safely. Prove the service is stronger.
- **Track:** Path B — Bring Your Own (Open Source Base with MIT License)
- **Primary Prize Category:** Path B — Best Supervised Agent ($4,000)
- **Secondary Prize Category:** Path B — Most Stages Covered ($5,000)
- **Additional Prize Opportunity:** Most Creative ($4,000)
- **Bonus Award:** Google Cloud Deployment Bonus (+0.2 Points)
- **Autonomy Level:** Supervised Autonomy

---

## Pitch & Submission Overview

### One-Sentence Pitch
FaultForge uses GitLab Duo Agent Platform to inject a controlled dependency failure into an isolated application environment, diagnose the code or configuration weakness that makes the application fail, recover safely, open a resilience-hardening merge request, and prove the fix by replaying the exact same fault.

### The Problem
Most CI pipelines only tell a developer when a deterministic unit test fails. AI coding assistants can generate code patches, but they cannot prove the patch actually withstands real-world network degradation. When external dependencies slow down, timeout, or reset connections, services experience cascading failures and thread starvation because unit tests mocked those dependencies.

### The Differentiator
The differentiator is not "AI says it fixed the app." **It is the before/after empirical proof under the exact same controlled failure condition.**

---

## Lifecycle Stages Covered (9 of 9)

1. **`plan`**: Creates an incident work item and Incident Dossier with sanitized logs and failure evidence.
2. **`create`**: GitLab Duo Flow Orchestrator prepares the resilience fix, branch, and Merge Request with risk classification.
3. **`configure`**: Configures Toxiproxy network chaos topology and latency toxic profiles.
4. **`verify`**: Runs pytest unit/integration tests and replays the identical Toxiproxy fault against both baseline and hardened revisions.
5. **`secure`**: Executes Bandit AST security scans and regex secret detection to ensure zero credential leakage.
6. **`package`**: Builds multi-stage production container image with security non-root user.
7. **`release`**: Deploys candidate revision to Google Cloud Run staging environment.
8. **`monitor`**: Evaluates live health probes (`/health`, `/ready`), sliding window latency percentiles (p50/p95/p99), and circuit breaker status.
9. **`govern`**: Enforces Supervised Autonomy risk policy, evaluates tamper-evident SHA-256 seal, and gates live production promotion on human approval.

---

## Architecture & Technology Stack

- **Agent Platform:** GitLab Duo Agent Platform Custom Flow (`flows/faultforge-flow.yaml`)
- **Backend Framework:** Python 3.12 + FastAPI (`app/main.py`)
- **Fault Injection Engine:** Shopify Toxiproxy & Python Standalone Chaos Proxy (`chaos/toxiproxy_helper.py`)
- **Resilience Layer:** Bounded HTTP timeouts (`httpx`), Circuit Breaker (`CLOSED` -> `OPEN` -> `HALF_OPEN`), and Graceful Fallback (`app/resilience/policy.py`)
- **Deployment Platform:** Google Cloud Run with Knative revision traffic management (`infra/cloudrun/`)
- **Verification Engine:** Machine-readable before/after evaluator (`scripts/evaluate_replay.py`) and tamper-evident Evidence Receipt (`scripts/generate_receipt.py`)
