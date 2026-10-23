# GitLab Platform Feature Usage & Transcend Evaluation Guide
# SPDX-License-Identifier: MIT

FaultForge is designed to showcase the full power of the **GitLab Duo Agent Platform** and the complete **GitLab DevSecOps lifecycle** across all 9 stages.

---

## 1. GitLab Feature Matrix & Evidence Links

| GitLab Platform Feature | Implementation / Location | Verifying Artifact | Status | Evaluation Notes |
|---|---|---|---|---|
| **GitLab Duo Agent Platform** | [`flows/faultforge-flow.yaml`](../flows/faultforge-flow.yaml) | [`docs/sample_reports/duo_run.json`](sample_reports/duo_run.json) | `established` | Custom flow with Diagnostician, Resilience Healer, and Chaos Hardener; executed via Session [9909079](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079). |
| **Duo Flow Triggers** | [`flows/faultforge-flow.yaml:8-12`](../flows/faultforge-flow.yaml#L8-L12), [`docs/duo-run-guide.md:27-32`](duo-run-guide.md#L27-L32) | `reports/duo_run.json` | `established` | Supports both `@mention` trigger and issue `assign` trigger conditions configured in Automate → Flows; verified on Issue `#42`. |
| **Duo-Authored Commit & Merge Request** | [`scripts/record_duo_evidence.py`](../scripts/record_duo_evidence.py), [`.gitlab-ci.yml:86-97`](../.gitlab-ci.yml#L86-L97) | `reports/duo_evidence.json` | `established` | Verified on GitLab Merge Request `!3` (Branch `fix/resilience-shipping-timeout`), commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token. Commit [`f8aa9d98`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/f8aa9d98b8617b51c15b5fa6ceda39eb43762730) authored by `FaultForge, Supervised, Resilience, Healer` (`service_account_group_121124982_e6349fd5e8ecd6554efb712ed8e2654f@noreply.gitlab.com`). MR !3 is unmerged; `main` retains the unpatched regression version of `app/clients/shipping_client.py`. |
| **GitLab Work Items & Incident Management** | [`scripts/plan_incident.py`](../scripts/plan_incident.py), [`.gitlab-ci.yml:71-84`](../.gitlab-ci.yml#L71-L84) | [`docs/sample_reports/issue.json`](sample_reports/issue.json) | `established` | Creates and tracks incident work items (`type: incident`) linking telemetry logs, commit SHA, and pipeline URLs. |
| **GitLab Environments (Staging & Production)** | [`.gitlab-ci.yml:292, 420`](../.gitlab-ci.yml#L292) | [`docs/sample_reports/stage_ledger.json`](sample_reports/stage_ledger.json) | `established` | Manages discrete `staging` deployment and manual protected `production` environment with tracked URLs. |
| **GitLab Secret Detection** | [`.gitlab-ci.yml:235-248`](../.gitlab-ci.yml#L235-L248) | GitLab CI Security tab | `established` | Native `Jobs/Secret-Detection.gitlab-ci.yml` template scanning repository on every push. |
| **GitLab SAST (Semgrep)** | [`.gitlab-ci.yml:250-264`](../.gitlab-ci.yml#L250-L264) | GitLab CI Security tab | `established` | Native `Jobs/SAST.gitlab-ci.yml` template scanning Python source code for security regressions. |
| **GitLab Pages** | [`.gitlab-ci.yml:278-290`](../.gitlab-ci.yml#L278-L290) | [Pages Deployment](https://gitlab-ai-hackathon.gitlab.io/transcend-october-2026/43424456/showcase/) | `established` | Publishes static documentation site and interactive dashboard via `public/` directory artifact. |
| **Supervised Autonomy Approval Gate** | [`.gitlab-ci.yml:384-422`](../.gitlab-ci.yml#L384-L422) | [`docs/sample_reports/evidence_receipt.json`](sample_reports/evidence_receipt.json) | `established` | Requires explicit human gate approval (`when: manual`) before candidate container revision can be promoted to production. |
| **GitLab Native Release Creation** | [`.gitlab-ci.yml:424-455`](../.gitlab-ci.yml#L424-L455) | [`.gitlab-ci.yml`](../.gitlab-ci.yml) | `established` | Uses official `release:` keyword and `release-cli` linking permanent evidence receipt and container image digest. |

---

## 2. Platform Verification & Empirical Evidence Status (`RECOVERED_AND_VERIFIED`)

In strict accordance with the hackathon's truthfulness rules, FaultForge reports `final_status: "RECOVERED_AND_VERIFIED"` with zero unestablished items (`not_established: []`) in [`docs/sample_reports/evidence_receipt.json`](sample_reports/evidence_receipt.json).

### Established GitLab Duo Artifacts:
- **Duo Agent Session:** [Session 9909079](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079) (`claude_sonnet_5_5_vertex`, CI Job `17391324956`)
- **Root Incident Work Item:** [Issue #42](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/42)
- **Duo Remediation Merge Request:** [Merge Request !3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) (Branch `fix/resilience-shipping-timeout`, Commit [`f8aa9d98`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/f8aa9d98b8617b51c15b5fa6ceda39eb43762730), **unmerged**; `main` retains unpatched `app/clients/shipping_client.py`)
- **Author Identity:** `FaultForge, Supervised, Resilience, Healer <service_account_group_121124982_e6349fd5e8ecd6554efb712ed8e2654f@noreply.gitlab.com>`
- **Candidate Replay Proof:** 0/20 SLA breaches (0%) under identical fault profile `644a89784316` (`candidate_source: commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token`)

### Incident Work Item Provenance: Root Issue #42 vs. Pipeline Issue #50
Evaluators inspecting evidence artifacts will note two incident issue references:
- **Issue #42 (Root Remediation Issue):** The primary incident work item created during initial chaos discovery. The GitLab Duo Healer custom flow was triggered on Issue #42, synthesized the resilience patch, and opened Merge Request `!3`.
- **Issue #50 (Pipeline Incident Tracking):** During automated GitLab CI pipeline executions on `main` (Pipeline `#2982183259`), the `plan:incident_tracking` job dynamically provisions a runtime incident work item (`#50`) to track the specific pipeline run and verify end-to-end incident automation without mutating historical issue records.

### Candidate Replay Architecture: Applying Candidate Branch on Pipeline Commit
In the CI stage `verify:exact_fault_replay_proof`:
1. The runner checks out the tested commit on `main`.
2. It fetches the Duo remediation candidate branch `origin/fix/resilience-shipping-timeout`.
3. It validates that the diff contains no forbidden files (via `scripts/check_forbidden_paths.py`).
4. It checks out `origin/fix/resilience-shipping-timeout -- app/` directly on top of HEAD, compiling the candidate tree.
5. It executes 20 probes under the identical Toxiproxy latency profile `644a89784316`.
Consequently, the candidate commit SHA recorded in `fault_run_hardened.json` (`d3720143...`) represents the candidate patch applied to the pipeline commit, while the candidate source branch references Duo commit `f8aa9d98`.

### Code Provenance: Why app_tree_matches_duo_commit is false
In `reports/duo_evidence.json` and the sealed receipt, `app_tree_matches_duo_commit` is recorded as `false`:
- **Duo-Authored Commit (`f8aa9d98`):** Synthesized by the GitLab Duo service account in session 9909079, providing the core 0.8s timeout, circuit breaker (3 failures, 10s cooldown), and fallback estimate in `app/clients/shipping_client.py`.
- **Subsequent Evaluated Commit (`d372014`):** During candidate replay hardening, the pair-programming agent added `asyncio.wait_for` as a hard wall-clock outer deadline to guard against asynchronous hanging connections and updated navigation in `app/dashboard.html`.
- **Exact Diff:** `app/clients/shipping_client.py` (+24/-21) and `app/dashboard.html` (+5/-4). Both commits reside on candidate branch `fix/resilience-shipping-timeout` (MR !3).

### Verified Deployment Status:
1. **Cloud Run Candidate Deployment:** `VERIFIED (SUCCESS)`  
   - *Status:* Candidate revision (`faultforge-checkout-00026-sam`) actively deployed to Google Cloud Run staging in `us-central1` via CI stage `release:cloudrun_candidate_deploy` (`reports/release.json` status `STAGED`).

2. **Live Canary Traffic Split Verification:** `VERIFIED (SUCCESS)`  
   - *Status:* Probed against live endpoint; confirmed HTTP 200 OK with 10% canary traffic routing verified (`reports/live_verification.json` status `VERIFIED`).
