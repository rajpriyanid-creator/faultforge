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
> **Crucial Measurement Semantic:** All candidate probes under active fault return `is_fallback: true` and `is_estimate: true`. The **808.95 ms P50 latency** and **-86.3% mean reduction** measure serving deterministic local fallback quotes (`$7.50 + $1.25 * weight_kg`) rather than waiting ~3.5–3.7 s for degraded carrier responses and breaching the 1,500 ms SLA.

---

## 3. Measurement Formulas & Empirical Values

All latency reduction metrics recorded in `reports/replay_evaluation.json` and rendered by `scripts/render_metrics.py` are deterministically computed using the formulas below from the active CI pipeline run:

### A. 95th Percentile (P95) Latency Reduction
Measures tail latency protection under severe dependency degradation:

$$\text{P95 Reduction (\%)} = \left( \frac{\text{Baseline P95 (ms)} - \text{Candidate P95 (ms)}}{\text{Baseline P95 (ms)}} \right) \times 100$$

- **Baseline P95:** 3,634.58 ms (unconstrained downstream hang)
- **Candidate P95:** 812.51 ms (bounded by strict client SLA budget <= 1500ms)
- **Computed Reduction:** **77.6%** tail latency reduction

### B. Mean (Average) Latency Reduction
Measures aggregate throughput improvement across both timeout and circuit-breaker short-circuit phases:

$$\text{Mean Reduction (\%)} = \left( \frac{\text{Baseline Mean (ms)} - \text{Candidate Mean (ms)}}{\text{Baseline Mean (ms)}} \right) \times 100$$

- **Baseline Mean:** 3,557.22 ms
- **Candidate Mean:** 487.12 ms
- **Computed Reduction:** **86.3%** mean latency reduction

### C. Median (P50) Latency Reduction & Percentile Methodology

$$\text{P50 Reduction (\%)} = \left( \frac{3,561.40 - 808.95}{3,561.40} \right) \times 100 = \mathbf{77.3\%}$$

#### Percentile Rank Method Documentation:
FaultForge's telemetry script `scripts/render_metrics.py` uses the standard **Nearest-Rank Method** with zero-indexed rank selection:

$$\text{Index} = \lfloor N \times P \rfloor$$

### D. Maximum Latency Reduction
$$\text{Max Reduction (\%)} = \left( \frac{3,634.58 - 812.51}{3,634.58} \right) \times 100 = \mathbf{77.6\%}$$

---

## 4. Empirical Sample Distribution & Variance Analysis

| Statistical Metric | Baseline Run (N=5) | Candidate Replay (N=20) | Notes on Distribution |
|---|---|---|---|
| **Count ($N$)** | 5 probes | 20 probes | CI execution dataset (`reports/replay_evaluation.json`) |
| **SLA Breaches** | 5 / 5 (100% failure) | 0 / 20 (0% breaches) | 1,500 ms SLA threshold |
| **Mean** | 3,557.22 ms | 487.12 ms | -86.3% mean reduction |
| **Median (P50)** | 3,561.40 ms | 808.95 ms | -77.3% P50 reduction |
| **P95** | 3,634.58 ms | 812.51 ms | -77.6% P95 reduction |
| **Minimum** | 3,312.60 ms | 1.91 ms | Min recorded latency |
| **Maximum** | 3,634.58 ms | 812.51 ms | Max recorded latency |
| **Sample Variance ($s^2$)** | 26,844.03 ms² | 162,902.09 ms² | Candidate has high variance due to bimodal distribution |
| **Sample Std Dev ($s$)** | ±163.84 ms | ±403.61 ms | Bimodal: timeout vs open breaker |

### Why Candidate Variance is High (Bimodal Distribution)
The candidate probe distribution is strictly bimodal across two operational phases:
1. **Phase A (Timeout-Only SLA Enforcement):** Probes exercise the bounded timeout path before tripping the breaker (Mean: 810.06 ms, P95: 812.51 ms). Breaker state is `CLOSED (reset each probe)`.
2. **Phase B (Circuit Breaker Tripped - Short Circuit):** Circuit breaker transitions to `OPEN`. Probes short-circuit locally in ~1.91–2.99 ms (Mean: 164.17 ms, P95: 811.08 ms).

### SLA Budget Margin Assessment
- **SLA Budget:** 1,500.00 ms
- **Measured Candidate P95:** 812.51 ms (Max: 812.51 ms)
- **Safety Margin:** **687.49 ms** under the budget ceiling.
- **Production Implication:** The candidate operates with a comfortable 687.49 ms safety margin during initial socket timeouts. Once 3 consecutive timeouts occur, the circuit breaker transitions to `OPEN` (Phase B), instantly dropping probe latency from ~810 ms down to **1.91–2.99 ms** (providing a **1,497.01 ms** margin against the 1,500 ms SLA).

---

## 5. Two-Phase Replay Verification

FaultForge evaluates timeout verification and circuit-breaker short-circuit verification across two distinct operational phases:

| Phase | Evaluation Gate | Execution Semantics | Probes | Measured Mean | Measured P95 | Breaker State | Status |
|---|---|---|---|---|---|---|---|
| **Phase A** | `candidate_timeout_only` | Initial probes exercise the bounded timeout path within SLA budget. | 10 probes | 810.06 ms | 812.51 ms | `CLOSED` (reset each probe) | PASS |
| **Phase B** | `candidate_breaker_short_circuit` | Circuit breaker trips OPEN; subsequent probes short-circuit locally in ~1.91ms. | 10 probes | 164.17 ms | 811.08 ms | `OPEN` (8 of 10 short-circuited) | PASS |

---

## 6. Earlier Local Run vs. CI Linux Container Run (Historical Context)

Reviewers evaluating different test logs may note differences between early pre-CI workstation runs and official GitLab CI runs:
- **Historical Workstation Run (Local Windows):** An early exploratory run on a Windows development workstation measured Phase A around ~1.4 s (observed difference, cause not measured), leaving a narrow margin against the 1,500 ms SLA.
- **Official GitLab CI Run (Containerized Linux `python:3.12-slim`):** In the official containerized CI runner, `httpx.Timeout(0.8, connect=0.8)` executes with minimal Linux network stack overhead (~5–6 ms), yielding candidate Phase A latencies around 810 ms (P95 812.51 ms) and expanding the safety margin to **687.49 ms**.

Both environments prove candidate resilience under identical Toxiproxy chaos (0% SLA breaches vs 100% baseline failure), but all production reports, cryptographic receipts, and scorecards cite the containerized CI pipeline replay (`reports/replay_evaluation.json`).

---

## 7. Anti-Fake Policy on Percentage Claims

- Documentation and dashboard must explicitly cite the basis when quoting percentage improvements (e.g. *"-77.6% P95 latency reduction"* or *"-86.3% mean latency reduction"*).
- No hardcoded numbers: all values displayed in the dashboard are dynamically read from `reports/replay_evaluation.json` (`latency_reduction` and `raw_metrics` objects).
