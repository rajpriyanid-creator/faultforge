# FaultForge Evidence Receipt & Audit Record

**Receipt ID:** `rcpt-fcde72b26ebf`  
**Generated At:** `2026-10-23 03:44:01 UTC`  
**Final Status:** **`CONTAINED_NEEDS_REVIEW`**  
**Autonomy Level:** `SUPERVISED` (Supervised Gate)  
**Approver:** `SUPERVISED_OPERATOR`  
**Tamper-Evident Seal (SHA-256):** `05dfdca7d72b1fb9e9dd36f9a652d3a24c683437837bce74bb7786d6dc68b156`

---

## 1. Controlled Chaos Experiment & Integrity
- **Injected Fault:** `latency_cascading_hang` (latency)
- **Profile Hash:** `644a89784316`
- **Identical Replay Confirmed:** `True`
- **Candidate Source:** `commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token`
- **Duo Run ID:** `9909079`
- **Pipeline URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/pipelines/2977803091`
- **Incident Issue URL:** `https://gitlab.com/gitlab-ai-hackathon/transcend-october-2026/43424456/showcase/-/work_items/42`
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
- Dossier commit SHA (b063a91b) differs from current HEAD (372ef5f9).
- Cloud Run revision deployment unconfirmed from release stage.
