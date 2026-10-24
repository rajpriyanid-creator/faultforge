# FaultForge Evidence Receipt & Audit Record

**Receipt ID:** `rcpt-4158e479bbce`  
**Generated At:** `2026-10-24 09:51:05 UTC`  
**Final Status:** **`RECOVERED_AND_VERIFIED`**  
**Autonomy Level:** `SUPERVISED` (Supervised Gate)  
**Approver:** `rajpriyanid`  
**Tamper-Evident Seal (SHA-256):** `4a58ba4daec1bd1313051b8b054f27bb9681da87af1878481a686f32ce8cc2d3`

---

## 1. Controlled Chaos Experiment & Integrity
- **Injected Fault:** `latency_cascading_hang` (latency)
- **Profile Hash:** `644a89784316`
- **Identical Replay Confirmed:** `True`
- **Candidate Source:** `commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token`
- **Duo Run ID:** `9909079`
- **Referenced Pipeline URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984259115`
- **Referenced Job URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/jobs/17436543228`
- **Incident Issue URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/issues/62`
- **Duo Merge Request URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3`
- **Duo Flow Run URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079`
- **Replay App Tree SHA:** `5bd23d542337f74dff3320fdd8d7909c17d57e27`
- **Deployed App Tree SHA:** `5bd23d542337f74dff3320fdd8d7909c17d57e27`
- **App Tree Parity Verified:** `True`

## 2. Before & After Verified Metrics
| Metric | Baseline (Unpatched) | Hardened (Candidate Patch) |
|---|---|---|
| **Average Latency** | 3572.47 ms | 488.2 ms |
| **p95 Latency** | 3678.92 ms | 814.05 ms |
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
