# FaultForge Sample Verification Reports

This directory stores reference artifacts generated from official pipeline execution for documentation, evaluation review, and reproducibility auditing.

## Provenance & Run Metadata

- **Originating CI Pipeline:** [GitLab CI Pipeline #2963430484](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2963430484)
- **Git Commit:** `481be8f57343e06f97fa620f3a61f2f01f010344`
- **Chaos Engine:** Official Shopify Toxiproxy Server `v2.9.0`
- **Canonical Fault Profile Hash:** `644a89784316` (Latency: 3500ms, Jitter: 250ms)
- **Canonical Payload Hash:** `ab41be6ea964`
- **Autonomy Model:** Supervised Autonomy (Risk-gated human promotion for live traffic)

## Artifact Manifest

| Artifact File | Lifecycle Stage | Description |
|---|---|---|
| [`issue.json`](issue.json) | `plan` | Structured incident issue representation |
| [`incident_dossier.json`](incident_dossier.json) | `create` | Synthesized incident dossier with sanitized logs and culprit commit |
| [`diagnosis_report.json`](diagnosis_report.json) | `create` | AST inspection and deterministic `git bisect` report |
| [`fault_config.json`](fault_config.json) | `configure` | Toxiproxy network chaos configuration and read-back toxic state |
| [`fault_run_baseline.json`](fault_run_baseline.json) | `create` / `verify` | 5 baseline probes reproducing SLA budget breach (avg 3742ms) |
| [`fault_run_hardened.json`](fault_run_hardened.json) | `verify` | 10 candidate probes passing under identical fault (avg 826ms, 0 breaches) |
| [`replay_evaluation.json`](replay_evaluation.json) | `verify` | Mathematical evaluation of 11 verification gates |
| [`bandit_security_report.json`](bandit_security_report.json) | `secure` | Static AST security analysis report |
| [`rollback.json`](rollback.json) | `release` | Automated canary traffic splitting and instantaneous rollback record |
| [`stage_ledger.json`](stage_ledger.json) | `govern` | Complete 9-stage append-only execution ledger |
| [`evidence_receipt.json`](evidence_receipt.json) | `govern` | Cryptographically sealed Evidence Receipt with SHA-256 seal |
| [`EVIDENCE_RECEIPT.md`](EVIDENCE_RECEIPT.md) | `govern` | Human-readable Markdown audit receipt |
