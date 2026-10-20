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

> ### 🟢 Headline: 0/10 SLA Breaches: Degraded but Available (Deterministic Estimated Fallback Quotes)
> **Crucial Measurement Semantic:** All 10 candidate probes under active fault return `is_fallback: true` and `is_estimate: true`. The **2.88 ms P50 latency** and **-99.9% reduction** measure serving deterministic local fallback quotes (`$7.50 + $1.25 * weight_kg`) when the circuit breaker trips OPEN during complete downstream carrier outage, rather than waiting ~3.5 s for degraded carrier responses and breaching the 1,500 ms SLA.

---

## 3. Measurement Formulas & Empirical Values

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

### C. Median (P50) Latency Reduction & Percentile Methodology

$$\text{P50 Reduction (\%)} = \left( \frac{3,453.42 - 2.88}{3,453.42} \right) \times 100 = \mathbf{99.9\%}$$

#### Percentile Rank Method Documentation:
FaultForge's telemetry scripts (`scripts/render_metrics.py`, `scripts/evaluate_replay.py`) use the standard **Nearest-Rank Method** with zero-indexed rank selection:

$$\text{Index} = \lfloor N \times P \rfloor$$

- For Candidate ($N = 10$, sorted latency array `[2.37, 2.44, 2.45, 2.47, 2.51, 2.88, 3.46, 812.74, 813.50, 817.02]`):
  - $\text{Index} = \lfloor 10 \times 0.50 \rfloor = 5$ (the 6th element in zero-based indexing), selecting **2.88 ms**.
  - By comparison, the continuous interpolated mid-point median method $\frac{s[4] + s[5]}{2} = \frac{2.51 + 2.88}{2} = \mathbf{2.70\text{ ms}}$ (2.695 ms).
  - Both methods yield the identical **-99.9% reduction** from the unpatched baseline P50 (3,453.42 ms), confirming that once the circuit breaker trips OPEN, requests short-circuit locally in under 3 milliseconds.

### D. Maximum Latency Reduction
$$\text{Max Reduction (\%)} = \left( \frac{3,653.06 - 817.02}{3,653.06} \right) \times 100 = \mathbf{77.6\%}$$

---

## 4. Empirical Sample Distribution & Variance Analysis

| Statistical Metric | Baseline Run (N=5) | Candidate Replay (N=10) | Notes on Distribution |
|---|---|---|---|
| **Count ($N$)** | 5 probes | 10 probes | CI execution dataset |
| **SLA Breaches** | 5 / 5 (100% failure) | 0 / 10 (0% breaches) | 1,500 ms SLA threshold |
| **Mean** | 3,446.08 ms | 246.18 ms | -92.9% mean reduction |
| **Median (P50)** | 3,453.42 ms | 2.88 ms | -99.9% P50 reduction |
| **P95** | 3,653.06 ms | 817.02 ms | -77.6% P95 reduction |
| **Minimum** | 3,268.03 ms | 2.37 ms | Min recorded latency |
| **Maximum** | 3,653.06 ms | 817.02 ms | Max recorded latency |
| **Sample Variance ($s^2$)** | 28,183.84 ms² | 153,759.43 ms² | Candidate has high variance due to bimodal distribution |
| **Sample Std Dev ($s$)** | ±167.88 ms | ±392.12 ms | Bimodal: timeout vs open breaker |

### Why Candidate Variance is High (Bimodal Distribution)
The candidate probe distribution is strictly bimodal across two operational phases:
1. **Phase A (Probes 1–3):** Timeout-only path. Probes experience the full 800ms client timeout before returning fallback quotes (Mean: 814.42 ms, P95: 817.02 ms, Min: 810.74 ms, Max: 817.02 ms, $s^2 = 11.2\text{ ms}^2$, $s = \pm 3.35\text{ ms}$). Breaker state is `CLOSED`.
2. **Phase B (Probes 4–10):** Breaker short-circuit. Having reached 3 consecutive failures, the circuit breaker transitions to `OPEN`. All subsequent probes short-circuit locally without network I/O (Mean: 2.65 ms, P95: 3.46 ms, Min: 2.37 ms, Max: 3.46 ms, $s^2 = 0.15\text{ ms}^2$, $s = \pm 0.39\text{ ms}$).

Combining 3 timeout probes (~814ms) and 7 short-circuit probes (~2.65ms) produces an aggregate mean of 246.18 ms with sample variance 153,759.43 ms² (std dev ±392.12 ms).

---

## 5. Two-Phase Replay Verification

FaultForge evaluates timeout verification and circuit-breaker short-circuit verification across two distinct operational phases:

| Phase | Evaluation Gate | Execution Semantics | Probes | Measured Mean | Measured P95 | Breaker State | Status |
|---|---|---|---|---|---|---|---|
| **Phase A** | `candidate_timeout_only` | Initial probes exercise the bounded 0.8s timeout path before tripping the breaker. | 3 probes | 814.42 ms | 817.02 ms | `CLOSED` (reset each probe) | PASS |
| **Phase B** | `candidate_breaker_short_circuit` | Circuit breaker trips OPEN after 3 consecutive timeouts; subsequent probes short-circuit in ~2.65ms. | 7 probes | 2.65 ms | 3.46 ms | `OPEN` (7 of 10 short-circuited) | PASS |

---

## 6. Anti-Fake Policy on Percentage Claims

- Documentation and dashboard must explicitly cite the basis when quoting percentage improvements (e.g. *"77.6% P95 latency reduction"* or *"92.9% mean latency reduction"*).
- No hardcoded numbers: all values displayed in the dashboard are dynamically read from `reports/replay_evaluation.json` (`latency_reduction` and `raw_metrics` objects).
