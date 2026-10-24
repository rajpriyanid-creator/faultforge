# FaultForge Evidence Receipt & Audit Record

**Receipt ID:** `rcpt-0fdcbef2fed6`  
**Generated At:** `2026-10-24 13:31:08 UTC`  
**Final Status:** **`RECOVERED_AND_VERIFIED`**  
**Autonomy Level:** `SUPERVISED` (Supervised Gate)  
**Approver:** `rajpriyanid`  
**Receipt Source:** `baked_image_receipt (pipeline 2984589851, commit d75de80a)`  
**Tamper-Evident Seal (SHA-256):** `c62ee3b35d29dcc013f4d70ab6a230892886911c83674f9b91b02a2d6846de23`

---

## 1. Controlled Chaos Experiment & Integrity
- **Injected Fault:** `latency_cascading_hang` (latency)
- **Profile Hash:** `644a89784316`
- **Identical Replay Confirmed:** `True`
- **Candidate Source:** `commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token`
- **Duo Run ID:** `9909079`
- **Referenced Pipeline URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984589851`
- **Referenced Job URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/jobs/17438210914`
- **Incident Issue URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/issues/62`
- **Duo Merge Request URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3`
- **Duo Flow Run URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079`
- **Replay App Tree SHA:** `de7c0b1cc7d6b7edb90c6b3041b10885ea702492`
- **Deployed App Tree SHA:** `de7c0b1cc7d6b7edb90c6b3041b10885ea702492`
- **App Tree Parity Verified:** `True`

## 2. Before & After Verified Metrics
| Metric | Baseline (Unpatched) | Hardened (Candidate Patch) |
|---|---|---|
| **Average Latency** | 3637.98 ms | 487.92 ms |
| **p95 Latency** | 3699.48 ms | 813.32 ms |
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
