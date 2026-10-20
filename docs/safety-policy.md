# FaultForge Safety Policy & Risk-Based Supervised Autonomy

**Target Prize:** Best Supervised Agent ($4,000)  
**Track:** Path A — Start Fresh  
**Declared Autonomy Tier:** SUPERVISED  
**Revision:** 3.0 (Supervised Resilience Agent Specification)

---

## 1. The Supervised Autonomy Paradigm

In strict compliance with the **GitLab Transcend 2026** competition guidelines, FaultForge operates under the **Supervised Autonomy** model:

> **"You approve the outcome, not the individual steps. Your agents execute a multi-step workflow on their own, clearing gates and making decisions along the way. You review the end result, not every individual action."**  
> — Official GitLab Transcend 2026 Hackathon Rubric

### The Enterprise Case for Supervised Autonomy
1. **Why Not "Assisted"?**  
   The Assisted model requires human approval for every file read, AST query, git command, test invocation, and container packaging step. For an enterprise incident recovery workflow spanning 9 lifecycle stages, this introduces intolerable friction, operator fatigue, and slow MTTR (Mean Time to Recovery).
2. **Why Not "Hands-Off"?**  
   The Hands-off model autonomously modifies production infrastructure without human verification. In financial, e-commerce, or mission-critical environments, unchecked autonomous deployments risk catastrophic cascading outages, data loss, and regulatory non-compliance.
3. **The Supervised Sweet Spot:**  
   The FaultForge Supervised Resilience Agent does the exhaustive autonomous heavy-lifting (diagnosing, bisecting, patching, testing, packaging, staging deployment, and exact-fault replay verification). It stops at the final boundary: live production traffic routing (`govern:promote_to_production`), presenting the developer with a cryptographically sealed Evidence Receipt for one-click approval.

---

## 2. Risk Classification Tiers & Blast-Radius Boundaries

FaultForge enforces programmatic risk policies defined in `chaos/risk-policy.json` via `scripts/classify_risk.py`:

| Risk Tier | Diff Scope & File Boundaries | Permitted Autonomous Actions | Mandatory Human Gate |
|---|---|---|---|
| **LOW** | Scoped network timeouts, circuit breaker thresholds, and deterministic fallback quotes in `app/clients/` or `app/resilience/` (<150 lines diff) | Branch creation, MR preparation, full test execution, packaging, staging deployment (0% traffic), exact-fault replay | Required before live production traffic promotion (100%) |
| **MEDIUM** | Dependency modifications (`requirements.txt`), build definitions (`Dockerfile`, `docker-compose`), files outside allowed prefixes | Branch creation, test execution; flagged with `REQUIRES_INSPECTION` | Required prior to staging deployment and production promotion |
| **HIGH** | Authentication, authorization, payment processing, database migrations, secrets management, IAM policies, or destructive commands | **Automated modification strictly prohibited.** Agent halts and files an incident advisory issue | Explicit manual developer implementation required |

---

## 3. The 11 Autonomous Quality Gates Cleared by the Agent

Before requesting human sign-off, the Supervised Agent autonomously verifies 11 distinct quality gates:

1. **Gate 1 (Plan):** Empirical SLA breach detected (>1500ms budget breach under 3500ms downstream delay).
2. **Gate 2 (Plan):** Sanitized Incident Dossier compiled with zero sensitive token or key leakage.
3. **Gate 3 (Create):** Deterministic AST call-site inspection and `git bisect` pinpointing culprit commit (`974035c`).
4. **Gate 4 (Create):** Scoped resilience code patch synthesized (0.8s bounded timeout, 3-failure circuit breaker, fallback).
5. **Gate 5 (Configure):** Automated risk classification confirms diff is MEDIUM tier (client resilience fix without new test fixtures under tests/), routing to Supervised gate.
6. **Gate 6 (Verify):** Unit and integration tests pass cleanly (`pytest tests/unit tests/integration`, 70+ passing).
7. **Gate 7 (Verify):** Exact-fault replay passes 10/10 probes under identical Toxiproxy profile hash (`644a89784316`), achieving 0 SLA breaches and >60% latency reduction.
8. **Gate 8 (Secure):** Bandit static AST security scan confirms 0 high/medium vulnerabilities.
9. **Gate 9 (Package):** Multi-stage Docker container built with non-root security user.
10. **Gate 10 (Release):** Candidate revision deployed to Google Cloud Run staging (0% live production traffic).
11. **Gate 11 (Monitor):** Telemetry probes confirm circuit breaker `CLOSED`, `/health` returns 200, and p95 latency stays within SLA.

---

## 4. The Supervised Sign-off Checkpoint

The agent halts at Stage 9 (`govern:promote_to_production`):
- **Evidence Dossier Presented to Operator:**
  - Merge Request payload with code diff and explanation.
  - Cryptographically sealed Evidence Receipt (`reports/evidence_receipt.json` & `/api/v1/evidence`).
  - Active staging URL on Google Cloud Run (`https://faultforge-checkout-136942862703.us-central1.run.app/dashboard`).
- **Human Decision:**
  - Click **Play** on `govern:promote_to_production` in GitLab CI/CD.
  - Or run: `python scripts/cloudrun_traffic.py --action promote --service faultforge-checkout`.
- **Instant Rollback Guard:**
  If post-promotion anomalies are detected, the system immediately invokes `scripts/cloudrun_traffic.py --action rollback` to revert traffic to the prior known-good revision with zero downtime.

---

## 5. Non-Negotiable Safety Invariants

1. **Disposable Isolation:** Chaos fault injection is restricted strictly to disposable test and staging environments. Live customer traffic is never subjected to fault injection.
2. **Least Privilege Identity:** CI runners, GitLab tokens, and Google Cloud service accounts operate with strictly bounded, least-privilege permissions.
3. **Zero Secret Exposure:** The Incident Dossier and log collection engines actively sanitize logs using regex filters to strip Bearer tokens, API keys, passwords, and private certificates.
4. **No Self-Approval:** An AI-generated patch is forbidden from approving or merging itself into protected branches. The independent CI pipeline is the sole arbiter of test correctness.
5. **Idempotency Protection:** Blind retries on mutating or non-idempotent endpoints (e.g. charge credit card) are strictly banned. Only safe, read-only requests may use retries.
6. **No False Claims:** If health probes fail or if exact-fault replay fails, the system immediately marks the status as `NOT_VERIFIED` or `CONTAINED_NEEDS_REVIEW` and halts the release pipeline.
