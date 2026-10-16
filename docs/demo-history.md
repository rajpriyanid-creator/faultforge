# FaultForge Demo Git History & Regression Boundary

This document records the exact commit history structure created on `main` to demonstrate deterministic chaos rehearsal, root-cause regression discovery via `git bisect`, and GitLab Duo Agent Platform remediation.

---

## 1. Commit Sequence

| Commit | Summary | Code State in `app/clients/shipping_client.py` | Chaos Probe Result (3500ms Delay) |
|---|---|---|---|
| **C1** | `feat: initial checkout and resilient shipping client` | Enforces bounded timeout (0.8s), circuit breaker, graceful fallback | **PASS** (Completes in ~840ms with fallback quote, within 1500ms SLA budget) |
| **C2** | `docs: add system architecture and component specifications` | Unchanged from C1 | **PASS** |
| **C3** | `chore: instrument request timing headers and metrics` | Unchanged from C1 | **PASS** |
| **C4** | `feat: add destination zip code format validation` | Unchanged from C1 | **PASS** |
| **C5** | `perf: reuse client, simplify error handling` *(REGRESSION)* | **Removes bounded timeout**, removes circuit breaker, removes fallback | **FAIL** (Hangs for 3500ms, exceeding 1500ms SLA budget) |
| **C6** | `docs: update operational runbook and troubleshooting guide` | Unchanged from C5 (Fragile) | **FAIL** |

---

## 2. The Regression Introduced in C5

In commit **C5**, a developer attempting to "streamline" outbound HTTP logic:
1. Removed the explicit `timeout=0.8` parameter from `httpx.AsyncClient`.
2. Removed the `try...except (httpx.TimeoutException, httpx.HTTPError)` handling block.
3. Removed the `get_graceful_shipping_fallback` mechanism.
4. Removed the circuit breaker execution gate.

### Observable Impact Under Chaos
- When external carrier dependencies respond normally (< 100ms), C5 appears to work fine. Ordinary mocked unit tests pass.
- When Toxiproxy injects a 3500ms latency into the shipping dependency path, C5 blocks the worker thread for the full 3.5 seconds, breaching the 1500ms SLA budget.
- This creates the exact failure condition that triggers the GitLab Duo Agent Platform workflow.

---

## 3. How `git bisect` Discovers C5
The probe script (`scripts/bisect_probe.sh`) runs a real HTTP probe through Toxiproxy for each tested commit:
- Testing C1: Probe completes in ~840ms -> Returns `0` (GOOD).
- Testing C6: Probe takes 3500ms -> Returns `1` (BAD).
- Binary search tests C4 -> Returns `0` (GOOD).
- Binary search tests C5 -> Returns `1` (BAD).
- `git bisect` conclusively identifies **C5** as the first bad commit.
- Status is classified as `CONFIRMED_REGRESSION` backed by automated test evidence.
