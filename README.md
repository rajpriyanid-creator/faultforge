# FaultForge — Break It, Heal It
## The Supervised Resilience Agent for Closed-Loop Post-Code Reliability

> **"Most chaos tools break things and stop. FaultForge breaks it, heals it, and proves the fix under the same fault."**  
> Built for the **GitLab Transcend 2026: Life After Code** Hackathon (Path A — Start Fresh).

[![Target Prize](https://img.shields.io/badge/Target_Prize-Best_Supervised_Agent_($4,000)-gold.svg)](#2-why-faultforge-wins-best-supervised-agent)
[![Google Cloud Run](https://img.shields.io/badge/Google_Cloud_Run-Live_Active_(+0.2_Bonus)-success.svg)](https://faultforge-checkout-136942862703.us-central1.run.app/dashboard)
[![GitLab Duo Agent Platform](https://img.shields.io/badge/GitLab_Duo-Custom_Flow-orange.svg)](flows/faultforge-flow.yaml)
[![Autonomy Model](https://img.shields.io/badge/Autonomy-Supervised-brightgreen.svg)](docs/safety-policy.md)
[![Lifecycle Stages](https://img.shields.io/badge/Stages-9_Covered-brightgreen.svg)](.gitlab-ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

> [!TIP]
> **Live Google Cloud Run Deployment (Google Cloud Bonus +0.2 Points):**  
> 🌐 **Interactive Dashboard:** [https://faultforge-checkout-136942862703.us-central1.run.app/dashboard](https://faultforge-checkout-136942862703.us-central1.run.app/dashboard)  
> 🩺 **Live Health Probe:** [https://faultforge-checkout-136942862703.us-central1.run.app/health](https://faultforge-checkout-136942862703.us-central1.run.app/health)  
> 📜 **Cryptographic Evidence Receipt:** [https://faultforge-checkout-136942862703.us-central1.run.app/api/v1/evidence](https://faultforge-checkout-136942862703.us-central1.run.app/api/v1/evidence)  
> 🔗 **9-Stage Cryptographic Ledger:** [https://faultforge-checkout-136942862703.us-central1.run.app/api/v1/ledger](https://faultforge-checkout-136942862703.us-central1.run.app/api/v1/ledger)  
> 📊 **Telemetry Metrics:** [https://faultforge-checkout-136942862703.us-central1.run.app/metrics](https://faultforge-checkout-136942862703.us-central1.run.app/metrics)  
> 🛡️ **Chaos Interception Probe:** `POST /api/v1/checkout/test-resilience`

---

## 1. Executive Summary

Most CI pipelines only verify that unit tests pass in isolation. Because unit tests routinely mock external HTTP dependencies, services fail catastrophically in production when a third-party dependency suffers high latency, connection resets, or cascading thread starvation. AI coding assistants can suggest code changes, but **cannot prove the fix actually withstands real network-level degradation**.

**FaultForge** connects deterministic chaos engineering, AI-assisted diagnosis via **GitLab Duo Agent Platform**, automated resilience healing, and empirical proof into a closed-loop platform engineering workflow:

1. **Inject Controlled Chaos:** Inject a deterministic network delay (3500ms ± 250ms jitter) into an isolated downstream shipping dependency via Toxiproxy.
2. **Detect & Collect Evidence:** Record SLA budget breaches (>1500ms budget, observed baseline avg 3742.46ms, p95 3918.27ms, 5/5 breaches), capture sanitized logs, and compile a structured Incident Dossier.
3. **Deterministic Diagnosis & Bisect:** Execute AST call-site inspection and automated `git bisect` to pinpoint the exact regressing commit (`974035c6e45e7c177452df260a155b6508b828e9`) where timeouts and circuit breakers were stripped.
4. **GitLab Duo Agent Platform Remediation:** Trigger a custom GitLab Duo flow (`flows/faultforge-flow.yaml`) whose Diagnostician, Resilience Healer, and Chaos Hardener synthesize a minimal scoped fix: a bounded 0.8s timeout, circuit breaker (3 failures, 10s cooldown), and deterministic fallback rate.
5. **Replay Identical Fault:** Re-execute the **identical Toxiproxy fault profile** (`644a89784316`) against the candidate release across 10 consecutive probe iterations.
6. **Empirical Proof:** Confirm zero SLA budget breaches, >60% latency reduction, and observable fallback responses (`is_fallback: true`, `is_estimate: true`).
7. **Supervised Autonomy Gate:** Enforce risk-based governance, deploy candidate container to Google Cloud Run staging (0% live traffic), and require human review before live production promotion, with automated instant rollback.

> **The Differentiator:** It is not "AI says it fixed the app." **It is the before/after empirical proof under the exact same controlled failure condition.**

---

## 2. Why FaultForge Wins "Best Supervised Agent" ($4,000)

The **GitLab Transcend 2026** competition defines **Supervised Autonomy** as:

> **"You approve the outcome, not the individual steps. Your agents execute a multi-step workflow on their own, clearing gates and making decisions along the way. You review the end result, not every individual action."**  
> *Example:* Code push -> Agents autonomously review, fix failing pipeline, remediate security finding, deploy to staging -> User receives summary report and gives a single sign-off/approval for final production deployment.

FaultForge is the quintessential implementation of this exact paradigm:

### 11 Autonomous Multi-Step Gates vs. 1 Human Outcome Approval

```mermaid
flowchart TD
    subgraph AutonomousExecution["AUTONOMOUS MULTI-STEP AGENT EXECUTION (No Human Hand-Holding)"]
        G1["1. SLA Breach Detection"] --> G2["2. Sanitized Incident Dossier"]
        G2 --> G3["3. AST & Git Bisect Culprit (974035c)"]
        G3 --> G4["4. Scoped 0.8s Timeout & Fallback Patch"]
        G4 --> G5["5. Risk Policy Check (<150 Lines, Low Risk)"]
        G5 --> G6["6. Unit & Integration Tests (39/39 Passed)"]
        G6 --> G7["7. Exact-Fault Replay (10/10 Passed under 644a89784316)"]
        G7 --> G8["8. Bandit Static AST Security Scan"]
        G8 --> G9["9. Hardened Multi-Stage Docker Build"]
        G9 --> G10["10. Cloud Run Staging Deploy (0% Live Traffic)"]
        G10 --> G11["11. Cryptographic Evidence Receipt Sealed"]
    end

    subgraph SupervisedGate["SUPERVISED HUMAN OUTCOME GATE (govern:promote_to_production)"]
        G11 ==> H{"Developer Outcome Review<br/>(Diff + Receipt + Staging URL)"}
        H -->|One-Click Sign-Off| P["Live Production Traffic Promotion (100%)"]
        H -.->|Post-Deploy Anomaly| R["Instant Zero-Downtime Rollback"]
    end
```

### The Enterprise Case: Why Supervised Wins

| Dimension | Assisted Model | Supervised Model (FaultForge) | Hands-Off Model |
|---|---|---|---|
| **Human Burden** | 🔴 Constant micro-approvals for every command, query, and test | 🟢 **Single high-level sign-off on empirical outcome** | 🟢 Zero human interaction |
| **MTTR (Mean Time to Recovery)** | 🔴 Very slow; blocked waiting on humans at every step | 🟢 **Rapid autonomous investigation & staging verification** | 🟡 Fast, but catastrophic if wrong |
| **Safety & Production Risk** | 🟡 High human fatigue causes rubber-stamping | 🟢 **Zero live impact: 100% verified on staging before review** | 🔴 High risk: untested AI code touches production |
| **Auditability & Compliance** | 🔴 Fragmented chat history | 🟢 **Cryptographically sealed Evidence Receipt (SHA-256)** | 🔴 Uncontrolled changes |
| **Best Hackathon Fit** | Fails "multi-step workflow" vision | 🏆 **Perfect match for "Best Supervised Agent" rubric** | Not permitted for production-critical paths |

---

## 3. End-to-End 3-Swimlane Architecture

```mermaid
flowchart TD
    subgraph Swimlane1["1. Chaos Engine (Toxiproxy)"]
        C1["Inject 3,500ms Delay<br/>(Hash: 644a89784316)"] --> C2["Prove Baseline Breach<br/>(3,742ms > 1,500ms SLA)"]
        C2 --> C3["Exact Fault Replay<br/>(10 Consecutive Probes)"]
    end

    subgraph Swimlane2["2. GitLab Duo Agent Platform"]
        D1["Diagnostician<br/>(AST & Bisect to 974035c)"] --> D2["Resilience Healer<br/>(0.8s Timeout + Fallback)"]
        D2 --> D3["Chaos Hardener<br/>(Automated MR & Tests)"]
    end

    subgraph Swimlane3["3. Governance & Supervised Gate"]
        G1["Stage-by-Stage Ledger<br/>(stage_ledger.json)"] --> G2["SHA-256 Evidence Receipt<br/>(evidence_receipt.json)"]
        G2 --> G3{"Supervised Human Gate<br/>(Approval for Live Traffic)"}
        G3 -->|Approved| G4["Cloud Run / Compose 100%"]
        G3 -->|Alert| G5["Instant 0-Downtime Rollback"]
    end

    C2 -.->|Incident Dossier| D1
    D3 -.->|Candidate Patch| C3
    C3 -.->|Replay Proof| G2
```

---

## 4. The 9 Covered Lifecycle Stages

FaultForge implements real, testable operations with machine-readable artifacts across all **9 GitLab Lifecycle Stages**. Reference outputs are mirrored in `docs/sample_reports/`, while live CI/CD pipelines generate fresh runtime artifacts directly into `reports/`:

| Stage | FaultForge Action | Output Artifact / Evidence |
|---|---|---|
| **`plan`** | Compiles structured Incident Dossier with sanitized logs, fault metrics, and `git bisect` culprit | [`docs/sample_reports/incident_dossier.json`](docs/sample_reports/incident_dossier.json) |
| **`create`** | GitLab Duo Flow triggers diagnosis, plans resilience fix, and prepares Merge Request payload | [`docs/sample_reports/diagnosis_report.json`](docs/sample_reports/diagnosis_report.json) |
| **`configure`** | Configures Toxiproxy network chaos topology and latency toxic profile | [`docs/sample_reports/fault_config.json`](docs/sample_reports/fault_config.json) |
| **`verify`** | Runs test suite and executes baseline chaos run reproducing SLA budget breach | [`docs/sample_reports/fault_run_baseline.json`](docs/sample_reports/fault_run_baseline.json) |
| **`secure`** | Scans Python AST for security weaknesses (Bandit) and validates secret sanitization | [`docs/sample_reports/bandit_security_report.json`](docs/sample_reports/bandit_security_report.json) |
| **`package`** | Builds multi-stage production Docker container with non-root security user | [`Dockerfile`](Dockerfile) |
| **`release`** | Deploys candidate container revision to Google Cloud Run staging (0% live traffic) | [`docs/sample_reports/rollback.json`](docs/sample_reports/rollback.json) |
| **`monitor`** | Evaluates exact-fault candidate replay (10 probes) and tracks sliding-window percentiles | [`docs/sample_reports/replay_evaluation.json`](docs/sample_reports/replay_evaluation.json) |
| **`govern`** | Enforces Supervised Autonomy gate and signs tamper-evident SHA-256 seal | [`docs/sample_reports/evidence_receipt.json`](docs/sample_reports/evidence_receipt.json) |

---

## 5. Quickstart & Judge Reproducibility

### Single-Command Full Verification
For evaluators and judges seeking instant verification of repository integrity, test suites, and cryptographic seals:

```bash
# 1. Run full unit and integration test suite (39 tests)
pytest tests/unit tests/integration -v

# 2. Run anti-fake truth audit in strict final mode
python scripts/truth_audit.py --final-audit

# 3. Launch the resilience web dashboard locally
python -m uvicorn app.main:app --host 127.0.0.1 --port 8090
# Open http://127.0.0.1:8090/dashboard in your browser
```

### Step-by-Step Closed-Loop Walkthrough

```bash
# Step 1: Demonstrate Baseline Vulnerability Under Chaos (5 probes under 3500ms delay)
python scripts/run_fault.py --label baseline --output reports/fault_run_baseline.json
# Empirical Result: 5/5 probes breach SLA budget (>1500ms budget, avg 3742ms, p95 3918ms). Status: FAIL.

# Step 2: Ingest Evidence & Bisect Culprit Commit
python scripts/collect_evidence.py
python scripts/diagnose_and_bisect.py
# Output: Deterministic bisect isolates culprit commit 974035c6e45e7c177452df260a155b6508b828e9.

# Step 3: Execute GitLab Duo Flow (Synthesizes 0.8s timeout, circuit breaker & fallback)
python scripts/trigger_duo_flow.py --mode manual

# Step 4: Replay Exact Same Fault Against Candidate (10 consecutive probes under hash 644a89784316)
python scripts/run_fault.py --label candidate --output reports/fault_run_candidate.json
python scripts/evaluate_replay.py --baseline reports/fault_run_baseline.json --candidate reports/fault_run_candidate.json
# Expected Outcome: SLA breaches drop from 5 to 0. Average latency drops to <850ms (>60% reduction). Status: RECOVERED_AND_VERIFIED.

# Step 5: Verify Governance & Cloud Run Staging Promotion Gate
python scripts/generate_receipt.py
python scripts/cloudrun_traffic.py --action rollback --dry-run
```

---

## 6. Limitations & Honest Boundaries

In strict compliance with the **Never Fabricate Evidence** and **Claim Only What Artifacts Prove** guidelines:

1. **System Scope:** FaultForge is evaluated on a single FastAPI checkout microservice (`checkout-service`) with an external shipping carrier dependency.
2. **Single Injected Fault Scenario:** The primary evaluated failure mode is downstream latency cascading hang (3500ms delay ± 250ms jitter); secondary scenario is connection reset.
3. **Estimated Fallback Semantics:** The fallback quote returned under network degradation is a deterministic flat estimate explicitly flagged with `is_fallback: true` and `is_estimate: true` to prevent misrepresenting live carrier rates.
4. **Orbit Dependency Unused:** The repository contains no active Orbit dependency calls; carrier communications strictly use the HTTP stub.
5. **Dual-Proxy Engine Architecture:** Real Toxiproxy (`ghcr.io/shopify/toxiproxy:2.9.0`) is the primary chaos engine in CI and Docker environments. The in-process standalone proxy is reserved solely for local development without Docker, requiring `--allow-standalone-proxy` and automatically downgrading receipt status to `NOT_VERIFIED_STANDALONE`.
6. **GitLab Duo Flow Requirements:** Automated Duo Flow execution relies on GitLab Duo Agent Platform enabled on the GitLab instance or namespace. If API credits or platform access are unconfigured, `scripts/trigger_duo_flow.py` falls back to Issue Mention/Assignment or manual workflow execution without generating fake MR payloads.

---

## 7. Hackathon Prize Strategy & Compliance

- **Track Selection:** **Path A — Start Fresh**. Built cleanly for GitLab Transcend 2026.
- **Primary Category:** **Best Supervised Agent ($4,000)**. Full multi-step automation for investigation, bisecting, code patching, replay verification, and staging deployment, with an explicit risk-gated human promotion gate for live production traffic.
- **Secondary Category:** **Most Stages Covered ($5,000)**. All 9 GitLab lifecycle stages actively verified with real machine-readable artifacts.
- **Additional Category:** **Most Creative ($4,000)**. Novel "Break It, Heal It" closed-loop system pairing chaos testing with exact-fault replay verification.
- **Google Cloud Bonus (+0.2 points):** **Verified Live Google Cloud Run Deployment** in `us-central1`. Service URL: [`https://faultforge-checkout-136942862703.us-central1.run.app`](https://faultforge-checkout-136942862703.us-central1.run.app). Full Knative service YAML in [`infra/cloudrun/service.yaml`](infra/cloudrun/service.yaml) and automated candidate routing / instant traffic rollback in [`scripts/cloudrun_traffic.py`](scripts/cloudrun_traffic.py). Live traffic rollback verified and audited in [`reports/rollback.json`](reports/rollback.json).

---

## 8. Engineering Takeaways & Lessons Learned

1. **Deterministic Baselines Over Ad-Hoc Chaos:** Testing code against arbitrary network delays introduces flakiness. Computing a SHA-256 canonical hash of the Toxiproxy JSON configuration (`644a89784316`) guaranteed that the candidate release was replayed under the exact same 3,500ms delay and 250ms jitter as the baseline failure.
2. **Fail Loudly with Anti-Fake Guards:** Masking exit codes with `|| true` creates dangerous illusions of safety. By enforcing `scripts/truth_audit.py` in Stage 9, FaultForge guarantees that every green checkmark in the 9-stage pipeline represents a real empirical pass.
3. **Platform Constraints in Custom Flow YAML:** GitLab Duo Agent Platform flows reject hardcoded model identifiers (`model: claude-3-5-sonnet`) and top-level names. Decoupling prompts and relying on platform-managed model routing ensures multi-environment portability.
4. **Graceful Fallbacks Over Cascading 504s:** Outbound HTTP dependencies will inevitably degrade. Providing observable fallback responses (`is_fallback: true`, `is_estimate: true`) allows checkout transactions to complete without customer loss while isolating upstream outages.
5. **Supervised Autonomy Is the Enterprise Standard:** Unchecked autonomous agents present severe production hazards. Supervised autonomy lets the agent handle the 99% grunt work of bisecting, testing, and staging deployment, while reserving final traffic migration for the human engineer.

---

## 9. Future Orbit Enhancement & Observability Architecture

GitLab's **Orbit** agent platform tool provides next-generation autonomous incident investigation. Orbit is currently in private beta / behind a feature flag for hackathon namespaces:
- **Future Orbit Integration:** FaultForge is architected to stream live OpenTelemetry spans and Toxiproxy fault events directly into Orbit agent sessions, allowing Orbit to autonomously correlate p95 latency spikes with downstream network topologies.
- **Battle-Tested Platform Fallback:** Because Orbit is not yet globally enabled, FaultForge implements an enterprise-ready fallback path using the GitLab Issues, Notes, Merge Requests, and REST Flows APIs (`scripts/trigger_duo_flow.py`). This guarantees zero dependency on feature-flagged platform capabilities while remaining forward-compatible.

---

## 10. License

This project is licensed under the terms of the [MIT License](LICENSE).
