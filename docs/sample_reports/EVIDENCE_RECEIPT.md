# FaultForge Evidence Receipt & Audit Record

**Receipt ID:** `rcpt-4d7b25040977`  
**Generated At:** `2026-10-23 14:54:54 UTC`  
**Final Status:** **`CONTAINED_NEEDS_REVIEW`**  
**Autonomy Level:** `SUPERVISED` (Supervised Gate)  
**Approver:** `rajpriyanid`  
**Tamper-Evident Seal (SHA-256):** `77fcdade74cbb5040bf7301b4bb8c55827e3c15fab3dbae8e679fe18e1ae8a40`

---

## 1. Controlled Chaos Experiment & Integrity
- **Injected Fault:** `latency_cascading_hang` (latency)
- **Profile Hash:** `644a89784316`
- **Identical Replay Confirmed:** `True`
- **Candidate Source:** `reference-fix (not Duo-authored)`
- **Duo Run ID:** `9909079`
- **Referenced Pipeline URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2981670120`
- **Referenced Job URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/jobs/17419950472`
- **Incident Issue URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/42`
- **Duo Merge Request URL:** `not established`
- **Duo Flow Run URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079`

## 2. Before & After Verified Metrics
| Metric | Baseline (Unpatched) | Hardened (Candidate Patch) |
|---|---|---|
| **Average Latency** | 3454.97 ms | 124.24 ms |
| **p95 Latency** | 3541.19 ms | 817.61 ms |
| **Graceful Fallback** | Missing (Hangs/Errors) | Active (`is_fallback`: true, `is_estimate`: true) |

## 3. Diagnosis & Culprit Discovery
- **Status:** `CONFIRMED_REGRESSION` (Confidence: `HIGH`)
- **Target Component:** `app/clients/shipping_client.py`
- **Culprit Commit:** `974035c6e45e7c177452df260a155b6508b828e9`

## 4. Governance & Promotion Gate
- **Risk Tier:** `MEDIUM`
- **Promotion Status:** **`BLOCKED_PENDING_REVIEW`**
- Human reviewer authorization is strictly required for live production traffic migration.

## 5. Items Not Established
- GitLab Duo flow execution
- Candidate authored by Duo
