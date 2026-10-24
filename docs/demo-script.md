# FaultForge Demo Video Script (< 3 Minutes)
## GitLab Transcend 2026: Life After Code

**Working Concept:** Rehearse a failure. Recover safely. Prove the service is stronger.  
**Target Video Duration:** 2 minutes 50 seconds  
**Track:** Path A — Start Fresh  
**Autonomy Level:** Supervised Autonomy  

---

### Segment 1: Incident Issue & Dependency Fragility Under Chaos (0:00 – 0:35)
- **Visual:** GitLab Issue Tracker displaying the incident issue ("SLA Breach Detected: Shipping dependency latency exceeds 1500ms budget"), followed by terminal split screen showing checkout service on port 8090, downstream carrier stub on 8081, and Toxiproxy on 8082.
- **Action:** Run baseline fault probe reproducing the failure:
  ```bash
  python scripts/run_fault.py --label baseline --output reports/fault_run_baseline.json
  ```
- **Narrator:**
  > "Ordinary CI pipelines mock downstream dependencies, giving teams false confidence. But in production, when an external carrier slows down, unhardened services hang.
  > Our automated monitor triggers an incident issue in GitLab when outbound dependency latency spikes.
  > Here, Toxiproxy injects a controlled 3500 millisecond network delay on the shipping path.
  > "Running our baseline probe against the unpatched checkout service reproduces the incident: all 5 requests breach our 1500 millisecond SLA budget, averaging 3652.0 milliseconds (p95: 3718.82 ms)."

---

### Segment 2: Deterministic Bisect Isolates Culprit Commit (0:35 – 1:00)
- **Visual:** Terminal showing `scripts/diagnose_and_bisect.py` executing AST analysis and automated `git bisect`.
- **Action:**
  ```bash
  python scripts/collect_evidence.py
  python scripts/diagnose_and_bisect.py
  ```
- **Narrator:**
  > "Rather than letting an LLM guess what broke, FaultForge runs deterministic AST inspection and real `git bisect`.
  > Binary searching our commit history with an automated probe tests good and bad revisions, and conclusively isolates commit `974035c` — where a recent commit removed the bounded timeout and fallback.
  > FaultForge compiles these verified facts into a compact, secret-sanitized Incident Dossier."

---

### Segment 3: GitLab Duo Agent Platform Custom Flow (1:00 – 1:35)
- **Visual:** GitLab UI showing Duo Agent Platform custom flow (`flows/faultforge-flow.yaml`) and the synthesized Merge Request.
- **Action:**
  ```bash
  python scripts/trigger_duo_flow.py --mode manual
  ```
- **Narrator:**
  > "The Incident Dossier is ingested by our GitLab Duo Custom Flow.
  > Duo's Diagnostician locates the unbounded `httpx` call site in `shipping_client.py`.
  > The Resilience Healer synthesizes the smallest scoped fix: enforcing an 0.8-second connect and read timeout, activating a circuit breaker, and returning a deterministic fallback rate.
  > The Hardener automatically extends our regression test suite in `tests/chaos/test_resilience.py` and opens a Merge Request targeting `main`."

---

### Segment 4: 9-Stage CI Pipeline & Exact-Fault Replay Verification (1:35 – 2:15)
- **Visual:** GitLab CI/CD Pipeline graph showing all 9 lifecycle stages executing, followed by terminal showing exact-fault replay under canonical profile hash `644a89784316`.
- **Action:**
  ```bash
  python scripts/run_fault.py --label candidate --output reports/fault_run_candidate.json
  python scripts/evaluate_replay.py --baseline reports/fault_run_baseline.json --candidate reports/fault_run_candidate.json
  ```
- **Narrator:**
  > "Here is our core differentiator: We don't trust a fix just because an AI wrote it. We replay the exact same fault profile against the candidate patch inside our 9-stage GitLab CI pipeline.
  > Replay verification confirms Toxiproxy is in-path with canonical profile hash `644a89784316`.
  > Under 20 probes with the identical 3500 millisecond network delay, all 20 pass within our 1500 millisecond SLA budget — achieving an 86.3% mean reduction (3572.47 ms down to 488.20 ms) and 77.9% P95 reduction (3678.92 ms down to 814.05 ms) with zero SLA breaches.
  > Phase A bounds the timeout path within the 1500ms budget (P95 815.41ms) while the breaker is reset; Phase B trips the breaker OPEN to short-circuit subsequent calls in just 1.91 to 2.99 milliseconds.
  > The response explicitly flags `is_fallback: true` and `is_estimate: true` so carrier data is never misrepresented."

---

### Segment 5: Supervised Governance Gate, Cloud Run & Rollback (2:15 – 2:50)
- **Visual:** Google Cloud Run staging deployment (0% live traffic), manual `govern:promote_to_production` gate button in GitLab CI, rollback script execution, and cryptographic Evidence Receipt.
- **Action:**
  ```bash
  python scripts/cloudrun_traffic.py --action rollback --dry-run
  python scripts/generate_receipt.py
  ```
- **Narrator:**
  > "Because we operate under Supervised Autonomy, our risk policy classifies this change as MEDIUM risk, allowing automated staging deployment on Google Cloud Run at zero live traffic.
  > But live production traffic promotion strictly requires explicit human sign-off at our governance gate.
  > If post-promotion telemetry ever breaches thresholds, `cloudrun_traffic.py` executes an instant traffic rollback to the previous revision in seconds.
  > Finally, FaultForge emits a tamper-evident Evidence Receipt sealed with a cryptographic SHA-256 hash.
  > FaultForge: Rehearse a failure. Recover safely. Prove the service is stronger."
