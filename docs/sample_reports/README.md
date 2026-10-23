# FaultForge Verified CI Sample Reports

These sample reports document the complete empirical evidence lifecycle of FaultForge: incident reproduction, autonomous GitLab Duo Healer remediation, exact-fault replay verification, and GitLab CI/CD pipeline execution.

---

## 1. Commit SHA & Multi-Stage Provenance Architecture

All artifacts in this directory were generated during the execution of **GitLab CI Pipeline [#2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120)** on the `main` branch, or reflect reference pipelines:

1. **Active CI Production Pipeline ([#2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) on `main`):**
   - Commit SHA: [`d64c35d4771113092df8d33a70408a1045ae108e`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/d64c35d4771113092df8d33a70408a1045ae108e)
   - Pipeline Execution Window: `2026-10-23T14:47:30Z` to `2026-10-23T14:55:01Z`
   - Automated Jobs Completed: 13 / 13 passed (100% green); human promotion gate held at `when: manual` per Supervised Autonomy policy.
   - Cloud Run Deployment: Candidate revision `faultforge-checkout-00012-xoc` deployed to Google Cloud Run staging ([`https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app`](https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app)) with verified 10% canary traffic split.

2. **Evaluated Candidate Resilience Patch ([MR !3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) on `fix/resilience-shipping-timeout`):**
   - Commit SHA: [`329404236f9ef37ef66f3f624f1b64b1bda9b509`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/329404236f9ef37ef66f3f624f1b64b1bda9b509) (eval revision `a1702b00`)
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
| `issue.json` | `plan` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`plan:incident_tracking`, Job 17419950457) | 2026-10-23 14:47:48 | Incident Work Item [#42](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/42) tracking production SLA breach. |
| `incident_dossier.json` | `create` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`create:duo_remediation_mr`, Job 17419950461) | 2026-10-23 14:48:49 | Structured incident dossier with sanitized telemetry and `git bisect` culprit identification (`974035c`). |
| `duo_run.json` | `create` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`create:duo_remediation_mr`, Job 17419950461) | 2026-10-23 14:48:49 | Duo Flow [Session 9909079](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079) execution record (`status: COMPLETED`). |
| `duo_evidence.json` | `create` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`create:duo_remediation_mr`, Job 17419950461) | 2026-10-23 14:48:49 | Detection record verifying Duo service account commit and MR [!3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) metadata. |
| `diagnosis_report.json` | `create` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`create:duo_remediation_mr`, Job 17419950461) | 2026-10-23 14:48:49 | Static AST inspection pinpointing missing timeout at `app/clients/shipping_client.py`. |
| `fault_config.json` | `configure` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`configure:chaos_topology`, Job 17419950462) | 2026-10-23 14:49:21 | Network chaos topology & latency toxic configuration (canonical hash `644a89784316`). |
| `fault_run_baseline.json` | `verify` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`verify:exact_fault_replay_proof`, Job 17419950464) | 2026-10-23 14:48:48 | 5 baseline probes under active fault: 100% SLA breaches (mean 3454.97 ms, p95 3541.19 ms). |
| `fault_run_hardened.json` | `verify` | `a1702b00` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`verify:exact_fault_replay_proof`, Job 17419950464) | 2026-10-23 14:50:08 | 20 candidate probes under identical fault: 0% SLA breaches (mean 124.24 ms, p95 817.61 ms). |
| `replay_evaluation.json` | `verify` | `d64c35d4` vs `a1702b00` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`verify:exact_fault_replay_proof`, Job 17419950464) | 2026-10-23 14:50:08 | Replay proof confirming identical fault hash `644a89784316`, Phase A timeout, and Phase B breaker trip. |
| `bandit_security_report.json` | `secure` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`secure:sast_and_secret_scan`, Job 17419950467) | 2026-10-23 14:50:40 | Static AST security audit confirming zero high/medium security weaknesses or credential leaks. |
| `image_digest.txt` | `package` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`package:container_build`, Job 17419950468) | 2026-10-23 14:52:19 | Immutable distroless container image digest built and pushed to Google Artifact Registry. |
| `release.json` | `release` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`release:cloudrun_candidate_deploy`, Job 17419950470) | 2026-10-23 14:53:44 | Deployment status: `STAGED`, revision `faultforge-checkout-00012-xoc` deployed to Cloud Run with 10% canary split. |
| `live_verification.json` | `release` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`release:cloudrun_candidate_deploy`, Job 17419950470) | 2026-10-23 14:53:38 | Live Cloud Run candidate probe confirming HTTP 200 on `/health` and 10% canary traffic split verified. |
| `monitor.json` | `monitor` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`monitor:telemetry_probes`, Job 17419950471) | 2026-10-23 14:54:14 | Telemetry probe validation confirming `/health`, `/ready`, and Prometheus `/metrics` availability. |
| `risk_classification.json` | `govern` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`govern:audit_receipt_and_gate`, Job 17419950472) | 2026-10-23 14:54:54 | Supervised Autonomy policy gate: classified as `MEDIUM` risk tier, requiring human outcome review. |
| `stage_ledger.json` | All (1–9) | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`govern:audit_receipt_and_gate`, Job 17419950472) | 2026-10-23 14:54:54 | Aggregated 9-stage empirical ledger recording atomic status and SHA-256 artifact hashes. |
| `stage_ledger_*.json` | Stages 1–9 | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (Jobs 17419950457–17419950472) | 2026-10-23 14:47:49–14:54:54 | Individual per-stage ledger fragments recorded atomically during pipeline execution. |
| `evidence_receipt.json` | `govern` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`govern:audit_receipt_and_gate`, Job 17419950472) | 2026-10-23 14:54:54 | Tamper-evident cryptographic receipt sealed in CI with SHA-256 `77fcdade74cbb5040bf7301b4bb8c55827e3c15fab3dbae8e679fe18e1ae8a40`. |
| `EVIDENCE_RECEIPT.md` | `govern` | `d64c35d4` | Pipeline [2981670120](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120) (`govern:audit_receipt_and_gate`, Job 17419950472) | 2026-10-23 14:54:54 | Human-readable rendering of the sealed evidence receipt from CI Job 17419950472. |

---

## 3. Audit Verification Rules

- All artifacts in this directory are static snapshots reflecting verified CI runs and are tracked in git for offline verification.
- In active CI/CD pipeline executions, new receipts and ledgers are generated dynamically into `reports/` and retained as CI job artifacts.
- To audit the claims in these reports against the codebase and documentation, run:
  ```bash
  python scripts/truth_audit.py --final-audit
  python scripts/check_readme_claims.py --samples
  ```
