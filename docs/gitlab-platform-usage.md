# GitLab Duo & Native Platform Usage Matrix
# SPDX-License-Identifier: MIT

This matrix provides judges and auditors with an exact, file-and-line traceable mapping of every GitLab native platform and GitLab Duo capability utilized across FaultForge, cross-referenced with empirical artifacts and current execution status.

---

## 1. Feature Traceability Matrix

| GitLab / Duo Feature | Implementation Location | Evidence Artifact | Verification Status | Notes / Criteria |
|---|---|---|---|---|
| **Duo Agent Platform Custom Flow** | [`flows/faultforge-flow.yaml`](../flows/faultforge-flow.yaml) | `reports/duo_run.json` | `not_established` | Flow Registry Framework v1 schema with 3 specialized agents (`diagnostician`, `resilience_healer`, `chaos_hardener`), full toolset (`get_issue`, `create_branch`, `create_commit`, `create_merge_request`), and Jinja2 context templates. |
| **Duo Flow Triggers** | [`flows/faultforge-flow.yaml:8-12`](../flows/faultforge-flow.yaml#L8-L12), [`docs/duo-run-guide.md:27-32`](duo-run-guide.md#L27-L32) | `reports/duo_run.json` | `not_established` | Supports both `@mention` trigger and issue `assign` trigger conditions configured in Automate → Flows. |
| **Incident Work Item / Issue Tracking** | [`scripts/plan_incident.py:45`](../scripts/plan_incident.py#L45), [`.gitlab-ci.yml:41-50`](../.gitlab-ci.yml#L41-L50) | [`docs/sample_reports/incident_dossier.json`](sample_reports/incident_dossier.json), `reports/issue.json` | `established` | Creates structured incident issue with sanitized logs, stack traces, and Toxiproxy reproduction parameters. |
| **Duo-Authored Merge Request** | [`scripts/record_duo_evidence.py`](../scripts/record_duo_evidence.py), [`.gitlab-ci.yml:86-97`](../.gitlab-ci.yml#L86-L97) | `reports/duo_evidence.json` | `not_established` | Ready for live Duo flow execution; currently evaluates audited `reference-fix (not Duo-authored)` fallback with no faked records. |
| **9-Stage Lifecycle CI/CD Pipeline** | [`.gitlab-ci.yml:8-17`](../.gitlab-ci.yml#L8-L17) | [`docs/sample_reports/stage_ledger.json`](sample_reports/stage_ledger.json) | `established` | All 9 GitLab stages (`plan`, `create`, `configure`, `verify`, `secure`, `package`, `release`, `monitor`, `govern`) verified on GitLab SaaS runners (Pipeline `2967640493`). |
| **Merge Request Event Pipelines** | [`.gitlab-ci.yml:9-14`](../.gitlab-ci.yml#L9-L14) | [`.gitlab-ci.yml`](../.gitlab-ci.yml) | `established` | Configured with `workflow:rules` to automatically run MR pipelines on Duo-authored MRs without duplicate branch runs. |
| **GitLab Container Registry** | [`.gitlab-ci.yml:230-245`](../.gitlab-ci.yml#L230-L245) | [`docs/sample_reports/stage_ledger.json`](sample_reports/stage_ledger.json) | `established` | Authenticates with `$CI_REGISTRY_IMAGE` and builds multi-stage distroless container image. |
| **GitLab Environments (Staging & Production)** | [`.gitlab-ci.yml:292, 420`](../.gitlab-ci.yml#L292) | [`docs/sample_reports/stage_ledger.json`](sample_reports/stage_ledger.json) | `established` | Manages discrete `staging` deployment and manual protected `production` environment with tracked URLs. |
| **GitLab Native Secret Detection** | [`.gitlab-ci.yml:5, 23`](../.gitlab-ci.yml#L5) | `reports/gl-secret-detection-report.json` | `established` | Includes official GitLab template `Jobs/Secret-Detection.gitlab-ci.yml` mapped to `stage: secure`. |
| **GitLab Native SAST (Semgrep)** | [`.gitlab-ci.yml:6, 27`](../.gitlab-ci.yml#L6) | `reports/gl-sast-report.json` | `established` | Includes official GitLab template `Jobs/SAST.gitlab-ci.yml` (`semgrep-sast`) mapped to `stage: secure` alongside Python AST Bandit scanning. |
| **Code Quality & Cobertura Coverage** | [`.gitlab-ci.yml:133-143`](../.gitlab-ci.yml#L133-L143) | `reports/coverage.xml`, `reports/junit_tests.xml` | `established` | `pytest-cov` generates Cobertura coverage reports linked via `artifacts:reports:coverage_report` and JUnit test reports. |
| **Supervised Autonomy Approval Gate** | [`.gitlab-ci.yml:384-422`](../.gitlab-ci.yml#L384-L422) | [`docs/sample_reports/evidence_receipt.json`](sample_reports/evidence_receipt.json) | `established` | Requires explicit human gate approval (`when: manual`) before candidate container revision can be promoted to production. |
| **GitLab Code Owners** | [`.gitlab/CODEOWNERS`](../.gitlab/CODEOWNERS) | [`.gitlab/CODEOWNERS`](../.gitlab/CODEOWNERS) | `established` | Declares mandatory review ownership over `/app/`, `/flows/`, `.gitlab-ci.yml`, and `/.gitlab/`. |
| **Duo Code Review Custom Instructions** | [`.gitlab/duo/mr-review-instructions.yaml`](../.gitlab/duo/mr-review-instructions.yaml) | [`.gitlab/duo/mr-review-instructions.yaml`](../.gitlab/duo/mr-review-instructions.yaml) | `established` | Configures repo-level review rules for `/duo review` to inspect bounded timeouts, fallback handling, and forbidden security boundaries. |
| **GitLab Native Release Creation** | [`.gitlab-ci.yml:424-455`](../.gitlab-ci.yml#L424-L455) | [`.gitlab-ci.yml`](../.gitlab-ci.yml) | `established` | Uses official `release:` keyword and `release-cli` linking permanent evidence receipt and container image digest. |
| **GitLab Pages Static Dashboard** | [`.gitlab-ci.yml:253-264`](../.gitlab-ci.yml#L253-L264) | `public/index.html` | `established` | Publishes static client-side telemetry dashboard to GitLab Pages on default branch. |
| **Cryptographic Evidence Receipt & Seal** | [`scripts/generate_receipt.py`](../scripts/generate_receipt.py) | [`docs/sample_reports/evidence_receipt.json`](sample_reports/evidence_receipt.json) | `established` | Signs SHA-256 ledger digest and enforces anti-fake auditing (`scripts/truth_audit.py`). |

---

## 2. Status of Unestablished Items (`CONTAINED_NEEDS_REVIEW`)

In strict accordance with the hackathon's truthfulness rules, FaultForge reports `final_status: "CONTAINED_NEEDS_REVIEW"` in [`docs/sample_reports/evidence_receipt.json`](sample_reports/evidence_receipt.json). The exact status of the three non-established items is:

1. **GitLab Duo Flow Execution:** `not_established`  
   - *Status:* Unexecuted in sample pipeline due to absence of Duo Agent Platform credits in runner context (`reports/duo_run.json` status `NOT_EXECUTED_NO_CREDENTIALS`).  
   - *Remediation:* Follow [`docs/duo-run-guide.md`](duo-run-guide.md) to execute the flow with credits and trigger the Duo MR.

2. **Cloud Run Candidate Deployment:** `not_established`  
   - *Status:* Skipped in sample pipeline due to absence of GCP credentials in runner context (`reports/release.json` status `SKIPPED_NO_GCP_CREDENTIALS`).  
   - *Remediation:* Provide `GCP_PROJECT`, `GCP_SA_KEY`, and set `REQUIRE_GCP_DEPLOY=true` in project CI/CD variables.

3. **Live Traffic Split Verification:** `not_established`  
   - *Status:* Unverified against live Cloud Run URL (`live_verification.json` status `NOT_VERIFIED`).  
   - *Remediation:* Run `python scripts/verify_live.py --base-url <LIVE_URL>` after deploying candidate revision with `--no-traffic --tag candidate`.
