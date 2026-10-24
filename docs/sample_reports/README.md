# FaultForge Verified CI Sample Reports

These sample reports document the complete empirical evidence lifecycle of FaultForge: incident reproduction, autonomous GitLab Duo Healer remediation, exact-fault replay verification, and GitLab CI/CD pipeline execution.

---

## 1. Commit SHA & Multi-Stage Provenance Architecture

> **Commit Provenance Note:** All sample evidence in `docs/sample_reports/` was generated during CI Pipeline [#2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) running on commit `36c677fb8cc30f2cb1e036bca8ed0b9bcfe7426f` (evaluating candidate commit `36c677fb8cc30f2cb1e036bca8ed0b9bcfe7426f` with merged Duo resilience fix against baseline `4ec3a5ad7fd0cc635d9546acf6974b83f7a57054`). The repository submission HEAD is a later commit incorporating post-pipeline documentation, packaging, and truth audit verification tooling.

All artifacts in this directory were generated during the execution of **GitLab CI Pipeline [#2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115)** on the `main` branch, or reflect reference pipelines:

1. **Active CI Production Pipeline ([#2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) on `main`):**
   - Commit SHA: [`36c677fb8cc30f2cb1e036bca8ed0b9bcfe7426f`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/36c677fb8cc30f2cb1e036bca8ed0b9bcfe7426f)
   - Pipeline Execution Window: `2026-10-24T09:41:33Z` to `2026-10-24T09:51:11Z`
   - Automated Jobs Completed: 14 / 14 passed (100% green, including `secure:gitleaks`); human promotion gate held at `when: manual` per Supervised Autonomy policy.
   - Cloud Run Deployment: Candidate revision `faultforge-checkout-00050-keq` deployed to Google Cloud Run staging ([`https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app`](https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app)) with verified clean 90% production (`faultforge-checkout-00002-kpl`) / 10% canary traffic split.
   - Cryptographic Seal: `4a58ba4daec1bd1313051b8b054f27bb9681da87af1878481a686f32ce8cc2d3`
   - App Tree Parity: `replay_tree_sha` (`5bd23d542337f74dff3320fdd8d7909c17d57e27`) matches `deployed_tree_sha` (`5bd23d542337f74dff3320fdd8d7909c17d57e27`) identically (`app_tree_matches_deployed: true`).

2. **Evaluated Candidate Resilience Patch ([MR !3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) on `fix/resilience-shipping-timeout`):**
   - Commit SHA: [`36c677fb8cc30f2cb1e036bca8ed0b9bcfe7426f`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/36c677fb8cc30f2cb1e036bca8ed0b9bcfe7426f) (evaluated candidate on main with Duo fix; origin MR authored by Duo service account `f8aa9d98` and `d372014`)
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
| `issue.json` | `plan` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`plan:incident_tracking`, Job 17436543215) | 2026-10-24 09:41:57 | Incident Work Item [#62](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/62) tracking production SLA breach (refs root incident #42). |
| `incident_dossier.json` | `create` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`create:duo_remediation_mr`, Job 17436543216) | 2026-10-24 09:42:57 | Structured incident dossier with sanitized telemetry and `git bisect` culprit identification (`974035c`). |
| `duo_run.json` | `create` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`create:duo_remediation_mr`, Job 17436543216) | 2026-10-24 09:42:57 | Autonomous Duo Healer execution record confirming agent session 9909079 and MR !3. |
| `duo_evidence.json` | `create` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`create:duo_remediation_mr`, Job 17436543216) | 2026-10-24 09:42:57 | Duo provenance evidence linking MR !3, session 9909079, commits `f8aa9d98` and `d372014`. |
| `diagnosis_report.json` | `create` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`create:duo_remediation_mr`, Job 17436543216) | 2026-10-24 09:42:57 | Automated bisection diagnosis identifying culprit commit `974035c` removing 0.8s timeout. |
| `fault_config.json` | `configure` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`configure:chaos_topology`, Job 17436543217) | 2026-10-24 09:43:25 | Toxiproxy configuration payload for 3500ms downstream latency injection on port 8082. |
| `fault_run_baseline.json` | `verify` | `4ec3a5ad` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`create:duo_remediation_mr`, Job 17436543216) | 2026-10-24 09:42:51 | 5 baseline probes under active fault: 100% SLA breaches (mean 3572.47 ms, p95 3678.92 ms). |
| `fault_run_hardened.json` | `verify` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`verify:exact_fault_replay_proof`, Job 17436543219) | 2026-10-24 09:44:11 | 20 candidate probes under identical fault: 0% SLA breaches (mean 488.20 ms, p95 814.05 ms). |
| `replay_evaluation.json` | `verify` | `4ec3a5ad` vs `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`verify:exact_fault_replay_proof`, Job 17436543219) | 2026-10-24 09:44:16 | Replay proof confirming identical fault hash `644a89784316`, Phase A timeout, and Phase B breaker trip. |
| `replay_tree_sha.txt` | `verify` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`verify:exact_fault_replay_proof`, Job 17436543219) | 2026-10-24 09:44:16 | Replay git tree SHA for `app/` (`5bd23d542337f74dff3320fdd8d7909c17d57e27`). |
| `bandit_security_report.json` | `secure` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`secure:sast_and_secret_scan`, Job 17436543222) | 2026-10-24 09:44:52 | Static AST security audit confirming zero high/medium security weaknesses or credential leaks. |
| `deployed_tree_sha.txt` | `package` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`package:container_build`, Job 17436543224) | 2026-10-24 09:48:39 | Deployed git tree SHA for `app/` (`5bd23d542337f74dff3320fdd8d7909c17d57e27`). |
| `image_digest.txt` | `package` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`package:container_build`, Job 17436543224) | 2026-10-24 09:48:39 | Immutable container image digest built and pushed to GitLab Container Registry. |
| `release.json` | `release` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`release:cloudrun_candidate_deploy`, Job 17436543226) | 2026-10-24 09:50:03 | Deployment status: `STAGED`, revision `faultforge-checkout-00050-keq` deployed to Cloud Run with clean 90/10 canary split. |
| `live_verification.json` | `release` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`release:cloudrun_candidate_deploy`, Job 17436543226) | 2026-10-24 09:50:02 | Live Cloud Run candidate probe confirming clean 90% production (`faultforge-checkout-00002-kpl`) / 10% canary traffic split verified. |
| `monitor.json` | `monitor` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`monitor:telemetry_probes`, Job 17436543227) | 2026-10-24 09:50:32 | Telemetry probe validation confirming `/health`, `/ready`, and Prometheus `/metrics` availability. |
| `risk_classification.json` | `govern` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`govern:audit_receipt_and_gate`, Job 17436543228) | 2026-10-24 09:51:11 | Supervised Autonomy policy gate: classified as `MEDIUM` risk tier, requiring human outcome review. |
| `stage_ledger.json` | All (1–9) | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`govern:audit_receipt_and_gate`, Job 17436543228) | 2026-10-24 09:51:11 | Aggregated 9-stage empirical ledger recording atomic status and SHA-256 artifact hashes. |
| `stage_ledger_*.json` | Stages 1–9 | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (Jobs 17436543215–17436543228) | 2026-10-24 09:51:11 | Individual per-stage ledger fragments recorded atomically during pipeline execution. |
| `evidence_receipt.json` | `govern` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`govern:audit_receipt_and_gate`, Job 17436543228) | 2026-10-24 09:51:05 | Tamper-evident cryptographic receipt sealed in CI with SHA-256 `4a58ba4daec1bd1313051b8b054f27bb9681da87af1878481a686f32ce8cc2d3`. |
| `EVIDENCE_RECEIPT.md` | `govern` | `36c677fb` | Pipeline [2984259115](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115) (`govern:audit_receipt_and_gate`, Job 17436543228) | 2026-10-24 09:51:11 | Human-readable rendering of the sealed evidence receipt from CI Job 17436543228. |

---

## 3. Audit Verification Rules

- All artifacts in this directory are static snapshots reflecting verified CI runs and are tracked in git for offline verification.
- In active CI/CD pipeline executions, new receipts and ledgers are generated dynamically into `reports/` and retained as CI job artifacts.
- To audit the claims in these reports against the codebase and documentation, run:
  ```bash
  python scripts/truth_audit.py --final-audit
  python scripts/check_readme_claims.py --samples
  ```
