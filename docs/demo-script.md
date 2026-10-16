# FaultForge Demo Video Script (< 3 Minutes)
## GitLab Transcend 2026: Life After Code

**Working Concept:** Rehearse a failure. Recover safely. Prove the service is stronger.  
**Target Video Duration:** 2 minutes 50 seconds  
**Autonomy Level:** Supervised Autonomy  

---

### Segment 1: The Dependency Fragility Under Chaos (0:00 – 0:35)
- **Visual:** Terminal split screen: Checkout service on port 8090, downstream carrier stub on 8081, and Toxiproxy on 8082/8474.
- **Narrator:**
  > "Ordinary CI pipelines mock downstream dependencies, giving teams false confidence. But in production, when an external carrier slows down, services hang.
  > Here, we introduce a controlled Toxiproxy network delay of 3500 milliseconds on the shipping dependency path.
  > Running `python scripts/run_fault.py --mode baseline --expect-fail` against the unpatched checkout service immediately reproduces the failure: requests exceed our 1500ms SLA budget, taking over 3.5 seconds."

---

### Segment 2: Deterministic Regression Discovery via Git Bisect (0:35 – 1:05)
- **Visual:** Screen showing `python scripts/diagnose_and_bisect.py` running `git bisect`.
- **Narrator:**
  > "Rather than letting an LLM hallucinate a culprit commit, FaultForge runs deterministic AST inspection and real `git bisect`.
  > Binary searching our commit history with an automated probe tests good and bad revisions, and conclusively isolates commit `974035c` — where a recent commit removed the bounded timeout and fallback.
  > FaultForge compiles this into a compact, secret-sanitized Incident Dossier."

---

### Segment 3: GitLab Duo Agent Platform Custom Flow (1:05 – 1:45)
- **Visual:** GitLab UI showing Duo Agent Platform custom flow (`flows/faultforge-flow.yaml`) and the synthesized Merge Request.
- **Narrator:**
  > "The Incident Dossier is ingested by our GitLab Duo Custom Flow.
  > Duo's Diagnostician locates the unbounded `httpx` call site.
  > The Resilience Healer synthesizes the smallest scoped fix: enforcing an 0.8-second connect/read timeout, activating a circuit breaker, and returning an observable fallback rate estimate.
  > The Hardener automatically extends our regression test suite in `tests/chaos/test_resilience.py` and opens a Merge Request targeting `main`."

---

### Segment 4: Exact-Fault Replay Verification (1:45 – 2:20)
- **Visual:** Terminal and GitLab CI pipeline running `scripts/evaluate_replay.py`.
- **Narrator:**
  > "Here is our core differentiator: We don't trust a fix just because an AI wrote it. We replay the exact same fault profile hash against the candidate patch.
  > As you see in the evaluation output, all 10 consecutive replay runs pass within ~820ms, 100% within our SLA budget.
  > The response explicitly flags `is_fallback: true` and `is_estimate: true` so data is never misrepresented."

---

### Segment 5: Supervised Governance, Cloud Run & Audit Receipt (2:20 – 2:50)
- **Visual:** Google Cloud Run console showing canary traffic split and `reports/EVIDENCE_RECEIPT.md`.
- **Narrator:**
  > "Because we operate under Supervised Autonomy, our risk policy gate classified this change as LOW risk, but live production promotion is gated on human developer approval.
  > Candidate revision is deployed to Google Cloud Run with zero live traffic, smoke-tested, and promoted only when approved, with instant automated traffic rollback ready if probes degrade.
  > Finally, FaultForge generates a tamper-evident Evidence Receipt with a cryptographic SHA-256 seal.
  > FaultForge: Rehearse a failure. Recover safely. Prove the service is stronger."
