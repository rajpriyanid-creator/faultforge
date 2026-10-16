# FaultForge Safety Policy & Risk-Based Autonomy

## 1. Declared Autonomy Model: SUPERVISED

In compliance with the official **GitLab Transcend 2026** competition rules, FaultForge declares the **Supervised Autonomy** tier.

- **Automated Lifecycle Scope:** Multi-step chaos rehearsal, evidence-backed diagnosis, candidate patch generation, regression testing, exact-fault replay, container packaging, security scanning, and candidate deployment to isolated staging revisions.
- **Human Approval Gate:** Final live production traffic migration and high-impact actions strictly require explicit human developer review and authorization.

---

## 2. Risk Classification Tiers

| Risk Tier | Scope & Examples | Automated System Permissions | Human Approval Requirement |
|---|---|---|---|
| **LOW** | Scoped network timeouts, circuit breaker thresholds, deterministic fallback quotes in `app/resilience/` or `app/clients/` | Prepare branch, generate MR, run full test suite, deploy to staging candidate revision | Required only before live production promotion |
| **MEDIUM** | Dependency version upgrades, broad control flow changes, component restructuring | Prepare branch and MR, run tests; mark as requiring developer inspection | Required prior to staging deployment and production promotion |
| **HIGH** | Authentication, authorization, payment capture, database schema migrations, IAM permissions, secrets management, destructive file operations | Prohibited from automated modification. System must halt and create an advisory issue | Explicit manual developer implementation required |

---

## 3. Non-Negotiable Safety Principles

1. **Disposable Isolation:** Chaos fault injection is restricted strictly to disposable test and staging environments. Live production customer traffic is never subjected to fault injection.
2. **Least Privilege Identity:** CI runners, GitLab tokens, and Google Cloud service accounts operate with strictly bounded, least-privilege permissions.
3. **Zero Secret Exposure:** The Incident Dossier and log collection engines actively sanitize logs using regex filters to strip Bearer tokens, API keys, passwords, and private certificates.
4. **No Self-Approval:** An AI-generated patch is forbidden from approving or merging itself. The independent CI pipeline is the sole arbiter of test correctness.
5. **Idempotency Protection:** Blind retries on mutating or non-idempotent endpoints (e.g. charge credit card) are strictly banned. Only safe, read-only requests may use retries.
6. **No False Claims:** If health probes fail or if exact-fault replay fails, the system immediately marks the status as `NOT_VERIFIED` or `CONTAINED_NEEDS_REVIEW` and halts the release pipeline.
7. **Automated Rollback:** If candidate revision health probes fail post-deployment, traffic is instantly rolled back to the last known-good revision via `scripts/cloudrun_traffic.py`.
