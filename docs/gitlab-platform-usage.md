# GitLab Platform Feature Usage & Transcend Evaluation Guide
# SPDX-License-Identifier: MIT

FaultForge is designed to showcase the full power of the **GitLab Duo Agent Platform** and the complete **GitLab DevSecOps lifecycle** across all 9 stages.

---

## 1. GitLab Feature Matrix & Evidence Links

| GitLab Platform Feature | Implementation / Location | Verifying Artifact | Status | Evaluation Notes |
|---|---|---|---|---|
| **GitLab Duo Agent Platform** | [`flows/faultforge-flow.yaml`](../flows/faultforge-flow.yaml) | [`docs/sample_reports/duo_run.json`](sample_reports/duo_run.json) | `established` | Custom flow with Diagnostician, Resilience Healer, and Chaos Hardener; executed via Session [9909079](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079). |
| **Duo Flow Triggers** | [`flows/faultforge-flow.yaml:8-12`](../flows/faultforge-flow.yaml#L8-L12), [`docs/duo-run-guide.md:27-32`](duo-run-guide.md#L27-L32) | `reports/duo_run.json` | `established` | Supports both `@mention` trigger and issue `assign` trigger conditions configured in Automate → Flows; verified on Issue `#42`. |
| **Duo-Authored Commit & Merge Request** | [`scripts/record_duo_evidence.py`](../scripts/record_duo_evidence.py), [`.gitlab-ci.yml:86-97`](../.gitlab-ci.yml#L86-L97) | `reports/duo_evidence.json` | `established` | Verified on GitLab Merge Request `!3` (Branch `fix/resilience-shipping-timeout`), commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token. Commit [`f8aa9d98`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/f8aa9d98b8617b51c15b5fa6ceda39eb43762730) authored by `FaultForge, Supervised, Resilience, Healer` (`service_account_group_121124982_e6349fd5e8ecd6554efb712ed8e2654f@noreply.gitlab.com`). MR !3 is unmerged; `main`'s `app/clients/shipping_client.py` was authored by FaultForge Agent in `e150fad` as an adapted copy of Duo's patch (18+/30- vs `79348f4`). |
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
- **Duo Remediation Merge Request:** [Merge Request !3](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3) (Branch `fix/resilience-shipping-timeout`, Commit [`f8aa9d98`](https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/commit/f8aa9d98b8617b51c15b5fa6ceda39eb43762730), **unmerged**; `main`'s `app/clients/shipping_client.py` was authored by FaultForge Agent in `e150fad` as an adapted copy of Duo's patch)
- **Author Identity:** `FaultForge, Supervised, Resilience, Healer <service_account_group_121124982_e6349fd5e8ecd6554efb712ed8e2654f@noreply.gitlab.com>`
- **Candidate Replay Proof:** 0/20 SLA breaches (0%) under identical fault profile `644a89784316` (`candidate_source: commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token`)

### Incident Work Item Provenance: Root Issue #42 vs. Pipeline Incident Work Item #62
Evaluators inspecting evidence artifacts will note two incident issue references:
- **Issue #42 (Root Remediation Issue):** The primary incident work item created during initial chaos discovery. The GitLab Duo Healer custom flow was triggered on Issue #42, synthesized the resilience patch, and opened Merge Request `!3`.
- **Issue #62 (Pipeline Incident Tracking):** During automated GitLab CI pipeline executions on `main` (Pipeline `#2984589851`), the `plan:incident_tracking` job dynamically provisions a runtime incident work item (`#62`) to track the specific pipeline run and verify end-to-end incident automation without mutating historical issue records.

### Candidate Replay Architecture: Applying Candidate Branch on Pipeline Commit
In the CI stage `verify:exact_fault_replay_proof`:
1. The runner checks out the tested commit on `main`.
2. It fetches the Duo remediation candidate branch `origin/fix/resilience-shipping-timeout`.
3. It validates that the diff contains no forbidden files (via `scripts/check_forbidden_paths.py`).
4. It checks out `origin/fix/resilience-shipping-timeout -- app/` directly on top of HEAD, compiling the candidate tree.
5. It executes 20 probes under the identical Toxiproxy latency profile `644a89784316`.
Consequently, the candidate commit SHA evaluated and recorded in `fault_run_hardened.json` (`79348f47042849465c737be2493b135a21f37e06`) represents the candidate branch head evaluated by the pipeline, while the initial Duo synthesis commit is `f8aa9d98`.

### Code Provenance: Author Breakdown and Candidate Tree Provenance

From `git log --all --author=service_account`, six commits were authored by the GitLab Duo service account (`FaultForge, Supervised, Resilience, Healer <service_account_group_121124982_e6349fd5e8ecd6554efb712ed8e2654f@noreply.gitlab.com>`) on branch `fix/resilience-shipping-timeout`:

| Short Commit | Full Commit SHA | Date (UTC) | Subject | GitLab Agent Session / Run |
|---|---|---|---|:---:|
| `f8aa9d9` | `f8aa9d98b8617b51c15b5fa6ceda39eb43762730` | 2026-10-22 17:18:48 | fix(resilience): bound shipping client with 0.8s timeout, circuit breaker and graceful fallback | Session `9909079` |
| `d372014` | `d3720143e15c85f519a7624859541d1ce997f1a0` | 2026-10-23 15:48:38 | fix(resilience): bound shipping call to 0.8s with circuit breaker and fallback estimate | not established |
| `fafadf8` | `fafadf8bdacf311e6ae7e34b6155b76905faa7d4` | 2026-10-23 17:13:14 | fix(resilience): bound shipping client with 0.8s timeout, circuit breaker and graceful fallback | not established |
| `b57584a` | `b57584ae2517633d989506c1898611c9adb84760` | 2026-10-23 17:16:01 | fix(resilience): bound shipping client with 0.8s timeout, circuit breaker and graceful fallback | not established |
| `001055b` | `001055befef13cb190f7f380b79dd371c4cdb8a3` | 2026-10-23 18:31:09 | fix(resilience): bound shipping call to 0.8s with circuit breaker and graceful fallback | not established |
| `79348f4` | `79348f47042849465c737be2493b135a21f37e06` | 2026-10-23 18:35:09 | fix(resilience): bound shipping call to 0.8s with circuit breaker and graceful fallback | not established |

**Provenance Facts & Commit Relationships:**
- **None of the six service-account commits is an ancestor of `main`:** Verified via `git merge-base --is-ancestor <commit> main` (`False` for all six).
- **Merge Request `!3` is unmerged:** Confirmed on GitLab via API (`state: opened`, `merged_at: None`).
- **Main's `app/clients/shipping_client.py` is authored by FaultForge Agent in `e150fad`:** Authored by `FaultForge Agent <agent@faultforge.internal>` as an adapted copy of Duo's patch (1 file changed, 18 insertions(+), 30 deletions(-) vs `79348f4`), preserving identical resilience semantics.
- **Orchestration Agent Commit (`3294042`):** Authored by `FaultForge Agent <agent@faultforge.internal>` to merge `main` into `fix/resilience-shipping-timeout`, synchronizing CI configuration and bringing in `app/dashboard.html` updates from `main`.
- **Evaluated Candidate Head (`79348f47`):** Authored by the Duo service account and evaluated as the candidate commit during exact-fault replay proof in pipeline #2982633493. The diff between initial Duo commit `f8aa9d98` and evaluated `79348f4` is:
  ```
  app/clients/shipping_client.py | 48 ++++++++++++++++++++++++++----------------
  app/dashboard.html             |  7 +++---
  2 files changed, 34 insertions(+), 21 deletions(-)
  ```
  Because `app/dashboard.html` and refinements exist beyond `f8aa9d98`, `app_tree_matches_duo_commit` is accurately recorded as `false`.
- **Evaluated Candidate vs. Main Pipeline Tree (`app_tree_matches_evaluated_candidate`):** Running `git diff --quiet 79348f47 e150fad -- app/` confirms `app_tree_matches_evaluated_candidate: false` with the exact diff stat:
  ```
  app/clients/__init__.py        |   3 +-
  app/clients/orbit_client.py    | 127 +++++++++++++++++++++++++++++++++++++++++
  app/clients/shipping_client.py |  48 ++++++----------
  app/dashboard.html             |  12 ++--
  app/main.py                    |  27 +++++++++
  5 files changed, 180 insertions(+), 37 deletions(-)
  ```
  This reflects post-remediation main branch features such as `orbit_client.py`.

### Shipping Client Diff: Candidate Branch Head (`79348f47`) vs. Main Adapted Commit (`e150fad`)
Running `git diff 79348f47 e150fad -- app/clients/shipping_client.py`:
- **Diff Stat:**
  ```
  app/clients/shipping_client.py | 48 ++++++++++++++++--------------------------
  1 file changed, 18 insertions(+), 30 deletions(-)
  ```
- **Factual Description of Differences:**
  The core resilience logic is functionally identical in both commits: both enforce a strict 0.8s timeout (`SHIPPING_TIMEOUT_SECONDS = 0.8`), 3-failure circuit breaker with 10s cooldown, and deterministic fallback calculation (`is_fallback=True`, `is_estimate=True`) on timeout, transport errors, HTTP 5xx errors, or OPEN circuit.
  The changes in `e150fad` are purely syntactic refactorings:
  1. `_fallback()` sets `data["is_fallback"] = True` and `data["is_estimate"] = True` directly, and records duration before calling `get_graceful_shipping_fallback()`.
  2. `httpx.Timeout` explicitly specifies `connect=SHIPPING_TIMEOUT_SECONDS`.
  3. `settings.CIRCUIT_BREAKER_ENABLED` is checked directly without an intermediate `use_breaker` local variable.
  4. Logging statements use `logger.error` rather than `logger.warning`, and error message strings differ slightly (e.g. `"Upstream HTTP {code}"` vs `"Shipping dependency HTTP {code}"`).
  None of the changes alter or relax the resilience policy or SLA timeout bounds.

### Tree-Parity Proof: Evaluated Candidate (`d75de80a`) vs. Archive Head (`dd1f966`)
To guarantee that post-pipeline documentation, test fixtures, and audit tooling commits did not modify the candidate application code:
- **Evaluated Candidate Commit (CI Pipeline #2984589851):** `d75de80a4242637bdf354f3b0631f4762c2f1f0e` (short `d75de80a`)
- **Documentation & Verification Commit:** `dd1f966eff9b14fb2dc86dec6c132bb0e66df35f` (short `dd1f966`)
- **Full Repository Diff Stat (`git diff --stat d75de80a..dd1f966`):**
  ```text
  .gitlab-ci.yml                                  |  11 +-
  AGENTS.md                                       |   4 +-
  README.md                                       |  64 +++---
  docs/architecture.md                            |   2 +-
  docs/duo-integration.md                         |   2 +-
  docs/gitlab-platform-usage.md                   |  12 +-
  docs/hackathon-submission.md                    |   8 +-
  docs/measurement-method.md                      |  71 ++++---
  docs/sample_reports/EVIDENCE_RECEIPT.md         |  19 +-
  docs/sample_reports/README.md                   |  60 +++---
  docs/sample_reports/bandit_security_report.json |  14 +-
  docs/sample_reports/deployed_tree_sha.txt       |   2 +-
  docs/sample_reports/diagnosis_report.json       |   2 +-
  docs/sample_reports/duo_evidence.json           |  10 +-
  docs/sample_reports/duo_run.json                |   2 +-
  docs/sample_reports/evidence_receipt.json       | 200 +++++++++---------
  docs/sample_reports/fault_run_baseline.json     |  42 ++--
  docs/sample_reports/fault_run_hardened.json     | 270 ++++++++++++------------
  docs/sample_reports/image_digest.txt            |   2 +-
  docs/sample_reports/incident_dossier.json       |  14 +-
  docs/sample_reports/issue.json                  |   6 +-
  docs/sample_reports/live_verification.json      |  12 +-
  docs/sample_reports/monitor.json                |   6 +-
  docs/sample_reports/release.json                |   4 +-
  docs/sample_reports/replay_evaluation.json      |  58 ++---
  docs/sample_reports/replay_tree_sha.txt         |   2 +-
  docs/sample_reports/risk_classification.json    |   8 +-
  docs/sample_reports/stage_ledger.json           | 138 ++++++------
  docs/sample_reports/stage_ledger_configure.json |  10 +-
  docs/sample_reports/stage_ledger_create.json    |  26 +--
  docs/sample_reports/stage_ledger_govern.json    |  14 +-
  docs/sample_reports/stage_ledger_monitor.json   |  12 +-
  docs/sample_reports/stage_ledger_package.json   |  14 +-
  docs/sample_reports/stage_ledger_plan.json      |  12 +-
  docs/sample_reports/stage_ledger_release.json   |  16 +-
  docs/sample_reports/stage_ledger_secure.json    |  12 +-
  docs/sample_reports/stage_ledger_verify.json    |  20 +-
  scripts/build_submission_zip.py                 |  12 +-
  scripts/check_forbidden_paths.py                |  84 ++++++--
  scripts/truth_audit.py                          |   2 +-
  tests/unit/test_forbidden_paths.py              |  31 ++-
  tests/unit/test_package_hygiene.py              |   5 +
  43 files changed, 725 insertions(+), 596 deletions(-)
  ```
- **Application Code Diff (`git diff d75de80a..dd1f966 -- app/`):**
  *(Output is empty — 0 files changed, 0 insertions, 0 deletions).*
- Later commits changed docs, tests, CI configuration and packaging/audit tooling; `app/` is unchanged, preserving the exact tree SHA `de7c0b1cc7d6b7edb90c6b3041b10885ea702492`.

### Safety Guard Boundary and Documented Orchestration Exemptions
To prevent automated remediation agents from tampering with critical platform boundaries or test suites, `scripts/check_forbidden_paths.py` enforces strict boundaries in CI:
- **Automated Remediation Scope:** Duo AI and automated candidate patches are strictly restricted to `app/clients/shipping_client.py`, `app/resilience/`, and **new test additions only** under `tests/`. Enforced for automated MR pipelines (`--name-status`) and covered by unit tests, edits or deletions of existing test files are strictly forbidden (`status='M'` or `status='D'` triggers a fatal gate violation).
- **Documented Human/Orchestration Exemptions:**
  1. `app/main.py` (Author: `rajpriyanid`): Human/orchestration infrastructure providing read-only evidence retrieval (`/api/v1/evidence`), health probe routing, and request timing middleware. All write methods (`POST`, `PUT`, `PATCH`, `DELETE`) are strictly forbidden and blocked.
  2. `app/dashboard.html` (Author: `FaultForge Maintainer`): Interactive client-side HTML review dashboard for evaluators and incident commanders.
  3. `app/clients/orbit_client.py` (Author: `FaultForge Maintainer`): Forward-compatible client stub for GitLab Duo Orbit MCP integration, providing deterministic fallback to AST call-site inspection and git bisecting (`resolution_path: "fallback_ast_git"`).

### Verified Deployment Status:
1. **Cloud Run Candidate Deployment:** `VERIFIED (SUCCESS)`  
   - *Status:* Candidate revision (`faultforge-checkout-00068-gaw`) actively deployed to Google Cloud Run staging in `us-central1` via CI stage `release:cloudrun_candidate_deploy` (`reports/release.json` status `STAGED`).

2. **Live Canary Traffic Split Verification:** `VERIFIED (SUCCESS)`  
   - *Status:* Probed against live endpoint; confirmed HTTP 200 OK with 10% canary traffic routing verified (`reports/live_verification.json` status `VERIFIED`).
