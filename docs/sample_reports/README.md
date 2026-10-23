# FaultForge Verified CI Sample Reports

These sample reports document the complete empirical evidence lifecycle of FaultForge: incident reproduction, autonomous GitLab Duo Healer remediation, exact-fault replay verification, and GitLab CI/CD pipeline execution.

---

## 1. Commit SHA & Multi-Stage Provenance Architecture

All artifacts in this directory were generated during the execution of **GitLab CI Pipeline [#2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493)** on the `main` branch, or reflect reference pipelines:

1. **Active CI Production Pipeline ([#2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) on `main`):**
   - Commit SHA: [`e150fad07a8627fbc5c1535d8fa9081ef9dc3a52`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/e150fad07a8627fbc5c1535d8fa9081ef9dc3a52)
   - Pipeline Execution Window: `2026-10-23T19:05:05Z` to `2026-10-23T19:12:39Z`
   - Automated Jobs Completed: 14 / 14 passed (100% green, including `secure:gitleaks`); human promotion gate held at `when: manual` per Supervised Autonomy policy.
   - Cloud Run Deployment: Candidate revision `faultforge-checkout-00036-pih` deployed to Google Cloud Run staging ([`https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app`](https://candidate---faultforge-checkout-tiottsrikq-uc.a.run.app)) with verified clean 90% production (`faultforge-checkout-00002-kpl`) / 10% canary traffic split.
   - Cryptographic Seal: `1fdf9fae649e620d1f92be6574b9cdb7b62b1a5b707fc6062a3a91797d9eb800`

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
| `issue.json` | `plan` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`plan:incident_tracking`, Job 17426629828) | 2026-10-23 19:05:31 | Incident Work Item [#50](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/50) tracking production SLA breach (refs root incident #42). |
| `incident_dossier.json` | `create` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`create:duo_remediation_mr`, Job 17426629829) | 2026-10-23 19:06:36 | Structured incident dossier with sanitized telemetry and `git bisect` culprit identification (`974035c`). |
| `duo_run.json` | `create` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`create:duo_remediation_mr`, Job 17426629829) | 2026-10-23 19:06:36 | Duo Flow [Session 9909079](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079) execution record (`status: COMPLETED`). |
| `duo_evidence.json` | `create` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`create:duo_remediation_mr`, Job 17426629829) | 2026-10-23 19:06:36 | Detection record verifying Duo service account commit and MR [!3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) metadata. |
| `diagnosis_report.json` | `create` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`create:duo_remediation_mr`, Job 17426629829) | 2026-10-23 19:06:36 | Static AST inspection pinpointing missing timeout at `app/clients/shipping_client.py`. |
| `fault_config.json` | `configure` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`configure:chaos_topology`, Job 17426629830) | 2026-10-23 19:07:05 | Network chaos topology & latency toxic configuration (canonical hash `644a89784316`). |
| `fault_run_baseline.json` | `verify` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`verify:exact_fault_replay_proof`, Job 17426629832) | 2026-10-23 19:06:36 | 5 baseline probes under active fault: 100% SLA breaches (mean 3558.46 ms, p95 3738.16 ms). |
| `fault_run_hardened.json` | `verify` | `79348f47` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`verify:exact_fault_replay_proof`, Job 17426629832) | 2026-10-23 19:08:01 | 20 candidate probes under identical fault: 0% SLA breaches (mean 484.27 ms, p95 806.79 ms). |
| `replay_evaluation.json` | `verify` | `e150fad0` vs `79348f47` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`verify:exact_fault_replay_proof`, Job 17426629832) | 2026-10-23 19:08:01 | Replay proof confirming identical fault hash `644a89784316`, Phase A timeout, and Phase B breaker trip. |
| `bandit_security_report.json` | `secure` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`secure:sast_and_secret_scan`, Job 17426629835) | 2026-10-23 19:08:27 | Static AST security audit confirming zero high/medium security weaknesses or credential leaks. |
| `image_digest.txt` | `package` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`package:container_build`, Job 17426629837) | 2026-10-23 19:10:03 | Immutable distroless container image digest built and pushed to Google Artifact Registry. |
| `release.json` | `release` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`release:cloudrun_candidate_deploy`, Job 17426629839) | 2026-10-23 19:11:25 | Deployment status: `STAGED`, revision `faultforge-checkout-00036-pih` deployed to Cloud Run with clean 90/10 canary split. |
| `live_verification.json` | `release` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`release:cloudrun_candidate_deploy`, Job 17426629839) | 2026-10-23 19:11:24 | Live Cloud Run candidate probe confirming clean 90% production (`faultforge-checkout-00002-kpl`) / 10% canary traffic split verified. |
| `monitor.json` | `monitor` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`monitor:telemetry_probes`, Job 17426629840) | 2026-10-23 19:11:54 | Telemetry probe validation confirming `/health`, `/ready`, and Prometheus `/metrics` availability. |
| `risk_classification.json` | `govern` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`govern:audit_receipt_and_gate`, Job 17426629841) | 2026-10-23 19:12:31 | Supervised Autonomy policy gate: classified as `MEDIUM` risk tier, requiring human outcome review. |
| `stage_ledger.json` | All (1–9) | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`govern:audit_receipt_and_gate`, Job 17426629841) | 2026-10-23 19:12:31 | Aggregated 9-stage empirical ledger recording atomic status and SHA-256 artifact hashes. |
| `stage_ledger_*.json` | Stages 1–9 | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (Jobs 17426629828–17426629841) | 2026-10-23 19:12:31 | Individual per-stage ledger fragments recorded atomically during pipeline execution. |
| `evidence_receipt.json` | `govern` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`govern:audit_receipt_and_gate`, Job 17426629841) | 2026-10-23 19:12:31 | Tamper-evident cryptographic receipt sealed in CI with SHA-256 `1fdf9fae649e620d1f92be6574b9cdb7b62b1a5b707fc6062a3a91797d9eb800`. |
| `EVIDENCE_RECEIPT.md` | `govern` | `e150fad0` | Pipeline [2982633493](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2982633493) (`govern:audit_receipt_and_gate`, Job 17426629841) | 2026-10-23 19:12:31 | Human-readable rendering of the sealed evidence receipt from CI Job 17426629841. |

---

## 3. Audit Verification Rules

- All artifacts in this directory are static snapshots reflecting verified CI runs and are tracked in git for offline verification.
- In active CI/CD pipeline executions, new receipts and ledgers are generated dynamically into `reports/` and retained as CI job artifacts.
- To audit the claims in these reports against the codebase and documentation, run:
  ```bash
  python scripts/truth_audit.py --final-audit
  python scripts/check_readme_claims.py --samples
  ```
