# FaultForge Verified CI Sample Reports

These sample reports document the complete empirical evidence lifecycle of FaultForge: incident reproduction, autonomous GitLab Duo Healer remediation, exact-fault replay verification, and GitLab CI/CD pipeline execution.

---

## 1. Commit SHA & Multi-Stage Provenance Architecture

Auditors will observe different commit SHAs and generation timestamps across these sample reports. This multi-commit structure is an intentional reflection of the real-world incident lifecycle rather than an inconsistency:

1. **Baseline Incident Reproduction (`b063a91b` on `main`):**
   - The unpatched production codebase where the SLA breach occurred. `app/clients/shipping_client.py` contains the regression (no timeout, no fallback).
   - Used to generate `incident_dossier.json`, `issue.json` (Incident #42), and `fault_run_baseline.json` (2026-10-22 17:38:19 UTC).

2. **Candidate Duo Remediation (`f8aa9d98` on `fix/resilience-shipping-timeout`):**
   - Candidate resilience patch authored autonomously by the GitLab Duo service account (`FaultForge, Supervised, Resilience, Healer <service_account_group_121124982_e6349fd5e8ecd6554efb712ed8e2654f@noreply.gitlab.com>`) via Duo Agent Platform Session [9909079](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079).
   - Submitted as Merge Request [!3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) (unmerged).
   - Evaluated under identical Toxiproxy fault profile `644a89784316` to generate `fault_run_hardened.json` (2026-10-22 17:39:25 UTC), `replay_evaluation.json`, and `duo_evidence.json`.

3. **Stage Ledger & Receipt Sealing (`372ef5f9` / `895299b` on `main`):**
   - The commit on `main` where the local 9-stage ledger reconciliation was executed (2026-10-22 17:41:54–17:45:30 UTC) and the cryptographic evidence receipt was sealed (`evidence_receipt.json`, 2026-10-23 03:44:01 UTC).
   - Because the baseline incident was captured on commit `b063a91b` while the receipt was generated on `372ef5f9`, the receipt generator detects this difference and explicitly flags it in `not_established`: `"Dossier commit SHA (b063a91b) differs from current HEAD (372ef5f9)."`.

4. **Reference Production Deployment Pipeline (`2967640493` on `main`):**
   - Pipeline ID: [2967640493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2967640493)
   - Commit SHA: `275c598ce2d128aa1107bc9b28c36c9572065ddb`
   - Execution Window: `2026-10-20T13:12:30Z` to `2026-10-20T13:19:09Z` (UTC)
   - Status: Success (verified Bandit AST security scan and Cloud Run candidate deploy stage record).

5. **GitLab SaaS CI Pipeline Run (`2977803091` on `main`):**
   - Pipeline ID: [2977803091](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2977803091)
   - Commit SHA: `e5a9752ba63115d6744a7996f0565272b2804762`
   - Execution Window: `2026-10-22T18:00:55Z` to `2026-10-22T18:08:00Z` (UTC)
   - Built the multi-stage container image (`sha256:7cf1e09f...`) and executed audit job [17392416795](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/jobs/17392416795).

6. **Recent Verified CI Pipeline Runs:**
   - **`main` Pipeline [2979433516](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2979433516):**
     - Execution Window: `2026-10-23T04:06:14Z` to `2026-10-23T04:14:56Z` (UTC)
     - Commit SHA: `9ed64d69aec025d449b19ee5a9da5a57c46f4060`
     - Final Status: **Success / Manual** (All 13 active CI jobs passed: plan, create, configure, verify, secure, package, pages, release, monitor, govern; manual promotion gate pending human sign-off).
   - **MR !3 Pipeline [2979434153](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2979434153):**
     - Execution Window: `2026-10-23T04:06:21Z` to `2026-10-23T04:12:38Z` (UTC)
     - Commit SHA: `eafbb6975b7e4019952fc3520d5ce32f556f9650`
     - Final Status: **Success / Manual** (All 10 active CI jobs passed; manual promotion gate pending human sign-off).

---

## 2. Per-File Provenance & Generation Metadata

| Artifact File | Generating Stage | Commit SHA | Source Pipeline / Execution Context | Generation Time (UTC) | Verification Status & Notes |
|---|---|---|---|---|---|
| `issue.json` | `plan` | `b063a91b` | Local run (pipeline not recorded) | 2026-10-22 16:46:39 | Incident Work Item [#42](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/42) tracking production SLA breach. |
| `incident_dossier.json` | `plan` | `b063a91b` | Local run (pipeline not recorded) | 2026-10-22 17:44:02 | Structured incident dossier with sanitized telemetry and `git bisect` culprit identification. |
| `duo_run.json` | `create` | N/A (Session) | GitLab Duo Agent Platform / CI Job 17391324956 | 2026-10-22 16:46:39 | Duo Flow [Session 9909079](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079) execution record (`claude_sonnet_5_5_vertex`, status: `COMPLETED`). |
| `duo_evidence.json` | `create` | `f8aa9d98` | Local run (pipeline not recorded; verified against MR !3) | 2026-10-22 17:41:54 | Detection record verifying Duo service account commit and MR [!3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) metadata. |
| `diagnosis_report.json` | `create` | `b063a91b` | Local run (pipeline not recorded) | 2026-10-22 17:41:54 | Static AST inspection pinpointing missing timeout at `app/clients/shipping_client.py`. |
| `fault_config.json` | `configure` | N/A | Local run (pipeline not recorded) | 2026-10-22 17:44:02 | Network chaos topology & latency toxic configuration (canonical hash `644a89784316`). |
| `fault_run_baseline.json` | `verify` | `b063a91b` | Local run (pipeline not recorded) | 2026-10-22 17:38:19 | 5 baseline probes under active fault: 100% SLA breaches (mean 4,212.32 ms, p95 4,349.98 ms). |
| `fault_run_hardened.json` | `verify` | `f8aa9d98` | Local run (pipeline not recorded) | 2026-10-22 17:39:25 | 20 candidate probes under identical fault: 0% SLA breaches (mean 825.56 ms, p95 1,472.12 ms). |
| `replay_evaluation.json` | `verify` | `b063a91b` vs `f8aa9d98` | Local run (pipeline not recorded) | 2026-10-22 17:42:06 | Replay proof confirming identical fault hash `644a89784316`, Phase A timeout, and Phase B breaker trip. |
| `bandit_security_report.json` | `secure` | `275c598c` | Pipeline [2967640493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2967640493) | 2026-10-20 13:15:58 | Static AST scan confirming zero high/medium security weaknesses or credential leaks. |
| `image_digest.txt` | `package` | `e5a9752b` | Pipeline [2977803091](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2977803091) (`package:container_build`) | 2026-10-22 18:04:12 | Immutable distroless container image digest: `sha256:7cf1e09f5f4e78c8d0e00032e1236924950607cbc85a9f9cd8cdac37a965da79`. |
| `release.json` | `release` | `275c598c` | Pipeline [2967640493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2967640493) | 2026-10-20 13:17:54 | Deployment status: `SKIPPED_NO_GCP_CREDENTIALS` (unestablished in sample CI runner context). |
| `monitor.json` | `monitor` | `372ef5f9` | Local run (pipeline not recorded) | 2026-10-22 17:44:53 | Telemetry probe validation confirming `/health`, `/ready`, and Prometheus `/metrics` availability. |
| `risk_classification.json` | `govern` | `372ef5f9` | Local run (pipeline not recorded) | 2026-10-22 17:45:30 | Supervised Autonomy policy gate: classified as `MEDIUM` risk tier, requiring human outcome review. |
| `stage_ledger.json` | All (1–9) | `372ef5f9` | Local run (pipeline not recorded) | 2026-10-22 17:45:30 | Aggregated 9-stage empirical ledger recording atomic status and SHA-256 artifact hashes. |
| `stage_ledger_*.json` | Stages 1–9 | `372ef5f9` | Local run (pipeline not recorded) | 2026-10-22 17:41:54–17:45:30 | Individual per-stage ledger fragments recorded atomically during pipeline execution. |
| `evidence_receipt.json` | `govern` | `372ef5f9` | Local run (sealed locally 2026-10-23 03:44 UTC; not an artifact of job 17392416795) | 2026-10-23 03:44:01 | Tamper-evident cryptographic receipt signed with SHA-256 seal; records 2 `not_established` items. |
| `EVIDENCE_RECEIPT.md` | `govern` | `372ef5f9` | Local run (sealed locally 2026-10-23 03:44 UTC; not an artifact of job 17392416795) | 2026-10-23 03:44:01 | Human-readable rendering of the locally sealed evidence receipt. |
| `live_verification.json` | `observe` | N/A | Local run (pipeline not recorded; verify_live.py probe against Cloud Run deployment) | 2026-10-20 13:54:17 | Probe of live Cloud Run production deployment (`faultforge-checkout-00002-kpl`), confirming HTTP 200. |

---

## 3. Audit Verification Rules

- All artifacts in this directory are static snapshots reflecting verified runs and are tracked in git for offline verification.
- In active CI/CD pipeline executions, new receipts and ledgers are generated dynamically into `reports/` and retained as CI job artifacts.
- To audit the claims in these reports against the codebase and documentation, run:
  ```bash
  python scripts/truth_audit.py --final-audit
  python scripts/check_readme_claims.py --samples
  ```
