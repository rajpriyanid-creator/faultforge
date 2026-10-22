# FaultForge Latency Reduction & Measurement Methodology
# SPDX-License-Identifier: MIT

This document defines the mathematical formulas, measurement conditions, experimental phases, and statistical distributions used to evaluate FaultForge resilience and compute latency reduction metrics.

---

## 1. Experimental Conditions

- **Downstream Injected Fault:** Shopify Toxiproxy v2.9.0
- **Toxic Profile:** `latency_cascading_hang` (Profile Hash: `644a89784316`)
- **Configured Toxic Delay:** 3,500ms delay with 250ms jitter
- **SLA Budget Threshold:** 1,500.00ms
- **Target Microservice:** FastAPI Checkout Service (`/api/v1/checkout`)

---

## 2. Headline Result: Degraded but Available

> ### 🟢 Headline: 0/20 SLA Breaches: Degraded but Available (Deterministic Estimated Fallback Quotes)
> **Crucial Measurement Semantic:** All candidate probes under active fault return `is_fallback: true` and `is_estimate: true`. The **1331.90 ms P50 latency** and **-68.4% reduction** measure serving deterministic local fallback quotes (`$7.50 + $1.25 * weight_kg`) rather than waiting ~4.2 s for degraded carrier responses and breaching the 1,500 ms SLA.

---

## 3. Measurement Formulas & Empirical Values

All latency reduction metrics recorded in `reports/replay_evaluation.json` and rendered by `scripts/render_metrics.py` are deterministically computed using the formulas below:

### A. 95th Percentile (P95) Latency Reduction
Measures tail latency protection under severe dependency degradation:

$$\text{P95 Reduction (\%)} = \left( \frac{\text{Baseline P95 (ms)} - \text{Candidate P95 (ms)}}{\text{Baseline P95 (ms)}} \right) \times 100$$

- **Baseline P95:** 4,349.98 ms (unconstrained downstream hang)
- **Candidate P95:** 1,472.12 ms (bounded by strict client SLA budget <= 1500ms)
- **Computed Reduction:** **66.2%** tail latency reduction

### B. Mean (Average) Latency Reduction
Measures aggregate throughput improvement across both timeout and circuit-breaker short-circuit phases:

$$\text{Mean Reduction (\%)} = \left( \frac{\text{Baseline Mean (ms)} - \text{Candidate Mean (ms)}}{\text{Baseline Mean (ms)}} \right) \times 100$$

- **Baseline Mean:** 4,212.32 ms
- **Candidate Mean:** 825.56 ms
- **Computed Reduction:** **80.4%** mean latency reduction

### C. Median (P50) Latency Reduction & Percentile Methodology

$$\text{P50 Reduction (\%)} = \left( \frac{4,219.23 - 1,331.90}{4,219.23} \right) \times 100 = \mathbf{68.4\%}$$

#### Percentile Rank Method Documentation:
FaultForge's telemetry script `scripts/render_metrics.py` uses the standard **Nearest-Rank Method** with zero-indexed rank selection:

$$\text{Index} = \lfloor N \times P \rfloor$$

### D. Maximum Latency Reduction
$$\text{Max Reduction (\%)} = \left( \frac{4,349.98 - 1,472.12}{4,349.98} \right) \times 100 = \mathbf{66.2\%}$$

---

## 4. Empirical Sample Distribution & Variance Analysis

| Statistical Metric | Baseline Run (N=5) | Candidate Replay (N=20) | Notes on Distribution |
|---|---|---|---|
| **Count ($N$)** | 5 probes | 20 probes | CI execution dataset |
| **SLA Breaches** | 5 / 5 (100% failure) | 0 / 20 (0% breaches) | 1,500 ms SLA threshold |
| **Mean** | 4,212.32 ms | 825.56 ms | -80.4% mean reduction |
| **Median (P50)** | 4,219.23 ms | 1,331.90 ms | -68.4% P50 reduction |
| **P95** | 4,349.98 ms | 1,472.12 ms | -66.2% P95 reduction |
| **Minimum** | 3,986.93 ms | 5.23 ms | Min recorded latency |
| **Maximum** | 4,349.98 ms | 1,472.12 ms | Max recorded latency |
| **Sample Variance ($s^2$)** | 19,500.70 ms² | 471,322.45 ms² | Candidate has high variance due to bimodal distribution |
| **Sample Std Dev ($s$)** | ±139.64 ms | ±686.53 ms | Bimodal: timeout vs open breaker |

### Why Candidate Variance is High (Bimodal Distribution)
The candidate probe distribution is strictly bimodal across two operational phases:
1. **Phase A (Timeout-Only SLA Enforcement):** Probes exercise the bounded timeout path before tripping the breaker (Mean: 1371.08 ms, P95: 1472.12 ms). Breaker state is `CLOSED (reset each probe)`.
2. **Phase B (Circuit Breaker Tripped - Short Circuit):** Circuit breaker transitions to `OPEN`. Probes short-circuit locally in ~7.28 ms (Min: 5.23 ms, P95: 11.38 ms).

---

## 5. Two-Phase Replay Verification

FaultForge evaluates timeout verification and circuit-breaker short-circuit verification across two distinct operational phases:

| Phase | Evaluation Gate | Execution Semantics | Probes | Measured Mean | Measured P95 | Breaker State | Status |
|---|---|---|---|---|---|---|---|
| **Phase A** | `candidate_timeout_only` | Initial probes exercise the bounded timeout path within SLA budget. | 12 probes | 1371.08 ms | 1472.12 ms | `CLOSED` (reset each probe) | PASS |
| **Phase B** | `candidate_breaker_short_circuit` | Circuit breaker trips OPEN; subsequent probes short-circuit locally in ~7.28ms. | 8 probes | 7.28 ms | 11.38 ms | `OPEN` (8 of 20 short-circuited) | PASS |

---

## 6. Anti-Fake Policy on Percentage Claims

- Documentation and dashboard must explicitly cite the basis when quoting percentage improvements (e.g. *"77.6% P95 latency reduction"* or *"92.9% mean latency reduction"*).
- No hardcoded numbers: all values displayed in the dashboard are dynamically read from `reports/replay_evaluation.json` (`latency_reduction` and `raw_metrics` objects).
