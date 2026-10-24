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
> **Crucial Measurement Semantic:** All candidate probes under active fault return `is_fallback: true` and `is_estimate: true`. The **810.55 ms P50 latency** and **-86.6% mean reduction** measure serving deterministic local fallback quotes (`$7.50 + $1.25 * weight_kg`) rather than waiting ~3.5–3.7 s for degraded carrier responses and breaching the 1,500 ms SLA.

---

## 3. Measurement Formulas & Empirical Values

All latency reduction metrics recorded in `reports/replay_evaluation.json` and rendered by `scripts/render_metrics.py` are deterministically computed using the formulas below from the active CI pipeline run:

### A. 95th Percentile (P95) Latency Reduction
Measures tail latency protection under severe dependency degradation:

$$\text{P95 Reduction (\%)} = \left( \frac{\text{Baseline P95 (ms)} - \text{Candidate P95 (ms)}}{\text{Baseline P95 (ms)}} \right) \times 100$$

- **Baseline P95:** 3,699.48 ms (unconstrained downstream hang)
- **Candidate P95:** 813.32 ms (bounded by strict client SLA budget <= 1500ms)
- **Computed Reduction:** **78.0%** tail latency reduction

### B. Mean (Average) Latency Reduction
Measures aggregate throughput improvement across both timeout and circuit-breaker short-circuit phases:

$$\text{Mean Reduction (\%)} = \left( \frac{\text{Baseline Mean (ms)} - \text{Candidate Mean (ms)}}{\text{Baseline Mean (ms)}} \right) \times 100$$

- **Baseline Mean:** 3,637.98 ms
- **Candidate Mean:** 487.92 ms
- **Computed Reduction:** **86.6%** mean latency reduction

### C. Median (P50) Latency Reduction & Percentile Methodology

$$\text{P50 Reduction (\%)} = \left( \frac{3,647.69 - 810.55}{3,647.69} \right) \times 100 = \mathbf{77.8\%}$$

#### Percentile Rank Method Documentation:
FaultForge's telemetry and evaluation scripts (`scripts/run_fault.py` and `scripts/render_metrics.py`) use the **Nearest-Rank Method** with 0-indexed integer truncation:

$$\text{Rank Index} = \min(\lfloor N \times q \rfloor, N - 1) = \text{sorted}[\text{int}(N \times q)]$$

Where $q \in (0, 1]$ represents the percentile quantile (e.g. $q = 0.50$ for P50, $q = 0.95$ for P95). This convention provides deterministic integer rank selection across discrete chaos probe samples without synthesizing interpolated latency values.

#### Empirical Behavior at $N = 20$ (Candidate Replay):
For candidate replay sample size $N = 20$:
- **P50 (Median) Selection:** $\text{int}(20 \times 0.50) = 10$, selecting the 11th sorted element `sorted[10] = 810.55 ms`. In an even sample size ($N = 20$), the two central values are `sorted[9] = 810.04 ms` (lower-middle) and `sorted[10] = 810.55 ms` (upper-middle). The nearest-rank method selects the upper-middle value.
  - **True Median Alongside:** The standard interpolated mathematical median $\frac{\text{sorted}[9] + \text{sorted}[10]}{2} = \frac{810.04 + 810.55}{2} = \mathbf{810.30\text{ ms}}$ (a difference of merely $0.25\text{ ms}$ or $0.03\%$).
- **P95 Selection:** $\min(\text{int}(20 \times 0.95), 19) = 19$, selecting `sorted[19] = 813.32 ms`. Because $20 \times 0.95 = 19$, at $N = 20$ the 95th percentile rank **equals the maximum recorded probe latency** ($813.32\text{ ms}$).
- **P99 Selection:** $\min(\text{int}(20 \times 0.99), 19) = 19$, also selecting the maximum element `sorted[19] = 813.32 ms`.

#### Empirical Behavior at $N = 5$ (Baseline Run):
For baseline sample size $N = 5$:
- **P50 (Median) Selection:** $\text{int}(5 \times 0.50) = 2$, selecting `sorted[2] = 3,647.69 ms`. Because $N = 5$ is odd, index 2 is the exact central value; the nearest-rank P50 and true median are identical ($\mathbf{3,647.69\text{ ms}}$).
- **P95 Selection:** $\min(\text{int}(5 \times 0.95), 4) = 4$, selecting `sorted[4] = 3,699.48 ms`, which likewise equals the baseline maximum recorded latency ($3,699.48\text{ ms}$).

### D. Maximum Latency Reduction
$$\text{Max Reduction (\%)} = \left( \frac{3,699.48 - 813.32}{3,699.48} \right) \times 100 = \mathbf{78.0\%}$$

