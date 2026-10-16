---
name: "Resilience Incident & Chaos Rehearsal"
about: "Track a controlled dependency failure, diagnosis, and verified recovery"
title: "[Incident] Chaos Failure Injected: {{ fault_type }} on {{ target_service }}"
labels: ["FaultForge", "incident", "chaos-testing", "supervised-autonomy"]
---

## 1. Incident Overview
- **Incident ID:** `{{ incident_id }}`
- **Target Service:** `{{ target_service }}`
- **Injected Fault:** `{{ fault_type }}` (Latency: `{{ latency_ms }}ms`, Jitter: `{{ jitter_ms }}ms`)
- **Profile Hash:** `{{ profile_hash }}`
- **Observed SLA Breaches:** `{{ sla_breaches }}`

## 2. Failure Evidence
- **Failed Test:** `{{ failed_test }}`
- **Pipeline URL:** `{{ pipeline_url }}`
- **Stack Trace / Excerpt:**
```text
{{ log_excerpt }}
```

## 3. Diagnosis & Remediation Plan
- **Status:** `{{ diagnosis_status }}` (Confidence: `{{ confidence }}`)
- **Call Site:** `{{ call_site }}`
- **Remediation MR:** `{{ merge_request_url }}`

## 4. Verification & Governance
- [ ] Pytest Unit & Integration Tests Passed
- [ ] Identical Fault Replayed via Toxiproxy
- [ ] Zero SLA Breaches under Replay
- [ ] Evidence Receipt Generated (`reports/EVIDENCE_RECEIPT.md`)
- [ ] Supervised Human Review Completed
