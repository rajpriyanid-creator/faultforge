# FaultForge Verified CI Sample Reports

These sample reports document the complete empirical evidence lifecycle of FaultForge: incident reproduction, autonomous GitLab Duo Healer remediation, exact-fault replay verification, and GitLab CI/CD pipeline execution.

---

## 1. Commit SHA & Multi-Stage Provenance Architecture

> **Commit Provenance Note:** All sample evidence in `docs/sample_reports/` was generated during CI Pipeline [#2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) running on commit `c5d67cdfd092371194fca081d9105116ee0dbc2e` (evaluating candidate commit `c5d67cdfd092371194fca081d9105116ee0dbc2e` with merged Duo resilience fix against baseline `578689ad048f3bfdff9754dcd391e33c5f73b38e`). The repository submission HEAD is a later commit incorporating post-pipeline documentation, packaging, and truth audit verification tooling.

All artifacts in this directory were generated during the execution of **GitLab CI Pipeline [#2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017)** on the `main` branch, or reflect reference pipelines:

1. **Active CI Production Pipeline ([#2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) on `main`):**
   - Commit SHA: [`c5d67cdfd092371194fca081d9105116ee0dbc2e`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/c5d67cdfd092371194fca081d9105116ee0dbc2e)
   - Pipeline Execution Window: `2026-10-24T08:39:00Z` to `2026-10-24T08:46:13Z`
   - Automated Jobs Completed: 14 / 14 passed (100% green, including `secure:gitleaks`); human promotion gate held at `when: manual` per Supervised Autonomy policy.
   - Cloud Run Deployment: Candidate revision `faultforge-checkout-00046-yeg` deployed to Google Cloud Run staging ([`https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app`](https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app)) with verified clean 90% production (`faultforge-checkout-00002-kpl`) / 10% canary traffic split.
   - Cryptographic Seal: `69fe40c67b5ecd4d8c8c23d07c903f41f62d062a553988df28dd3576b4d65cb0`
   - App Tree Parity: `replay_tree_sha` (`5bd23d542337f74dff3320fdd8d7909c17d57e27`) matches `deployed_tree_sha` (`5bd23d542337f74dff3320fdd8d7909c17d57e27`) identically (`app_tree_matches_deployed: true`).

2. **Evaluated Candidate Resilience Patch ([MR !3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) on `fix/resilience-shipping-timeout`):**
   - Commit SHA: [`c5d67cdfd092371194fca081d9105116ee0dbc2e`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/c5d67cdfd092371194fca081d9105116ee0dbc2e) (evaluated candidate on main with Duo fix; origin MR authored by Duo service account `f8aa9d98` and `d372014`)
   - Baseline Commit SHA: [`578689ad048f3bfdff9754dcd391e33c5f73b38e`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/578689ad048f3bfdff9754dcd391e33c5f73b38e) (pinned tag `baseline-v0.1.0`)
   - Evaluated under identical Toxiproxy fault profile `644a89784316` to generate `fault_run_hardened.json` and `replay_evaluation.json`.

3. **Reference Production Deployment Pipeline ([#2967640493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2967640493) on `main`):**
   - Pipeline ID: [2967640493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2967640493)
   - Execution Window: `2026-10-20T13:12:30Z` to `2026-10-20T13:19:09Z`
   - Initial deployment of reference revision `faultforge-checkout-00002-kpl`.

4. **Reference Test Pipeline ([#2977803091](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2977803091) on `main`):**
   - Pipeline ID: [2977803091](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2977803091)
   - Execution Window: `2026-10-22T18:00:55Z` to `2026-10-22T18:08:00Z`
   - Reference container packaging run.

---

## 2. Per-File Provenance & Generation Metadata

| Artifact File | Generating Stage | Commit SHA | Source Pipeline / Execution Context | Generation Time (UTC) | Verification Status & Notes |
|---|---|---|---|---|---|
| `issue.json` | `plan` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`plan:incident_tracking`, Job 17436072830) | 2026-10-24 08:39:18 | Incident Work Item [#62](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/62) tracking production SLA breach (refs root incident #42). |
| `incident_dossier.json` | `create` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`create:duo_remediation_mr`, Job 17436072831) | 2026-10-24 08:40:16 | Structured incident dossier with sanitized telemetry and `git bisect` culprit identification (`974035c`). |
| `duo_run.json` | `create` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`create:duo_remediation_mr`, Job 17436072831) | 2026-10-24 08:40:16 | Autonomous Duo Healer execution record confirming agent session 9909079 and MR !3. |
| `duo_evidence.json` | `create` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`create:duo_remediation_mr`, Job 17436072831) | 2026-10-24 08:40:16 | Duo provenance evidence linking MR !3, session 9909079, commits `f8aa9d98` and `d372014`. |
| `diagnosis_report.json` | `create` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`create:duo_remediation_mr`, Job 17436072831) | 2026-10-24 08:40:16 | Automated bisection diagnosis identifying culprit commit `974035c` removing 0.8s timeout. |
| `fault_config.json` | `configure` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`configure:chaos_topology`, Job 17436072832) | 2026-10-24 08:40:45 | Toxiproxy configuration payload for 3500ms downstream latency injection on port 8082. |
| `fault_run_baseline.json` | `verify` | `578689ad` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`create:duo_remediation_mr`, Job 17436072831) | 2026-10-24 08:40:15 | 5 baseline probes under active fault: 100% SLA breaches (mean 3652.00 ms, p95 3718.82 ms). |
| `fault_run_hardened.json` | `verify` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`verify:exact_fault_replay_proof`, Job 17436072834) | 2026-10-24 08:41:39 | 20 candidate probes under identical fault: 0% SLA breaches (mean 488.75 ms, p95 815.41 ms). |
| `replay_evaluation.json` | `verify` | `578689ad` vs `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`verify:exact_fault_replay_proof`, Job 17436072834) | 2026-10-24 08:41:39 | Replay proof confirming identical fault hash `644a89784316`, Phase A timeout, and Phase B breaker trip. |
| `replay_tree_sha.txt` | `verify` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`verify:exact_fault_replay_proof`, Job 17436072834) | 2026-10-24 08:41:39 | Replay git tree SHA for `app/` (`5bd23d542337f74dff3320fdd8d7909c17d57e27`). |
| `bandit_security_report.json` | `secure` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`secure:sast_and_secret_scan`, Job 17436072837) | 2026-10-24 08:42:14 | Static AST security audit confirming zero high/medium security weaknesses or credential leaks. |
| `deployed_tree_sha.txt` | `package` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`package:container_build`, Job 17436072839) | 2026-10-24 08:43:44 | Deployed git tree SHA for `app/` (`5bd23d542337f74dff3320fdd8d7909c17d57e27`). |
| `image_digest.txt` | `package` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`package:container_build`, Job 17436072839) | 2026-10-24 08:43:44 | Immutable container image digest built and pushed to GitLab Container Registry. |
| `release.json` | `release` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`release:cloudrun_candidate_deploy`, Job 17436072841) | 2026-10-24 08:45:02 | Deployment status: `STAGED`, revision `faultforge-checkout-00046-yeg` deployed to Cloud Run with clean 90/10 canary split. |
| `live_verification.json` | `release` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`release:cloudrun_candidate_deploy`, Job 17436072841) | 2026-10-24 08:45:01 | Live Cloud Run candidate probe confirming clean 90% production (`faultforge-checkout-00002-kpl`) / 10% canary traffic split verified. |
| `monitor.json` | `monitor` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`monitor:telemetry_probes`, Job 17436072842) | 2026-10-24 08:45:30 | Telemetry probe validation confirming `/health`, `/ready`, and Prometheus `/metrics` availability. |
| `risk_classification.json` | `govern` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`govern:audit_receipt_and_gate`, Job 17436072843) | 2026-10-24 08:46:07 | Supervised Autonomy policy gate: classified as `MEDIUM` risk tier, requiring human outcome review. |
| `stage_ledger.json` | All (1–9) | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`govern:audit_receipt_and_gate`, Job 17436072843) | 2026-10-24 08:46:07 | Aggregated 9-stage empirical ledger recording atomic status and SHA-256 artifact hashes. |
| `stage_ledger_*.json` | Stages 1–9 | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (Jobs 17436072830–17436072843) | 2026-10-24 08:46:07 | Individual per-stage ledger fragments recorded atomically during pipeline execution. |
| `evidence_receipt.json` | `govern` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`govern:audit_receipt_and_gate`, Job 17436072843) | 2026-10-24 08:46:07 | Tamper-evident cryptographic receipt sealed in CI with SHA-256 `69fe40c67b5ecd4d8c8c23d07c903f41f62d062a553988df28dd3576b4d65cb0`. |
| `EVIDENCE_RECEIPT.md` | `govern` | `c5d67cdf` | Pipeline [2984172017](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017) (`govern:audit_receipt_and_gate`, Job 17436072843) | 2026-10-24 08:46:07 | Human-readable rendering of the sealed evidence receipt from CI Job 17436072843. |

---

## 3. Audit Verification Rules

- All artifacts in this directory are static snapshots reflecting verified CI runs and are tracked in git for offline verification.
- In active CI/CD pipeline executions, new receipts and ledgers are generated dynamically into `reports/` and retained as CI job artifacts.
- To audit the claims in these reports against the codebase and documentation, run:
  ```bash
  python scripts/truth_audit.py --final-audit
  python scripts/check_readme_claims.py --samples
  ```
