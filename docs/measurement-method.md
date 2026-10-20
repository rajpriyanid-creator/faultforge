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

## 2. Measurement Formulas

All latency reduction metrics recorded in `reports/replay_evaluation.json` and reported across documentation are deterministically computed using the formulas below:

### A. 95th Percentile (P95) Latency Reduction
Measures tail latency protection under severe dependency degradation:

$$\text{P95 Reduction (\%)} = \left( \frac{\text{Baseline P95 (ms)} - \text{Candidate P95 (ms)}}{\text{Baseline P95 (ms)}} \right) \times 100$$

- **Baseline P95:** ~3,742.46 ms (unconstrained downstream hang)
- **Candidate P95:** ~814.00 ms (bounded by 0.8s strict client timeout)
- **Computed Reduction:** **78.3%** tail latency reduction

### B. Mean (Average) Latency Reduction
Measures aggregate throughput improvement across both timeout and circuit-breaker short-circuit phases:

$$\text{Mean Reduction (\%)} = \left( \frac{\text{Baseline Mean (ms)} - \text{Candidate Mean (ms)}}{\text{Baseline Mean (ms)}} \right) \times 100$$

- **Baseline Mean:** ~3,600.00 ms
- **Candidate Mean (Phase A + Phase B Combined):** ~528.00 ms
- **Computed Reduction:** **~85.3%** (or **~93.2%** during Phase B breaker-open short-circuit)

---

## 3. Two-Phase Replay Verification

FaultForge separates timeout verification from circuit-breaker short-circuit verification into two distinct gates in `scripts/evaluate_replay.py`:

| Phase | Evaluation Gate | Execution Semantics | Probes | Target Latency | Status |
|---|---|---|---|---|---|
| **Phase A** | `candidate_timeout_only` | Circuit breaker reset before every probe; strictly exercises the 0.8s bounded timeout path with fallback quote. | 10 probes | ~812 ms (all $\le 1,500$ ms) | PASS |
| **Phase B** | `candidate_breaker_short_circuit` | Circuit breaker enabled; probes 1–3 trip the breaker, probes 4–10 are immediately short-circuited (~2ms). | 10 probes | 7 / 10 short-circuited | PASS |

---

## 4. Anti-Fake Policy on Percentage Claims

- Documentation and dashboard must explicitly cite the basis when quoting percentage improvements (e.g. *"78.3% P95 latency reduction"* or *"~85% mean latency reduction"*).
- No hardcoded numbers: all values displayed in the dashboard are dynamically read from `reports/replay_evaluation.json` (`latency_reduction` object).
