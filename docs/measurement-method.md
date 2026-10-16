# FaultForge Measurement & Verification Methodology

## 1. Core Principle: Zero Fabrication Policy

FaultForge operates on empirical, machine-readable pipeline measurements. The system strictly prohibits:
- Hardcoded or illustrative latency claims presented as actual test results.
- Inventing commit SHAs or fabricated root-cause blame.
- Declaring recovery without an independent passing health probe.

---

## 2. Measurable Key Performance Indicators (KPIs)

| Metric | Definition | Collection Tool | Target Gate |
|---|---|---|---|
| **SLA Budget Breach Count** | Number of checkout requests exceeding the 1500ms budget under 3500ms dependency latency | `scripts/run_fault.py` | Baseline: >0 (Fail)<br>Hardened: 0 (Pass) |
| **Average Latency (Avg)** | Mean roundtrip duration across N probe iterations | `scripts/run_fault.py` | Reduced by >60% post-hardening |
| **p95 Latency** | 95th percentile latency across sample distribution | `app/resilience/metrics.py` | Must remain < 1500ms under fault |
| **Fallback Invocation Rate** | Percentage of requests successfully returning standard fallback quote | `app/main.py` | 100% of degraded requests |
| **Error Rate (5xx)** | Percentage of unhandled gateway timeouts or internal errors | `reports/fault_run_result.json` | 0.0% post-hardening |
| **Profile Integrity Hash** | Canonical SHA-256 hash of Toxiproxy toxic configuration | `scripts/run_fault.py` | `baseline_hash == hardened_hash` |

---

## 3. The Exact-Fault Replay Gate

A candidate release is considered verified if and only if:
1. **Baseline Failure Established:** The unpatched application reproducibly fails the latency SLA or raises a 5xx error under the declared chaos profile.
2. **Identical Replay Executed:** The candidate patch is subjected to the exact same Toxiproxy configuration (verified by canonical SHA-256 profile hash).
3. **Graceful Fallback Observable:** The hardened service returns a successful HTTP 200 with `"is_fallback": true` within the SLA budget.
4. **Independent Health Probe Passes:** The `/health` and `/ready` endpoints return HTTP 200 confirming process health.
5. **Tamper-Evident Seal Generated:** A cryptographic SHA-256 seal is generated over the composite test artifacts in `reports/evidence_receipt.json`.