---

## 4. Empirical Sample Distribution & Variance Analysis

| Statistical Metric | Baseline Run (N=5) | Candidate Replay (N=20) | Notes on Distribution |
|---|---|---|---|
| **Count ($N$)** | 5 probes | 20 probes | CI execution dataset (`reports/replay_evaluation.json`) |
| **SLA Breaches** | 5 / 5 (100% failure) | 0 / 20 (0% breaches) | 1,500 ms SLA threshold |
| **Mean** | 3,637.98 ms | 487.92 ms | -86.6% mean reduction |
| **Median (P50)** | 3,647.69 ms | 810.55 ms | -77.8% P50 reduction |
| **P95** | 3,699.48 ms | 813.32 ms | -78.0% P95 reduction |
| **Minimum** | 3,540.60 ms | 2.35 ms | Min recorded latency |
| **Maximum** | 3,699.48 ms | 813.32 ms | Max recorded latency |
| **Sample Variance ($s^2$)** | 3,480.12 ms² | 165,260.41 ms² | Candidate has high variance due to bimodal distribution |
| **Sample Std Dev ($s$)** | ±58.99 ms | ±406.52 ms | Bimodal: timeout vs open breaker |

### Why Candidate Variance is High (Bimodal Distribution)
The candidate probe distribution is strictly bimodal across two operational phases:
1. **Phase A (Timeout-Only SLA Enforcement):** Probes exercise the bounded timeout path before tripping the breaker (Mean: 811.29 ms, P95: 813.32 ms). Breaker state is `CLOSED (reset each probe)`.
2. **Phase B (Circuit Breaker Tripped - Short Circuit):** Circuit breaker transitions to `OPEN`. Probes short-circuit locally in ~2.35–3.35 ms (Mean: 164.54 ms, Max: 812.85 ms).

### SLA Budget Margin Assessment
- **SLA Budget:** 1,500.00 ms
- **Measured Candidate P95:** 813.32 ms (Max: 813.32 ms)
- **Safety Margin:** **686.68 ms** under the budget ceiling.
- **Production Implication:** The candidate operates with a comfortable 686.68 ms safety margin during initial socket timeouts. Once 3 consecutive timeouts occur, the circuit breaker transitions to `OPEN` (Phase B), instantly dropping probe latency from ~811 ms down to **2.35–3.35 ms** (providing a **1,497.65 ms** margin against the 1,500 ms SLA).

---

## 5. Two-Phase Replay Verification

FaultForge evaluates timeout verification and circuit-breaker short-circuit verification across two distinct operational phases:

| Phase | Evaluation Gate | Execution Semantics | Probes | Measured Mean | Measured P95 | Breaker State | Status |
|---|---|---|---|---|---|---|---|
| **Phase A** | `candidate_timeout_only` | Initial probes exercise the bounded timeout path within SLA budget. | 10 probes | 811.29 ms | 813.32 ms | `CLOSED` (reset each probe) | PASS |
| **Phase B** | `candidate_breaker_short_circuit` | Circuit breaker trips OPEN; subsequent probes short-circuit locally in ~2.35–3.35 ms. | 10 probes | 164.54 ms | 812.85 ms | `OPEN` (8 of 10 short-circuited) | PASS |

---

## 6. Earlier Local Run vs. CI Linux Container Run (Historical Context)

Reviewers evaluating different test logs may note differences between early pre-CI workstation runs and official GitLab CI runs:
- **Historical Workstation Run (Local Windows):** An early exploratory run on a Windows development workstation measured Phase A around ~1.4 s (observed difference, cause not measured), leaving a narrow margin against the 1,500 ms SLA.
- **Official GitLab CI Run (Containerized Linux `python:3.12-slim`):** In the official containerized CI runner, `httpx.Timeout(0.8, connect=0.8)` executes with minimal Linux network stack overhead (~5–6 ms), yielding candidate Phase A latencies around 810 ms (P95 813.32 ms) and expanding the safety margin to **686.68 ms**.

Both environments prove candidate resilience under identical Toxiproxy chaos (0% SLA breaches vs 100% baseline failure), but all production reports, cryptographic receipts, and scorecards cite the containerized CI pipeline replay (`reports/replay_evaluation.json`).

---

## 7. Anti-Fake Policy on Percentage Claims

- Documentation and dashboard must explicitly cite the basis when quoting percentage improvements (e.g. *"-78.0% P95 latency reduction"* or *"-86.6% mean latency reduction"*).
- No hardcoded numbers: all values displayed in the dashboard are dynamically read from `reports/replay_evaluation.json` (`latency_reduction` and `raw_metrics` objects).
