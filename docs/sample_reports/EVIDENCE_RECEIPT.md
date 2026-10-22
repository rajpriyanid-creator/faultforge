# FaultForge Evidence Receipt & Audit Record

**Receipt ID:** `rcpt-9d6818a1b938`  
**Generated At:** `2026-10-22 17:44:53 UTC`  
**Final Status:** **`CONTAINED_NEEDS_REVIEW`**  
**Autonomy Level:** `SUPERVISED` (Supervised Gate)  
**Approver:** `SUPERVISED_OPERATOR`  
**Tamper-Evident Seal (SHA-256):** `f38e2cf55b0b789ba4bba6ed3cb1476b16e7263af62ad0e7a5ee0c72028e586b`

---

## 1. Controlled Chaos Experiment & Integrity
- **Injected Fault:** `latency_cascading_hang` (latency)
- **Profile Hash:** `644a89784316`
- **Identical Replay Confirmed:** `True`
- **Candidate Source:** `duo-authored (MR !3)`
- **Duo Run ID:** `9909079`
- **Pipeline URL:** `not established`
- **Incident Issue URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/issues/29`
- **Duo Merge Request URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3`
- **Duo Flow Run URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079`

## 2. Before & After Verified Metrics
| Metric | Baseline (Unpatched) | Hardened (Candidate Patch) |
|---|---|---|
| **Average Latency** | 4212.32 ms | 825.56 ms |
| **p95 Latency** | 4349.98 ms | 1472.12 ms |
| **Graceful Fallback** | Missing (Hangs/Errors) | Active (`is_fallback`: true, `is_estimate`: true) |

## 3. Diagnosis & Culprit Discovery
- **Status:** `SUSPECTED_WEAKNESS` (Confidence: `MEDIUM`)
- **Target Component:** `app/clients/shipping_client.py`
- **Culprit Commit:** `Hypothesized via AST`

## 4. Governance & Promotion Gate
- **Risk Tier:** `MEDIUM`
- **Promotion Status:** **`BLOCKED_PENDING_REVIEW`**
- Human reviewer authorization is strictly required for live production traffic migration.

## 5. Items Not Established
- Cloud Run revision deployment unconfirmed from release stage.
