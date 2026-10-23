# FaultForge Evidence Receipt & Audit Record

**Receipt ID:** `rcpt-730430900cca`  
**Generated At:** `2026-10-23 16:10:06 UTC`  
**Final Status:** **`RECOVERED_AND_VERIFIED`**  
**Autonomy Level:** `SUPERVISED` (Supervised Gate)  
**Approver:** `rajpriyanid`  
**Tamper-Evident Seal (SHA-256):** `bb345ac430daf1b02c4cf2bfce7ed942591c7aa047656d14d191c327bc075d58`

---

## 1. Controlled Chaos Experiment & Integrity
- **Injected Fault:** `latency_cascading_hang` (latency)
- **Profile Hash:** `644a89784316`
- **Identical Replay Confirmed:** `True`
- **Candidate Source:** `commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token`
- **Duo Run ID:** `9909079`
- **Referenced Pipeline URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981969651`
- **Referenced Job URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/jobs/17422097723`
- **Incident Issue URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/issues/48`
- **Duo Merge Request URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3`
- **Duo Flow Run URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079`

## 2. Before & After Verified Metrics
| Metric | Baseline (Unpatched) | Hardened (Candidate Patch) |
|---|---|---|
| **Average Latency** | 3478.57 ms | 484.36 ms |
| **p95 Latency** | 3749.62 ms | 806.83 ms |
| **Graceful Fallback** | Missing (Hangs/Errors) | Active (`is_fallback`: true, `is_estimate`: true) |

## 3. Diagnosis & Culprit Discovery
- **Status:** `CONFIRMED_REGRESSION` (Confidence: `HIGH`)
- **Target Component:** `app/clients/shipping_client.py`
- **Culprit Commit:** `974035c6e45e7c177452df260a155b6508b828e9`

## 4. Governance & Promotion Gate
- **Risk Tier:** `MEDIUM`
- **Promotion Status:** **`BLOCKED_PENDING_APPROVAL`**
- Human reviewer authorization is strictly required for live production traffic migration.

## 5. Items Not Established
- None. All empirical verification gates established.
