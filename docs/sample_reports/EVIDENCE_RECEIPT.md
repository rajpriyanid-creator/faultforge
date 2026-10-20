# FaultForge Evidence Receipt & Audit Record

**Receipt ID:** `rcpt-3876c8e2fbdb`  
**Generated At:** `2026-10-20 13:19:01 UTC`  
**Final Status:** **`CONTAINED_NEEDS_REVIEW`**  
**Autonomy Level:** `SUPERVISED` (Supervised Gate)  
**Approver:** `rajpriyanid`  
**Tamper-Evident Seal (SHA-256):** `a3dfe5ab8fdefd831ed75b46d37e3bbc79181fae1dfd33db05bb36728b9ec05d`

---

## 1. Controlled Chaos Experiment & Integrity
- **Injected Fault:** `latency_cascading_hang` (latency)
- **Profile Hash:** `644a89784316`
- **Identical Replay Confirmed:** `True`
- **Duo Run ID:** `unconfirmed`

## 2. Before & After Verified Metrics
| Metric | Baseline (Unpatched) | Hardened (Candidate Patch) |
|---|---|---|
| **Average Latency** | 3446.08 ms | 246.18 ms |
| **p95 Latency** | 3653.06 ms | 817.02 ms |
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
- Cloud Run revision deployment unconfirmed from release stage.
