# FaultForge Pre-Submission Hardening Report
## Final Audit & Compliance Deliverables

**Hackathon:** GitLab Transcend — Life After Code (October 2026)  
**Track:** Path A — Start Fresh  
**Target Category:** Best Supervised Agent ($4,000)  
**Secondary Category:** Most Stages Covered ($5,000)  
**Bonus Target:** Google Cloud Bonus (+0.2 Points)  
**Submission Deadline:** October 27, 2026, 1:00 PM UTC (6:30 PM IST)  
**Working Branch:** `fix/submission-hardening`  
**GitLab Showcase Repository:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase`  
**Live Google Cloud Run Service:** `https://faultforge-checkout-136942862703.us-central1.run.app`

---

## 1. MANDATORY HUMAN-ONLY ACTION ITEMS (Action Required by Submitter)

The autonomous agent has hardened all code, automated CI/CD pipelines, truth guards, and verification receipts. The following steps **must be completed manually by the repository owner/submitter**:

| Step | Action Item | Target Location / Interface | Purpose |
|---|---|---|---|
| **1** | **Revoke Exposed PAT** | GitLab User Settings → Access Tokens | Immediately revoke any previously created Personal Access Token. Verify no active token exists on unauthenticated machines. |
| **2** | **Configure CI/CD Variables** | GitLab Showcase Project → Settings → CI/CD → Variables | Add the following masked variables:<br/>- `FF_GITLAB_TOKEN` (Masked): GitLab Token with `api` scope.<br/>- `GCP_PROJECT`: Google Cloud Project ID.<br/>- `GCP_SA_KEY` (File type, masked): Service Account JSON credentials with Cloud Run Admin role. |
| **3** | **Trigger Duo Flow Once** | GitLab Duo Agent Platform UI / Custom Flows | Register `flows/faultforge-flow.yaml` in the GitLab UI and trigger one flow run against an incident issue to populate the live run record. |
| **4** | **Re-run Pipeline on Final Commit** | GitLab Showcase Project → CI/CD → Pipelines | Trigger a clean pipeline run on the final commit of `main` after merging `fix/submission-hardening`. |
| **5** | **Record Video Demo (<3 mins)** | YouTube (Public or Unlisted) | Record the 2:50 demo walkthrough following [`docs/demo-script.md`](demo-script.md). Include timestamps and link in Devpost. |
| **6** | **Submit on Devpost** | Devpost Transcend Portal | Submit before deadline: **Oct 27, 2026, 1:00 PM UTC**. Include GitLab project URL, YouTube video link, and Google Cloud Run live URL. |

---

## 2. Hardening Tasks 0–7 Status Matrix

| Task | Title | Status | Summary of Actions Completed |
|---|---|---|---|
| **Task 0** | Security & Hygiene | **DONE** | Sanitized git remote URLs; verified 0 secrets in git history; integrated GitLab Secret Detection into CI `secure` stage; updated `.gitignore` and `.dockerignore`. |
| **Task 1** | Real GitLab Duo Agent Platform Use | **DONE** | Hardened `trigger_duo_flow.py` with strict API credential validation; created `record_duo_evidence.py`; added dynamic Duo MR candidate detection in CI; authored `docs/duo-run-guide.md`. |
| **Task 2** | Honest & Real Release Stage | **DONE** | Made Cloud Run deploy real when `GCP_PROJECT` and `GCP_SA_KEY` are present; eliminated fake `STAGED` dry-run output in `cloudrun_traffic.py`; added dynamic dotenv environment URL; moved package ledger into `package:container_build`. |
| **Task 3** | Real Toxiproxy in CI | **DONE** | Created `scripts/start_toxiproxy.py` bootstrapper for official Shopify Toxiproxy `v2.9.0`; removed `--allow-standalone-proxy` from all CI jobs; verified profile hash `644a89784316` from live Toxiproxy API readback; regenerated sample reports. |
| **Task 4** | Trustworthy Ledger & Claim Validator | **DONE** | Hardened `evidence_ledger.py` to verify artifact existence, non-emptiness, and SHA-256 hashes; created `scripts/check_readme_claims.py` gating govern stage against inflated claims; added full unit tests. |
| **Task 5** | Fresh, Consistent Evidence | **DONE** | Reconciled risk tier to MEDIUM (client-side resilience without tests); reconciled count mismatch to 11 agent quality checks across 9 CI stages; ensured `reports/` directory contains only `.gitkeep`. |
| **Task 6** | Path A Provenance | **DONE** | Authored `docs/provenance.md` factually detailing repository inception on October 16, 2026 (commit `b22d2e8`) and complete Path A "Start Fresh" compliance. |
| **Task 7** | Submission Package | **DONE** | Updated `docs/hackathon-submission.md` with Devpost copy; verified `docs/demo-script.md` under 3 minutes; produced `docs/hardening-report.md`. |

