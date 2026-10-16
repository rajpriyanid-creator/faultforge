# FaultForge Demo Video Script (< 3 Minutes)
## GitLab Transcend 2026: Life After Code

**Working Concept:** Rehearse a failure. Recover safely. Prove the service is stronger.  
**Target Video Duration:** 2 minutes 50 seconds  
**Track:** Path A — Start Fresh  
**Autonomy Level:** Supervised Autonomy  

---

### Segment 1: The Dependency Fragility Under Chaos (0:00 – 0:35)
- **Visual:** Terminal split screen: Checkout service on port 8090, downstream carrier stub on 8081, and Toxiproxy on 8082/8474.
- **Action:** Run baseline fault probe:
  ```bash
  python scripts/run_fault.py --label baseline --output reports/fault_run_baseline.json
  ```
- **Narrator:**
  > "Ordinary CI pipelines mock downstream dependencies, giving teams false confidence. But in production, when an external carrier slows down, unhardened services hang.
  > Here, we introduce a controlled Toxiproxy network delay of 3500 milliseconds on the shipping dependency path.
  > Running our baseline probe against the unpatched checkout service immediately reproduces the failure: all 5 requests breach our 1500 millisecond SLA budget, averaging 3742 milliseconds."

---

### Segment 2: Deterministic Bisect Isolates Culprit Commit (0:35 – 1:00)
- **Visual:** Terminal showing `scripts/diagnose_and_bisect.py` executing AST analysis and automated `git bisect`.
- **Action:**
  ```bash
  python scripts/collect_evidence.py
  python scripts/diagnose_and_bisect.py
  ```
- **Narrator:**
  > "Rather than letting an LLM hallucinate a culprit commit, FaultForge runs deterministic AST inspection and real `git bisect`.
  > Binary searching our commit history with an automated probe tests good and bad revisions, and conclusively isolates commit `974035c` — where a recent commit removed the bounded timeout and fallback.
  > FaultForge compiles these verified facts into a compact, secret-sanitized Incident Dossier."

---

### Segment 3: GitLab Duo Agent Platform Custom Flow (1:00 – 1:40)
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

### Segment 4: Regression Test & Exact-Fault Replay Verification (1:40 – 2:15)
- **Visual:** Terminal showing regression tests failing on unpatched code, passing on candidate branch, and `evaluate_replay.py` validating 10/10 probes.
- **Action:**
  ```bash
  python scripts/run_fault.py --label candidate --output reports/fault_run_candidate.json
  python scripts/evaluate_replay.py --baseline reports/fault_run_baseline.json --candidate reports/fault_run_candidate.json
  ```
- **Narrator:**
  > "Here is our core differentiator: We don't trust a fix just because an AI wrote it. We replay the exact same fault profile against the candidate patch.
  > Under the candidate run, 10 consecutive probes are executed against the identical 3500ms network delay.
  > All 10 pass within ~820 milliseconds — zero SLA breaches.
  > The response explicitly flags `is_fallback: true` and `is_estimate: true` so carrier data is never misrepresented."

---

### Segment 5: Supervised Governance, Cloud Run & Audit Receipt (2:15 – 2:50)
- **Visual:** Google Cloud Run console showing canary traffic split, rollback execution, and `reports/EVIDENCE_RECEIPT.md`.
- **Action:**
  ```bash
  python scripts/cloudrun_traffic.py --action rollback --dry-run
  python scripts/generate_receipt.py
  ```
- **Narrator:**
  > "Because we operate under Supervised Autonomy, our risk policy classifies this change as LOW risk, allowing automated staging deployment at zero live traffic.
  > But live production traffic promotion strictly requires explicit human developer authorization.
  > If candidate health probes ever degrade, `cloudrun_traffic.py` executes an instant traffic rollback to the previous revision in seconds.
  > Finally, FaultForge emits a tamper-evident Evidence Receipt sealed with a cryptographic SHA-256 hash.
  > FaultForge: Rehearse a failure. Recover safely. Prove the service is stronger."
