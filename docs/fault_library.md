# FaultForge Chaos Fault Library
# SPDX-License-Identifier: MIT

This document cataloges the deterministic chaos fault profiles supported by FaultForge via Shopify Toxiproxy (`ghcr.io/shopify/toxiproxy:2.9.0`).

---

## 1. Evaluated Production-Grade Profiles

### Profile 1: Downstream Latency Cascading Hang
- **File:** `chaos/profiles/latency_cascading_hang.json`
- **Canonical Hash:** `644a89784316`
- **Toxiproxy Toxic Type:** `latency`
- **Attributes:**
  - `latency`: `3500` ms
  - `jitter`: `250` ms
  - `toxicity`: `1.0` (100% of packets affected)
  - `stream`: `downstream`
- **Target Microservice:** `checkout-service` -> `shipping-dependency`
- **SLA Budget:** `1500` ms
- **Baseline Behavior:** 5/5 probes hang (>3,700ms), tripping cascading request queue starvation.
- **Hardened Behavior:** 0.8s bounded timeout fires, returning deterministic fallback (`CONFIRMED_ESTIMATED_SHIPPING`, `is_fallback: true`, `is_estimate: true`) under 850ms.

---

### Profile 2: Upstream Connection Reset (`reset_peer`)
- **File:** `chaos/profiles/connection_reset.json`
- **Canonical Hash:** `0496439547a1`
- **Toxiproxy Toxic Type:** `reset_peer`
- **Attributes:**
  - `toxicity`: `1.0`
  - `stream`: `downstream`
- **Target Microservice:** `checkout-service` -> `shipping-dependency`
- **Baseline Behavior:** Immediate TCP connection reset; unhandled exception drops checkout transactions.
- **Hardened Behavior:** Circuit breaker intercepts reset, catches network transport exception, logs error, and returns safe estimated rate fallback.

---

## 2. Extended Supported Toxiproxy Profiles (Future Scope)

FaultForge's deterministic proxy architecture supports the full suite of Toxiproxy toxics:

| Toxic Profile | Toxiproxy Type | Target Failure Mode | Resilience Countermeasure |
|---|---|---|---|
| **Bandwidth Throttle** | `bandwidth` | Simulates congested cellular or cross-region trunk links | Streaming buffers, response payload compression |
| **Packet Slicer** | `slicer` | Slices packets into small TCP segments with inter-packet delay | Socket buffer tuning, TCP NODELAY flags |
| **Timeout Flap** | `timeout` | Drops all packets after specified timeout | Strict connect/read socket deadline budgets |
| **Slow Close** | `slow_close` | Delays TCP FIN/RST packet delivery | Graceful connection pool reap timeouts |

---

## 3. Cryptographic Profile Verification

Every fault profile executed in CI/CD is hashed deterministically using canonical JSON key sorting:

```python
import hashlib, json

def compute_profile_hash(profile_dict: dict) -> str:
    canonical = json.dumps(profile_dict, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]
```

This guarantees that baseline failure measurements and candidate recovery measurements are compared under **strictly identical network conditions**.