---

## 3. Claims Adjusted from "Real" to "Not Established / Skipped"

In strict compliance with **Rule 1 (Never Fabricate Evidence)** and **Rule 2 (Prefer Changing the Claim Over Faking the Capability)**, the following claims were adjusted to preserve 100% empirical credibility:

1. **Google Cloud Run Candidate Staging Deployment:**
   - *Previous behavior:* In uncredentialed CI runs, `cloudrun_traffic.py --dry-run` printed "staging verified successfully" and emitted `reports/release.json` with `status: STAGED`.
   - *Hardened truth:* When `GCP_PROJECT` or `GCP_SA_KEY` are not set in CI variables, `release:cloudrun_candidate_deploy` writes `status: SKIPPED_NO_GCP_CREDENTIALS`, passes ledger status `SKIPPED`, and the receipt records Cloud Run candidate deployment under `not_established`. `--dry-run` prints `DRY RUN: no action taken` and exits without writing a fake staged record.
2. **GitLab Duo Flow Execution:**
   - *Previous behavior:* Local trigger script emitted `CONFIRMED` without an active GitLab API token.
   - *Hardened truth:* When `FF_GITLAB_TOKEN` or `GITLAB_TOKEN` is unconfigured, `trigger_duo_flow.py` sets status to `NOT_EXECUTED_NO_CREDENTIALS` (`executed: False`). The receipt flags Duo remote remediation under `not_established` and sets `CONTAINED_NEEDS_REVIEW`.
3. **Candidate Fix Provenance:**
   - *Previous behavior:* If Duo was unexecuted, CI fell back to `reference-fix` silently.
   - *Hardened truth:* CI now explicitly inspects `reports/duo_evidence.json`. If a Duo-authored branch is found, it evaluates that branch; if missing, it falls back to `reference-fix` and explicitly tags candidate source as `reference-fix (not Duo-authored)`. The receipt reports this under `not_established`.
4. **Chaos Engine Architecture:**
   - *Previous behavior:* CI passed `--allow-standalone-proxy` while README claimed Toxiproxy was the primary engine.
   - *Hardened truth:* `--allow-standalone-proxy` has been completely eliminated from CI. Both `create` and `verify` jobs now boot and verify the official Shopify Toxiproxy binary (`v2.9.0`), read back toxic configuration from the live Toxiproxy REST API, and assert profile hash `644a89784316`. The receipt generator refuses `RECOVERED_AND_VERIFIED` if either run used the standalone engine.
5. **Risk Classification Tier:**
   - *Previous behavior:* README claimed the shipping client change was `Low Risk / auto-apply`, while `classify_risk.py` classified it as `MEDIUM`.
   - *Hardened truth:* Documentation and architecture specs have been reconciled to `MEDIUM Risk / Supervised Route`. Because the candidate change touches outbound client network logic without committing new test files under `tests/`, it triggers the supervised review route, requiring human sign-off for live production promotion.

---

## 4. Final Verification Command Log

Before opening the Merge Request, the following verification suite was executed locally:

```text
======================================================================
1. Pytest Unit & Integration Test Suite: 65 passed, 1 skipped
2. FaultForge Truth Audit (Anti-Fake Guard): PASSED (0 violations)
3. README Claims vs. Stage Ledger Gate: PASSED (9/9 stages verified)
4. Secret Detection Check: 0 token/secret patterns across all commits
======================================================================
```
