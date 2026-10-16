# FaultForge Measurement & Verification Methodology

**Revision:** 2.0 (Empirical Measurements)  
**Track:** Path A — Start Fresh  

---

## 1. Core Principle: Zero Fabrication Policy

FaultForge operates strictly on empirical, machine-readable pipeline measurements. In adherence to Hackathon Rule 1:
- **No Hardcoded Metrics:** Every latency, status code, hash, and SHA in reports originates from an active execution run.
- **No Simulated Chaos:** Network latency is injected exclusively via Toxiproxy sockets; no `time.sleep()` or mocked HTTP clients are permitted in fault evidence.
- **Fail Loudly:** Masked failures (`|| true`, `|| echo`, `allow_failure: true` on quality gates) are prohibited.
- **Verified Provenance:** All commit SHAs are cross-checked against git history; receipts record whether the environment used the official Shopify Toxiproxy container or the standalone fallback.

---

## 2. Measurable Key Performance Indicators (KPIs)

| Metric | Definition | Measurement Source | Target / Observed Baseline | Candidate Hardened Target |
|---|---|---|---|---|
| **SLA Budget Breach Count** | Probes taking longer than the 1500ms latency budget | `scripts/run_fault.py` | Observed: 5/5 breaches (100%) | Exactly 0 breaches (0%) |
| **Average Latency (Avg)** | Arithmetic mean roundtrip duration | `reports/fault_run_baseline.json` | Observed: 3742.46 ms | < 850 ms (>60% reduction) |
| **95th Percentile Latency (p95)** | 95th percentile latency across probe distribution | `reports/fault_run_baseline.json` | Observed: 3918.27 ms | < 1500 ms |
| **Fallback Invocation Rate** | Percentage of degraded probes returning fallback quote | `app/clients/shipping_client.py` | Observed: 0% (unbounded hang) | 100% under degraded fault |
| **Fallback Estimation Flag** | Mandatory metadata distinguishing estimates from live rates | Checkout API response payload | N/A (baseline hangs) | Both `is_fallback: true` and `is_estimate: true` present |
| **Consecutive Candidate Passes** | Sequential passing probes required during replay verification | `chaos/criteria.json` | N/A (baseline fails) | 10 consecutive passes |
| **Toxic Read-Back Parity** | Verification that toxic configuration was identical | `chaos/toxiproxy_helper.py` | Recorded: latency 3500ms, jitter 250ms | Must match baseline toxic read-back identically |

---

## 3. The Exact-Fault Replay Gate

A candidate release is validated as `RECOVERED_AND_VERIFIED` if and only if all of the following empirical criteria are satisfied:

1. **Baseline Failure Established:** The unpatched application at HEAD reproducibly breaches the 1500ms SLA budget across all 5 initial probes (observed 3742.46ms avg).
2. **Identical Toxic Configuration Replayed:** The candidate patch is subjected to the exact same Toxiproxy toxic configuration, verified by toxic read-back parameters (`latency: 3500`, `jitter: 250`) and payload hash matching.
3. **10 Consecutive Candidate Passes:** The candidate service completes 10 consecutive probe executions without a single SLA breach or 5xx error.
4. **Observable Fallback Marked:** Fallback responses return HTTP 200 with `is_fallback: true` and `is_estimate: true`.
5. **Independent Service Health Verified:** `/health` endpoint responds HTTP 200 and emits the matching `X-Service-Revision` header.
6. **Cryptographic Seal Affixed:** Composite artifact hashes are signed into `reports/evidence_receipt.json` with a SHA-256 tamper-evident seal.
