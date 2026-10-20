# FaultForge Latency Reduction & Measurement Methodology
# SPDX-License-Identifier: MIT

This document defines the mathematical formulas, measurement conditions, and experimental phases used to evaluate FaultForge resilience and compute latency reduction metrics.

---

## 1. Experimental Conditions

- **Downstream Injected Fault:** Shopify Toxiproxy v2.9.0
- **Toxic Profile:** `latency_cascading_hang` (Profile Hash: `644a89784316`)
- **Configured Toxic Delay:** 3,500ms delay with 250ms jitter
- **SLA Budget Threshold:** 1,500.00ms
- **Target Microservice:** FastAPI Checkout Service (`/api/v1/checkout`)

---

## 2. Measurement Formulas & Empirical Values

All latency reduction metrics recorded in `reports/replay_evaluation.json` and rendered by `scripts/render_metrics.py` are deterministically computed using the formulas below:

### A. 95th Percentile (P95) Latency Reduction
Measures tail latency protection under severe dependency degradation:

$$\text{P95 Reduction (\%)} = \left( \frac{\text{Baseline P95 (ms)} - \text{Candidate P95 (ms)}}{\text{Baseline P95 (ms)}} \right) \times 100$$

- **Baseline P95:** 3,653.06 ms (unconstrained downstream hang)
- **Candidate P95:** 817.02 ms (bounded by 0.8s strict client timeout)
- **Computed Reduction:** **77.6%** tail latency reduction

### B. Mean (Average) Latency Reduction
Measures aggregate throughput improvement across both timeout and circuit-breaker short-circuit phases:

$$\text{Mean Reduction (\%)} = \left( \frac{\text{Baseline Mean (ms)} - \text{Candidate Mean (ms)}}{\text{Baseline Mean (ms)}} \right) \times 100$$

- **Baseline Mean:** 3,446.08 ms
- **Candidate Mean:** 246.18 ms
- **Computed Reduction:** **92.9%** mean latency reduction

### C. Median (P50) Latency Reduction
$$\text{P50 Reduction (\%)} = \left( \frac{3,453.42 - 2.88}{3,453.42} \right) \times 100 = \mathbf{99.9\%}$$

### D. Maximum Latency Reduction
$$\text{Max Reduction (\%)} = \left( \frac{3,653.06 - 817.02}{3,653.06} \right) \times 100 = \mathbf{77.6\%}$$

---

## 3. Two-Phase Replay Verification

FaultForge evaluates timeout verification and circuit-breaker short-circuit verification across two distinct operational phases:

| Phase | Evaluation Gate | Execution Semantics | Probes | Measured Mean | Measured P95 | Breaker State | Status |
|---|---|---|---|---|---|---|---|
| **Phase A** | `candidate_timeout_only` | Initial probes exercise the bounded 0.8s timeout path before tripping the breaker. | 3 probes | 814.42 ms | 817.02 ms | `CLOSED` (reset each probe) | PASS |
| **Phase B** | `candidate_breaker_short_circuit` | Circuit breaker trips OPEN after 3 consecutive timeouts; subsequent probes short-circuit in ~2.65ms. | 7 probes | 2.65 ms | 3.46 ms | `OPEN` (7 of 10 short-circuited) | PASS |

---

## 4. Anti-Fake Policy on Percentage Claims

- Documentation and dashboard must explicitly cite the basis when quoting percentage improvements (e.g. *"77.6% P95 latency reduction"* or *"92.9% mean latency reduction"*).
- No hardcoded numbers: all values displayed in the dashboard are dynamically read from `reports/replay_evaluation.json` (`latency_reduction` and `raw_metrics` objects).
