# FaultForge Evidence Receipt & Audit Record

**Receipt ID:** `rcpt-a924d06a7614`  
**Generated At:** `2026-10-16 14:18:20 UTC`  
**Final Status:** **`NOT_VERIFIED`**  
**Autonomy Level:** `SUPERVISED` (Supervised Gate)  
**Approver:** `SUPERVISED_OPERATOR`  
**Tamper-Evident Seal (SHA-256):** `391e8824de808f1190d7af3e23f3673080a4c6e662f2ce56e661e7135511bc31`

---

## 1. Controlled Chaos Experiment & Integrity
- **Injected Fault:** `latency_cascading_hang` (latency)
- **Profile Hash:** `None`
- **Identical Replay Confirmed:** `False`
- **Duo Run ID:** `None`

## 2. Before & After Verified Metrics
| Metric | Baseline (Unpatched) | Hardened (Candidate Patch) |
|---|---|---|
| **Average Latency** | N/A ms | N/A ms |
| **p95 Latency** | N/A ms | N/A ms |
| **Graceful Fallback** | Missing (Hangs/Errors) | Active (`is_fallback`: true, `is_estimate`: true) |

## 3. Diagnosis & Culprit Discovery
- **Status:** `CONFIRMED_REGRESSION` (Confidence: `HIGH`)
- **Target Component:** `app/clients/shipping_client.py`
- **Culprit Commit:** `974035c6e45e7c177452df260a155b6508b828e9`

## 4. Governance & Promotion Gate
- **Risk Tier:** `LOW`
- **Promotion Status:** **`REJECTED`**
- Human reviewer authorization is strictly required for live production traffic migration.

## 5. Items Not Established
- Exact fault profile hash match could not be established across baseline and hardened runs.
- Dossier commit SHA (e53f1d35) differs from current HEAD (c44795c9).
- GitLab Duo remote run ID unconfirmed (local or API trigger pending).
- Complete 15-probe run evidence incomplete (found 5/15).
- Container image digest unconfirmed from package stage.
- Cloud Run revision deployment unconfirmed from release stage.
