# AGENTS.md — Agent Operating Rules & Guardrails
## FaultForge: Break It, Heal It

This document defines the strict operating constraints, safety boundaries, code conventions, and verification requirements for **GitLab Duo Agent Platform** custom flows and any AI agent operating within this repository.

---

### 1. Fundamental Principle
**FaultForge must prove resilience, not merely generate a fix.**
The primary differentiator of this project is the **before/after proof under the exact same controlled failure condition**. Never declare success or report recovery unless independent, machine-readable CI tests confirm it.

---

### 2. Evidence Integrity (Zero Hallucination Policy)
- **Do not invent data:** Never fabricate commit SHAs, pipeline job URLs, test logs, latency percentiles, error rates, or Cloud Run revision IDs.
- **Strict evidence separation:** Always distinguish between **confirmed facts** (e.g., deterministic probe failure, explicit stack trace) and **hypotheses** (e.g., suspected regression commit).
- **No false blame:** Toxiproxy creates the stress condition; it does not inherently mean a recent commit is guilty. Use `git bisect` only when an automated probe demonstrably passes on good commits and fails on bad commits. Otherwise, state that it is a hypothesis or code-level weakness.

---

### 3. Resilience Hardening Rules
When proposing code patches (Healer / Hardener roles):
- **Make the smallest scoped change:** Focus strictly on the affected outbound dependency path. Do not perform wide architectural refactorings.
- **Enforce bounded timeouts:** All outbound network calls (`httpx`, `requests`, sockets) must specify explicit, bounded connect and read timeouts (e.g. `0.8s` SLA budget). Unbounded network calls are prohibited.
- **Idempotency-aware retries:** Never apply retries blindly. Retrying non-idempotent operations (such as payment processing, order capture, or mutating database writes) can cause duplicate charges and data corruption. Only retry safe, idempotent operations (such as shipping rate quotes or status lookups) using exponential backoff with jitter.
- **Graceful fallbacks:** Provide deterministic, observable fallbacks. The fallback response must clearly identify itself with `"is_fallback": true` and a diagnostic reason. Do not silently swallow exceptions or masquerade a degraded service as a healthy upstream response.
- **Circuit Breakers:** Implement circuit breaking (e.g. 3 consecutive failures trips circuit to OPEN for 10s cooldown) to prevent cascading resource exhaustion.

---

### 4. Safety & Autonomy Classification (Supervised Gate)
This repository operates under the **Supervised Autonomy** model:
- **Low Risk:** Scoped timeouts, circuit breaker thresholds, graceful fallback estimates in `app/resilience/` or `app/clients/`. Agents are permitted to open branches, create Merge Requests, run test suites, and trigger staging verification.
- **Medium Risk:** Dependency version changes, broader control flow modifications. Requires explicit developer review.
- **High Risk:** Authentication, authorization, payment processing, database migrations/schema changes, secret handling, or destructive actions. **Agents are strictly forbidden from modifying these areas automatically.**
- **No direct push to protected branches:** All changes must be proposed via a GitLab Merge Request targeting `main`.
- **Production Gate:** Live production promotion to Google Cloud Run requires explicit human approval via the manual CI gate (`govern:promote_to_production`).

---

### 5. Verification & Exact-Fault Replay Requirements
- **Deterministic regression test:** Every proposed fix must include a regression test in `tests/chaos/` that reproduces the original failure.
- **Identical fault profile:** The exact same Toxiproxy fault profile (matching JSON attributes and profile hash) used to break the baseline must be replayed against the candidate patch.
- **Objective machine-readable gates:** Verification is evaluated by scripts (`scripts/evaluate_replay.py`), not by model self-assessment.
- **Fail-safe halt:** If any test fails, if dependencies are unreachable, or if evidence is ambiguous, mark status as `NOT_VERIFIED` or `CONTAINED_NEEDS_REVIEW` and halt the flow.

---

### 6. Repository Commands & Test Execution
Agents must use the following standard commands when verifying code changes:

- **Run Unit & Integration Tests:**
  ```bash
  python -m pytest tests/unit tests/integration -v
  ```
- **Run Live Chaos Resilience Test (requires Toxiproxy stack):**
  ```bash
  python -m pytest tests/chaos/test_resilience.py -v
  ```
- **Launch Chaos Stack (Docker Compose):**
  ```bash
  docker compose -f chaos/docker-compose.chaos.yml up -d
  ```
- **Run Fault Injection Probe:**
  ```bash
  python scripts/run_fault.py --mode baseline --expect-fail --output reports/fault_run_baseline.json
  python scripts/run_fault.py --mode hardened --output reports/fault_run_hardened.json
  ```
- **Evaluate Replay Gates:**
  ```bash
  python scripts/evaluate_replay.py --baseline reports/fault_run_baseline.json --hardened reports/fault_run_hardened.json
  ```

