# FaultForge Verified CI Sample Reports

These sample reports document the complete empirical evidence lifecycle of FaultForge: incident reproduction, autonomous GitLab Duo Healer remediation, exact-fault replay verification, and GitLab CI/CD pipeline execution.

---

## 1. Commit SHA & Multi-Stage Provenance Architecture

> **Commit Provenance Note:** All sample evidence in `docs/sample_reports/` was generated during CI Pipeline [#2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) running on commit `d75de80a4242637bdf354f3b0631f4762c2f1f0e` (evaluating candidate commit `d75de80a4242637bdf354f3b0631f4762c2f1f0e` with merged Duo resilience fix against baseline `4ec3a5ad7fd0cc635d9546acf6974b83f7a57054`). While the repository submission archive HEAD is `7aca1e5` (and subsequent documentation/audit polish commits), the application code tree `app/` is 100% byte-for-byte identical (tree SHA `de7c0b1cc7d6b7edb90c6b3041b10885ea702492`).

All artifacts in this directory were generated during the execution of **GitLab CI Pipeline [#2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851)** on the `main` branch, or reflect reference pipelines:

1. **Active CI Production Pipeline ([#2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) on `main`):**
   - Commit SHA: [`d75de80a4242637bdf354f3b0631f4762c2f1f0e`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/d75de80a4242637bdf354f3b0631f4762c2f1f0e)
   - Pipeline Execution Window: `2026-10-24T13:23:46Z` to `2026-10-24T13:31:30Z`
   - Automated Jobs Completed: 14 / 14 passed (100% green, including `secure:gitleaks`); human promotion gate held at `when: manual` per Supervised Autonomy policy.
   - Cloud Run Deployment: Candidate revision `faultforge-checkout-00068-gaw` deployed to Google Cloud Run staging ([`https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app`](https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app)) with verified clean 90% production (`faultforge-checkout-00002-kpl`) / 10% canary traffic split.
   - Cryptographic Seal: `c62ee3b35d29dcc013f4d70ab6a230892886911c83674f9b91b02a2d6846de23`
   - App Tree Parity: `replay_tree_sha` (`de7c0b1cc7d6b7edb90c6b3041b10885ea702492`) matches `deployed_tree_sha` (`de7c0b1cc7d6b7edb90c6b3041b10885ea702492`) identically (`app_tree_matches_deployed: true`).

2. **Evaluated Candidate Resilience Patch ([MR !3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) on `fix/resilience-shipping-timeout`):**
   - Commit SHA: [`d75de80a4242637bdf354f3b0631f4762c2f1f0e`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/d75de80a4242637bdf354f3b0631f4762c2f1f0e) (evaluated candidate on main with Duo fix; origin MR authored by Duo service account `f8aa9d98` and `d372014`)
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
| `issue.json` | `plan` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`plan:incident_tracking`, Job 17438210902) | 2026-10-24 13:24:12 | Incident Work Item [#62](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/62) tracking production SLA breach (refs root incident #42). |
| `incident_dossier.json` | `create` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`create:duo_remediation_mr`, Job 17438210903) | 2026-10-24 13:25:13 | Structured incident dossier with sanitized telemetry and `git bisect` culprit identification (`974035c`). |
| `duo_run.json` | `create` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`create:duo_remediation_mr`, Job 17438210903) | 2026-10-24 13:25:13 | Autonomous Duo Healer execution record confirming agent session 9909079 and MR !3. |
| `duo_evidence.json` | `create` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`create:duo_remediation_mr`, Job 17438210903) | 2026-10-24 13:25:13 | Duo provenance evidence linking MR !3, session 9909079, commits `f8aa9d98` and `d372014`. |
| `diagnosis_report.json` | `create` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`create:duo_remediation_mr`, Job 17438210903) | 2026-10-24 13:25:13 | Automated bisection diagnosis identifying culprit commit `974035c` removing 0.8s timeout. |
| `fault_config.json` | `configure` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`configure:chaos_topology`, Job 17438210904) | 2026-10-24 13:25:41 | Toxiproxy configuration payload for 3500ms downstream latency injection on port 8082. |
| `fault_run_baseline.json` | `verify` | `4ec3a5ad` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`create:duo_remediation_mr`, Job 17438210903) | 2026-10-24 13:25:07 | 5 baseline probes under active fault: 100% SLA breaches (mean 3637.98 ms, p95 3699.48 ms). |
| `fault_run_hardened.json` | `verify` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`verify:exact_fault_replay_proof`, Job 17438210906) | 2026-10-24 13:26:32 | 20 candidate probes under identical fault: 0% SLA breaches (mean 487.92 ms, p95 813.32 ms). |
| `replay_evaluation.json` | `verify` | `4ec3a5ad` vs `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`verify:exact_fault_replay_proof`, Job 17438210906) | 2026-10-24 13:26:37 | Replay proof confirming identical fault hash `644a89784316`, Phase A timeout, and Phase B breaker trip. |
| `replay_tree_sha.txt` | `verify` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`verify:exact_fault_replay_proof`, Job 17438210906) | 2026-10-24 13:26:37 | Replay git tree SHA for `app/` (`de7c0b1cc7d6b7edb90c6b3041b10885ea702492`). |
| `bandit_security_report.json` | `secure` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`secure:sast_and_secret_scan`, Job 17438210909) | 2026-10-24 13:27:11 | Static AST security audit confirming zero high/medium security weaknesses or credential leaks. |
| `deployed_tree_sha.txt` | `package` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`package:container_build`, Job 17438210911) | 2026-10-24 13:28:49 | Deployed git tree SHA for `app/` (`de7c0b1cc7d6b7edb90c6b3041b10885ea702492`). |
| `image_digest.txt` | `package` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`package:container_build`, Job 17438210911) | 2026-10-24 13:28:49 | Immutable container image digest built and pushed to GitLab Container Registry. |
| `release.json` | `release` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`release:cloudrun_candidate_deploy`, Job 17438210912) | 2026-10-24 13:30:05 | Deployment status: `STAGED`, revision `faultforge-checkout-00068-gaw` deployed to Cloud Run with clean 90/10 canary split. |
| `live_verification.json` | `release` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`release:cloudrun_candidate_deploy`, Job 17438210912) | 2026-10-24 13:30:04 | Live Cloud Run candidate probe confirming clean 90% production (`faultforge-checkout-00002-kpl`) / 10% canary traffic split verified. |
| `monitor.json` | `monitor` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`monitor:telemetry_probes`, Job 17438210913) | 2026-10-24 13:30:36 | Telemetry probe validation confirming `/health`, `/ready`, and Prometheus `/metrics` availability. |
| `risk_classification.json` | `govern` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`govern:audit_receipt_and_gate`, Job 17438210914) | 2026-10-24 13:31:14 | Supervised Autonomy policy gate: classified as `MEDIUM` risk tier, requiring human outcome review. |
| `stage_ledger.json` | All (1–9) | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`govern:audit_receipt_and_gate`, Job 17438210914) | 2026-10-24 13:31:14 | Aggregated 9-stage empirical ledger recording atomic status and SHA-256 artifact hashes. |
| `stage_ledger_*.json` | Stages 1–9 | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (Jobs 17438210902–17438210914) | 2026-10-24 13:31:14 | Individual per-stage ledger fragments recorded atomically during pipeline execution. |
| `evidence_receipt.json` | 15,021 | `b740bd6290f4f52ed132a3ce04430b9c445e699119eb557807e46519ed6f99db` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`govern:audit_receipt_and_gate`, Job 17438210914) | 2026-10-24 13:31:14 | Tamper-evident cryptographic receipt sealed in CI with SHA-256 `c62ee3b35d29dcc013f4d70ab6a230892886911c83674f9b91b02a2d6846de23`. |
| `EVIDENCE_RECEIPT.md` | `govern` | `d75de80a` | Pipeline [2984589851](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851) (`govern:audit_receipt_and_gate`, Job 17438210914) | 2026-10-24 13:31:14 | Human-readable rendering of the sealed evidence receipt from CI Job 17438210914. |

---

## 3. Audit Verification Rules

- All artifacts in this directory are static snapshots reflecting verified CI runs and are tracked in git for offline verification.
- In active CI/CD pipeline executions, new receipts and ledgers are generated dynamically into `reports/` and retained as CI job artifacts.
- To audit the claims in these reports against the codebase and documentation, run:
  ```bash
  python scripts/truth_audit.py --final-audit
  python scripts/check_readme_claims.py --samples
  ```
