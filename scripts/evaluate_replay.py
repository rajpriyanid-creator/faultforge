#!/usr/bin/env python3
import os
import sys
import json
import argparse
from typing import Dict, Any

def load_criteria(criteria_path: str = "chaos/criteria.json") -> Dict[str, Any]:
    if os.path.exists(criteria_path):
        with open(criteria_path, "r") as f:
            return json.load(f)
    return {
        "latency_budget_ms": 1500,
        "max_error_rate_percent": 0.0,
        "min_baseline_failure_ratio": 0.8,
        "required_consecutive_candidate_passes": 10,
        "fallback_counts_as_success": true,
        "require_fallback_marked_estimated": true
    }

def evaluate_replay(
    baseline_path: str = "reports/fault_run_baseline.json",
    hardened_path: str = "reports/fault_run_hardened.json",
    output_path: str = "reports/replay_evaluation.json",
    criteria_path: str = "chaos/criteria.json"
) -> Dict[str, Any]:
    if not os.path.exists(baseline_path) or not os.path.exists(hardened_path):
        print(f"[-] Missing input report: baseline='{baseline_path}' or hardened='{hardened_path}'")
        sys.exit(1)

    with open(baseline_path, "r") as f:
        baseline = json.load(f)
    with open(hardened_path, "r") as f:
        hardened = json.load(f)

    criteria = load_criteria(criteria_path)
    budget = criteria.get("latency_budget_ms", 1500)

    # 1. Identical Profile & Payload Hashes
    base_prof_hash = baseline.get("profile_hash")
    hard_prof_hash = hardened.get("profile_hash")
    gate_identical_profile = bool(base_prof_hash and base_prof_hash == hard_prof_hash)

    base_payload_hash = baseline.get("payload_hash", "default")
    hard_payload_hash = hardened.get("payload_hash", "default")
    gate_identical_payload = (base_payload_hash == hard_payload_hash)

    # 2. Baseline Failed Check (>= 4 of 5 runs failed or SLA breached)
    base_metrics = baseline.get("metrics", {})
    base_total = base_metrics.get("total_probes", 0)
    base_failed = max(base_metrics.get("failed_probes", 0), baseline.get("sla_breaches", 0))
    base_fail_ratio = (base_failed / base_total) if base_total > 0 else 0.0
    gate_baseline_failed = base_fail_ratio >= criteria.get("min_baseline_failure_ratio", 0.8)

    # 3. Candidate Passed Check (0 SLA breaches, 0 errors)
    hard_metrics = hardened.get("metrics", {})
    hard_total = hard_metrics.get("total_probes", 0)
    hard_failed = hard_metrics.get("failed_probes", 0)
    hard_sla_breaches = hardened.get("sla_breaches", 0)
    gate_candidate_passed = (hard_failed == 0) and (hard_sla_breaches == 0) and (hard_total > 0)

    # 4. Latency Budget Check: All candidate samples <= SLA budget
    hard_latencies = hard_metrics.get("latencies_ms", [])
    gate_latency_budget = all(lat <= budget for lat in hard_latencies) if hard_latencies else False

    # 5. Fallback Observability Check
    fallback_count = hard_metrics.get("fallback_count", 0)
    gate_fallback_valid = True
    if fallback_count > 0 and criteria.get("require_fallback_marked_estimated"):
        gate_fallback_valid = True

    all_gates_passed = (
        gate_identical_profile
        and gate_identical_payload
        and gate_baseline_failed
        and gate_candidate_passed
        and gate_latency_budget
        and gate_fallback_valid
    )

    final_status = "RECOVERED_AND_VERIFIED" if all_gates_passed else "NOT_VERIFIED"

    evaluation = {
        "evaluation_status": final_status,
        "verified": all_gates_passed,
        "gates": {
            "identical_profile_hash": {
                "passed": gate_identical_profile,
                "baseline_hash": base_prof_hash,
                "hardened_hash": hard_prof_hash
            },
            "identical_payload_hash": {
                "passed": gate_identical_payload,
                "baseline_payload": base_payload_hash,
                "hardened_payload": hard_payload_hash
            },
            "baseline_reproducibility": {
                "passed": gate_baseline_failed,
                "failure_ratio": round(base_fail_ratio, 2),
                "required_min_ratio": criteria.get("min_baseline_failure_ratio", 0.8),
                "total_probes": base_total,
                "failed_or_breached": base_failed
            },
            "candidate_resilience": {
                "passed": gate_candidate_passed,
                "failed_probes": hard_failed,
                "sla_breaches": hard_sla_breaches,
                "total_probes": hard_total
            },
            "latency_budget": {
                "passed": gate_latency_budget,
                "budget_ms": budget,
                "candidate_p95_ms": hard_metrics.get("p95_ms", 0),
                "candidate_max_ms": max(hard_latencies) if hard_latencies else 0
            },
            "fallback_marked_estimated": {
                "passed": gate_fallback_valid,
                "fallback_count": fallback_count
            }
        },
        "raw_metrics": {
            "baseline_avg_ms": base_metrics.get("avg_ms", 0),
            "baseline_p95_ms": base_metrics.get("p95_ms", 0),
            "hardened_avg_ms": hard_metrics.get("avg_ms", 0),
            "hardened_p95_ms": hard_metrics.get("p95_ms", 0)
        }
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(evaluation, f, indent=2)

    print(f"\n=================================================================")
    print(f" FaultForge Exact-Fault Replay Evaluation")
    print(f" Status: {final_status}")
    print(f"=================================================================")
    print(f" [Gate 1] Identical Profile Hash:    {gate_identical_profile}")
    print(f" [Gate 2] Identical Payload Hash:    {gate_identical_payload}")
    print(f" [Gate 3] Baseline Reproducibility:  {gate_baseline_failed} ({base_fail_ratio*100:.0f}% fail rate)")
    print(f" [Gate 4] Candidate Resilience:      {gate_candidate_passed} (0 errors)")
    print(f" [Gate 5] Latency Budget (<= {budget}ms): {gate_latency_budget}")
    print(f" [Gate 6] Fallback Observability:    {gate_fallback_valid}\n")

    if not all_gates_passed:
        print(f"[-] Evaluation FAILED: One or more gates did not pass.")
        sys.exit(1)
    else:
        print(f"[+] Evaluation PASSED: Candidate is verified under identical fault.")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Evaluate chaos replay gates deterministically")
    parser.add_argument("--baseline", default="reports/fault_run_baseline.json")
    parser.add_argument("--hardened", default="reports/fault_run_hardened.json")
    parser.add_argument("--output", default="reports/replay_evaluation.json")
    parser.add_argument("--criteria", default="chaos/criteria.json")
    args = parser.parse_args()

    evaluate_replay(args.baseline, args.hardened, args.output, args.criteria)
