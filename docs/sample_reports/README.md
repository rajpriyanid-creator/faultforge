# FaultForge Verified CI Sample Reports

These sample reports document the complete empirical evidence lifecycle of FaultForge: incident reproduction, autonomous GitLab Duo Healer remediation, exact-fault replay verification, and GitLab CI/CD pipeline execution.

---

## 1. Commit SHA & Multi-Stage Provenance Architecture

> **Commit Provenance Note:** All sample evidence in `docs/sample_reports/` was generated during CI Pipeline [#2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) running on commit `57757a3d0dcdd97a83009c0966a9ca3ad46378bf` (evaluating candidate commit `57757a3d0dcdd97a83009c0966a9ca3ad46378bf` with merged Duo resilience fix against baseline `4ec3a5ad7fd0cc635d9546acf6974b83f7a57054`). The repository submission HEAD is a later commit incorporating post-pipeline documentation, packaging, and truth audit verification tooling.

All artifacts in this directory were generated during the execution of **GitLab CI Pipeline [#2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378)** on the `main` branch, or reflect reference pipelines:

1. **Active CI Production Pipeline ([#2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) on `main`):**
   - Commit SHA: [`57757a3d0dcdd97a83009c0966a9ca3ad46378bf`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/57757a3d0dcdd97a83009c0966a9ca3ad46378bf)
   - Pipeline Execution Window: `2026-10-24T12:08:48Z` to `2026-10-24T12:16:14Z`
   - Automated Jobs Completed: 14 / 14 passed (100% green, including `secure:gitleaks`); human promotion gate held at `when: manual` per Supervised Autonomy policy.
   - Cloud Run Deployment: Candidate revision `faultforge-checkout-00062-juq` deployed to Google Cloud Run staging ([`https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app`](https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app)) with verified clean 90% production (`faultforge-checkout-00002-kpl`) / 10% canary traffic split.
   - Cryptographic Seal: `aa514c463da7fa3f24dc071733f1702e7653b94e6febf0c9915a42c221b9c78d`
   - App Tree Parity: `replay_tree_sha` (`d77c1ee7399956d358c1099bca4bc72fde1be5eb`) matches `deployed_tree_sha` (`d77c1ee7399956d358c1099bca4bc72fde1be5eb`) identically (`app_tree_matches_deployed: true`).

2. **Evaluated Candidate Resilience Patch ([MR !3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) on `fix/resilience-shipping-timeout`):**
   - Commit SHA: [`57757a3d0dcdd97a83009c0966a9ca3ad46378bf`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/57757a3d0dcdd97a83009c0966a9ca3ad46378bf) (evaluated candidate on main with Duo fix; origin MR authored by Duo service account `f8aa9d98` and `d372014`)
   - Baseline Commit SHA: [`4ec3a5ad7fd0cc635d9546acf6974b83f7a57054`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/4ec3a5ad7fd0cc635d9546acf6974b83f7a57054) (pinned tag `baseline-v0.1.0`, annotated tag object `578689ad048f3bfdff9754dcd391e33c5f73b38e`)
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
| `issue.json` | `plan` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`plan:incident_tracking`, Job 17437653504) | 2026-10-24 12:09:08 | Incident Work Item [#62](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/62) tracking production SLA breach (refs root incident #42). |
| `incident_dossier.json` | `create` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`create:duo_remediation_mr`, Job 17437653505) | 2026-10-24 12:10:10 | Structured incident dossier with sanitized telemetry and `git bisect` culprit identification (`974035c`). |
| `duo_run.json` | `create` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`create:duo_remediation_mr`, Job 17437653505) | 2026-10-24 12:10:10 | Autonomous Duo Healer execution record confirming agent session 9909079 and MR !3. |
| `duo_evidence.json` | `create` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`create:duo_remediation_mr`, Job 17437653505) | 2026-10-24 12:10:10 | Duo provenance evidence linking MR !3, session 9909079, commits `f8aa9d98` and `d372014`. |
| `diagnosis_report.json` | `create` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`create:duo_remediation_mr`, Job 17437653505) | 2026-10-24 12:10:10 | Automated bisection diagnosis identifying culprit commit `974035c` removing 0.8s timeout. |
| `fault_config.json` | `configure` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`configure:chaos_topology`, Job 17437653506) | 2026-10-24 12:10:35 | Toxiproxy configuration payload for 3500ms downstream latency injection on port 8082. |
| `fault_run_baseline.json` | `verify` | `4ec3a5ad` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`create:duo_remediation_mr`, Job 17437653505) | 2026-10-24 12:10:06 | 5 baseline probes under active fault: 100% SLA breaches (mean 3585.40 ms, p95 3757.09 ms). |
| `fault_run_hardened.json` | `verify` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`verify:exact_fault_replay_proof`, Job 17437653508) | 2026-10-24 12:11:30 | 20 candidate probes under identical fault: 0% SLA breaches (mean 489.66 ms, p95 817.02 ms). |
| `replay_evaluation.json` | `verify` | `4ec3a5ad` vs `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`verify:exact_fault_replay_proof`, Job 17437653508) | 2026-10-24 12:11:30 | Replay proof confirming identical fault hash `644a89784316`, Phase A timeout, and Phase B breaker trip. |
| `replay_tree_sha.txt` | `verify` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`verify:exact_fault_replay_proof`, Job 17437653508) | 2026-10-24 12:11:30 | Replay git tree SHA for `app/` (`d77c1ee7399956d358c1099bca4bc72fde1be5eb`). |
| `bandit_security_report.json` | `secure` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`secure:sast_and_secret_scan`, Job 17437653511) | 2026-10-24 12:12:05 | Static AST security audit confirming zero high/medium security weaknesses or credential leaks. |
| `deployed_tree_sha.txt` | `package` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`package:container_build`, Job 17437653513) | 2026-10-24 12:13:41 | Deployed git tree SHA for `app/` (`d77c1ee7399956d358c1099bca4bc72fde1be5eb`). |
| `image_digest.txt` | `package` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`package:container_build`, Job 17437653513) | 2026-10-24 12:13:41 | Immutable container image digest built and pushed to GitLab Container Registry. |
| `release.json` | `release` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`release:cloudrun_candidate_deploy`, Job 17437653515) | 2026-10-24 12:15:00 | Deployment status: `STAGED`, revision `faultforge-checkout-00062-juq` deployed to Cloud Run with clean 90/10 canary split. |
| `live_verification.json` | `release` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`release:cloudrun_candidate_deploy`, Job 17437653515) | 2026-10-24 12:14:59 | Live Cloud Run candidate probe confirming clean 90% production (`faultforge-checkout-00002-kpl`) / 10% canary traffic split verified. |
| `monitor.json` | `monitor` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`monitor:telemetry_probes`, Job 17437653516) | 2026-10-24 12:15:28 | Telemetry probe validation confirming `/health`, `/ready`, and Prometheus `/metrics` availability. |
| `risk_classification.json` | `govern` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`govern:audit_receipt_and_gate`, Job 17437653517) | 2026-10-24 12:16:06 | Supervised Autonomy policy gate: classified as `MEDIUM` risk tier, requiring human outcome review. |
| `stage_ledger.json` | All (1–9) | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`govern:audit_receipt_and_gate`, Job 17437653517) | 2026-10-24 12:16:06 | Aggregated 9-stage empirical ledger recording atomic status and SHA-256 artifact hashes. |
| `stage_ledger_*.json` | Stages 1–9 | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (Jobs 17437653504–17437653517) | 2026-10-24 12:16:06 | Individual per-stage ledger fragments recorded atomically during pipeline execution. |
| `evidence_receipt.json` | 14,949 | `e3cc9efdb5f2cafee6506e31c74bf9c1e10f30571a1ee15bec89333bd04a71d0` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`govern:audit_receipt_and_gate`, Job 17437653517) | 2026-10-24 12:16:06 | Tamper-evident cryptographic receipt sealed in CI with SHA-256 `aa514c463da7fa3f24dc071733f1702e7653b94e6febf0c9915a42c221b9c78d`. |
| `EVIDENCE_RECEIPT.md` | `govern` | `57757a3d` | Pipeline [2984485378](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984485378) (`govern:audit_receipt_and_gate`, Job 17437653517) | 2026-10-24 12:16:06 | Human-readable rendering of the sealed evidence receipt from CI Job 17437653517. |

---

## 3. Audit Verification Rules

- All artifacts in this directory are static snapshots reflecting verified CI runs and are tracked in git for offline verification.
- In active CI/CD pipeline executions, new receipts and ledgers are generated dynamically into `reports/` and retained as CI job artifacts.
- To audit the claims in these reports against the codebase and documentation, run:
  ```bash
  python scripts/truth_audit.py --final-audit
  python scripts/check_readme_claims.py --samples
  ```
