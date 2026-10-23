# FaultForge Verified CI Sample Reports

These sample reports document the complete empirical evidence lifecycle of FaultForge: incident reproduction, autonomous GitLab Duo Healer remediation, exact-fault replay verification, and GitLab CI/CD pipeline execution.

---

## 1. Commit SHA & Multi-Stage Provenance Architecture

All artifacts in this directory were generated during the execution of **GitLab CI Pipeline [#2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651)** on the `main` branch, or reflect reference pipelines:

1. **Active CI Production Pipeline ([#2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) on `main`):**
   - Commit SHA: [`34eb7ebd520feeb83706c3b853589c195cbe953f`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/34eb7ebd520feeb83706c3b853589c195cbe953f)
   - Pipeline Execution Window: `2026-10-23T16:00:22Z` to `2026-10-23T16:10:14Z`
   - Automated Jobs Completed: 13 / 13 passed (100% green); human promotion gate held at `when: manual` per Supervised Autonomy policy.
   - Cloud Run Deployment: Candidate revision `faultforge-checkout-00022-dej` deployed to Google Cloud Run staging ([`https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app`](https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app)) with verified 10% canary traffic split.

2. **Evaluated Candidate Resilience Patch ([MR !3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) on `fix/resilience-shipping-timeout`):**
   - Commit SHA: [`d3720143e15c85f519a7624859541d1ce997f1a0`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/d3720143e15c85f519a7624859541d1ce997f1a0) (MR source commit `f8aa9d98`)
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
| `issue.json` | `plan` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`plan:incident_tracking`, Job 17422097711) | 2026-10-23 16:00:43 | Incident Work Item [#48](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/48) tracking production SLA breach. |
| `incident_dossier.json` | `create` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`create:duo_remediation_mr`, Job 17422097712) | 2026-10-23 16:01:45 | Structured incident dossier with sanitized telemetry and `git bisect` culprit identification (`974035c`). |
| `duo_run.json` | `create` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`create:duo_remediation_mr`, Job 17422097712) | 2026-10-23 16:01:45 | Duo Flow [Session 9909079](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079) execution record (`status: COMPLETED`). |
| `duo_evidence.json` | `create` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`create:duo_remediation_mr`, Job 17422097712) | 2026-10-23 16:01:46 | Detection record verifying Duo service account commit and MR [!3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) metadata. |
| `diagnosis_report.json` | `create` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`create:duo_remediation_mr`, Job 17422097712) | 2026-10-23 16:01:45 | Static AST inspection pinpointing missing timeout at `app/clients/shipping_client.py`. |
| `fault_config.json` | `configure` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`configure:chaos_topology`, Job 17422097713) | 2026-10-23 16:02:14 | Network chaos topology & latency toxic configuration (canonical hash `644a89784316`). |
| `fault_run_baseline.json` | `verify` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`verify:exact_fault_replay_proof`, Job 17422097715) | 2026-10-23 16:01:44 | 5 baseline probes under active fault: 100% SLA breaches (mean 3478.57 ms, p95 3749.62 ms). |
| `fault_run_hardened.json` | `verify` | `d3720143` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`verify:exact_fault_replay_proof`, Job 17422097715) | 2026-10-23 16:03:09 | 20 candidate probes under identical fault: 0% SLA breaches (mean 484.36 ms, p95 806.83 ms). |
| `replay_evaluation.json` | `verify` | `34eb7ebd` vs `d3720143` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`verify:exact_fault_replay_proof`, Job 17422097715) | 2026-10-23 16:03:10 | Replay proof confirming identical fault hash `644a89784316`, Phase A timeout, and Phase B breaker trip. |
| `bandit_security_report.json` | `secure` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`secure:sast_and_secret_scan`, Job 17422097718) | 2026-10-23 16:03:37 | Static AST security audit confirming zero high/medium security weaknesses or credential leaks. |
| `image_digest.txt` | `package` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`package:container_build`, Job 17422097719) | 2026-10-23 16:07:25 | Immutable distroless container image digest built and pushed to Google Artifact Registry. |
| `release.json` | `release` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`release:cloudrun_candidate_deploy`, Job 17422097721) | 2026-10-23 16:08:55 | Deployment status: `STAGED`, revision `faultforge-checkout-00022-dej` deployed to Cloud Run with 10% canary split. |
| `live_verification.json` | `release` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`release:cloudrun_candidate_deploy`, Job 17422097721) | 2026-10-23 16:08:49 | Live Cloud Run candidate probe confirming 10% canary traffic split verified. |
| `monitor.json` | `monitor` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`monitor:telemetry_probes`, Job 17422097722) | 2026-10-23 16:09:25 | Telemetry probe validation confirming `/health`, `/ready`, and Prometheus `/metrics` availability. |
| `risk_classification.json` | `govern` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`govern:audit_receipt_and_gate`, Job 17422097723) | 2026-10-23 16:10:06 | Supervised Autonomy policy gate: classified as `MEDIUM` risk tier, requiring human outcome review. |
| `stage_ledger.json` | All (1–9) | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`govern:audit_receipt_and_gate`, Job 17422097723) | 2026-10-23 16:10:06 | Aggregated 9-stage empirical ledger recording atomic status and SHA-256 artifact hashes. |
| `stage_ledger_*.json` | Stages 1–9 | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (Jobs 17422097711–17422097723) | 2026-10-23 16:10:06 | Individual per-stage ledger fragments recorded atomically during pipeline execution. |
| `evidence_receipt.json` | `govern` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`govern:audit_receipt_and_gate`, Job 17422097723) | 2026-10-23 16:10:06 | Tamper-evident cryptographic receipt sealed in CI with SHA-256 `bb345ac430daf1b02c4cf2bfce7ed942591c7aa047656d14d191c327bc075d58`. |
| `EVIDENCE_RECEIPT.md` | `govern` | `34eb7ebd` | Pipeline [2981969651](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651) (`govern:audit_receipt_and_gate`, Job 17422097723) | 2026-10-23 16:10:06 | Human-readable rendering of the sealed evidence receipt from CI Job 17422097723. |

---

## 3. Audit Verification Rules

- All artifacts in this directory are static snapshots reflecting verified CI runs and are tracked in git for offline verification.
- In active CI/CD pipeline executions, new receipts and ledgers are generated dynamically into `reports/` and retained as CI job artifacts.
- To audit the claims in these reports against the codebase and documentation, run:
  ```bash
  python scripts/truth_audit.py --final-audit
  python scripts/check_readme_claims.py --samples
  ```
