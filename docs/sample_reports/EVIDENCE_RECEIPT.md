# FaultForge Evidence Receipt & Audit Record

**Receipt ID:** `rcpt-91fa551afd88`  
**Generated At:** `2026-10-24 08:46:07 UTC`  
**Final Status:** **`RECOVERED_AND_VERIFIED`**  
**Autonomy Level:** `SUPERVISED` (Supervised Gate)  
**Approver:** `rajpriyanid`  
**Tamper-Evident Seal (SHA-256):** `69fe40c67b5ecd4d8c8c23d07c903f41f62d062a553988df28dd3576b4d65cb0`

---

## 1. Controlled Chaos Experiment & Integrity
- **Injected Fault:** `latency_cascading_hang` (latency)
- **Profile Hash:** `644a89784316`
- **Identical Replay Confirmed:** `True`
- **Candidate Source:** `commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token`
- **Duo Run ID:** `9909079`
- **Referenced Pipeline URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2984172017`
- **Referenced Job URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/jobs/17436072843`
- **Incident Issue URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/issues/62`
- **Duo Merge Request URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/merge_requests/3`
- **Duo Flow Run URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/automate/agent-sessions/9909079`
- **Replay App Tree SHA:** `5bd23d542337f74dff3320fdd8d7909c17d57e27`
- **Deployed App Tree SHA:** `5bd23d542337f74dff3320fdd8d7909c17d57e27`
- **App Tree Parity Verified:** `True`

## 2. Before & After Verified Metrics
| Metric | Baseline (Unpatched) | Hardened (Candidate Patch) |
|---|---|---|
| **Average Latency** | 3652.0 ms | 488.75 ms |
| **p95 Latency** | 3718.82 ms | 815.41 ms |
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
