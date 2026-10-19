# GitLab Duo Agent Platform: Execution & Verification Guide
# SPDX-License-Identifier: MIT

This guide provides step-by-step instructions to register and execute the **FaultForge Custom Flow** (`flows/faultforge-flow.yaml`) on GitLab, creating the official Duo-authored Merge Request for hackathon evaluation.

---

## 1. Flow Registration on GitLab

1. Navigate to your project on GitLab:  
   `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase`
2. In the left navigation menu, go to **Automate** → **Flows** (or **Duo Agent Platform** → **Flows**).
3. Click **New Flow** (or **Register Custom Flow**).
4. Enter the Flow configuration:
   - **Flow ID:** `faultforge_resilience_flow`
   - **Display Name:** `FaultForge Supervised Resilience Healer`
   - **Source:** Select **Repository file** and enter `flows/faultforge-flow.yaml` (or paste file contents).
   - **Environment:** `ambient` (Full workspace execution).
5. Click **Save & Activate**.

---

## 2. Triggering Duo Flow on an Incident Issue

FaultForge's CI stage `plan:incident_tracking` automatically registers an incident issue (e.g. Issue #29).

To trigger the registered Duo Agent flow:
1. Open the created incident issue in **Plan** → **Issues** (or click the URL from `reports/issue.json`).
2. Add a comment mentioning the Duo agent service account:
   ```markdown
   @ai-faultforge_resilience_flow Please diagnose and repair the shipping carrier timeout breach identified in this incident.
   ```
3. Alternatively, click **Run Flow** at the top of the issue and select `faultforge_resilience_flow`.
4. The Duo Agent Platform initializes:
   - **Diagnostician Agent:** Inspects AST and identifies missing timeouts in `app/clients/shipping_client.py`.
   - **Resilience Healer Agent:** Synthesizes the 0.8s bounded timeout, circuit breaker, and graceful fallback.
   - **Chaos Hardener Agent:** Runs tests and opens a candidate Merge Request targeting `main`.

---

## 3. Confirming the Duo-Authored Merge Request

1. Go to **Code** → **Merge Requests**.
2. Locate the MR opened by `ai-faultforge_resilience_flow` (branch: `fix/resilience-shipping-timeout` or similar).
3. Inspect the MR description:
   - Contains root-cause summary, culprit commit reference (`974035c`), and test plan.
4. Verify the author is the registered Duo service bot.

---

## 4. Capturing Evidence for Hackathon Submission

1. **Screenshot Duo Flow Session:** Take high-resolution screenshots of the Duo session log showing the agent reasoning, tool calls (`read_file`, `run_command`), and patch synthesis.
2. **Record Duo Run URL:** Copy the session link (e.g. `https://gitlab.com/.../-/work_items/30` or flow run URL).
3. **Run Evidence Harvester:**
   In your local shell or CI, run:
   ```bash
   python scripts/record_duo_evidence.py
   ```
   This populates `reports/duo_evidence.json` with the verified MR IID, author, and branch name.
4. **CI Auto-Detection:**
   The `verify:exact_fault_replay_proof` job will automatically detect `reports/duo_evidence.json` and test the Duo MR branch directly, certifying the run as Duo-authored in `evidence_receipt.json`.
