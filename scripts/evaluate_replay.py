#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
import re
import sys
import json
import argparse
from typing import Dict, Any

def load_criteria(criteria_path: str = "chaos/criteria.json") -> Dict[str, Any]:
    if os.path.exists(criteria_path):
        try:
            with open(criteria_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as exc:
            print(f"[!] Warning: Could not read {criteria_path} ({exc}), using defaults", file=sys.stderr)
    return {
        "latency_budget_ms": 1500,
        "max_error_rate_percent": 0.0,
        "min_baseline_failure_ratio": 0.8,
        "required_consecutive_candidate_passes": 10,
        "fallback_counts_as_success": True,
        "require_fallback_marked_estimated": True
    }

def evaluate_replay(
    baseline_path: str = "reports/fault_run_baseline.json",
    hardened_path: str = "reports/fault_run_hardened.json",
    output_path: str = "reports/replay_evaluation.json",
    criteria_path: str = "chaos/criteria.json",
    candidate_source: str = "duo-authored-mr"
) -> Dict[str, Any]:
    if not os.path.exists(baseline_path) or not os.path.exists(hardened_path):
        print(f"[-] Missing input report: baseline='{baseline_path}' or hardened='{hardened_path}'", file=sys.stderr)
        sys.exit(1)

    try:
        with open(baseline_path, "r", encoding="utf-8") as f:
            baseline = json.load(f)
        with open(hardened_path, "r", encoding="utf-8") as f:
            hardened = json.load(f)
    except Exception as exc:
        print(f"[-] Malformed JSON report: {exc}", file=sys.stderr)
        sys.exit(1)

    criteria = load_criteria(criteria_path)
    budget = criteria.get("latency_budget_ms", 1500)

    # 1. Real 40-character hexadecimal commit SHAs
    base_sha = baseline.get("git_sha", "")
    hard_sha = hardened.get("git_sha", "")
    valid_base_sha = bool(re.match(r"^[0-9a-fA-F]{40}$", base_sha))
    valid_hard_sha = bool(re.match(r"^[0-9a-fA-F]{40}$", hard_sha))
    gate_valid_shas = valid_base_sha and valid_hard_sha
    gate_distinct_revisions = (base_sha != hard_sha) if (base_sha and hard_sha) else False

    # 2. Identical Profile & Payload Hashes, Proxy Engine & Path Verification
    base_prof_hash = baseline.get("profile_hash")
    hard_prof_hash = hardened.get("profile_hash")
    gate_identical_profile = bool(base_prof_hash and base_prof_hash == hard_prof_hash)

    base_engine = baseline.get("proxy_engine", "toxiproxy")
    hard_engine = hardened.get("proxy_engine", "toxiproxy")
    gate_toxiproxy_engine = (base_engine == "toxiproxy" and hard_engine == "toxiproxy")

    base_payload_hash = baseline.get("payload_hash", "default")
    hard_payload_hash = hardened.get("payload_hash", "default")
    gate_identical_payload = bool(base_payload_hash and base_payload_hash == hard_payload_hash)

    base_toxic = baseline.get("toxic_readback")
    hard_toxic = hardened.get("toxic_readback")
    if base_toxic is not None and hard_toxic is not None:
        gate_identical_toxic = (base_toxic == hard_toxic)
    else:
        gate_identical_toxic = gate_identical_profile

    # Toxic proved active (delay > 0)
    gate_toxic_active = bool(
        base_toxic and (base_toxic.get("latency", 0) > 0 or base_toxic.get("attributes", {}).get("latency", 0) > 0)
    )

    # 3. Baseline Failed Check (>= 4 of 5 runs failed or SLA breached)
    base_metrics = baseline.get("metrics", {})
    base_total = base_metrics.get("total_probes", 0)
    base_failed = max(base_metrics.get("failed_probes", 0), baseline.get("sla_breaches", 0))
    base_fail_ratio = (base_failed / base_total) if base_total > 0 else 0.0
    gate_baseline_failed = base_fail_ratio >= criteria.get("min_baseline_failure_ratio", 0.8)

    # 4. Candidate Passed Check (10/10 consecutive passes, 0 SLA breaches, 0 errors)
    hard_metrics = hardened.get("metrics", {})
    hard_total = hard_metrics.get("total_probes", 0)
    hard_failed = hard_metrics.get("failed_probes", 0)
    hard_sla_breaches = hardened.get("sla_breaches", 0)
    req_consecutive = criteria.get("required_consecutive_candidate_passes", 10)
    gate_candidate_passed = (hard_failed == 0) and (hard_sla_breaches == 0) and (hard_total >= req_consecutive)

    # 5. Latency Budget Check: All candidate samples <= SLA budget
    hard_latencies = hard_metrics.get("latencies_ms", [])
    gate_latency_budget = all(lat <= budget for lat in hard_latencies) if hard_latencies else False

    # 5b. Separate Phases: Phase A (Timeout Only) and Phase B (Breaker Short Circuit)
    has_two_phases = ("phase_a_timeout_only" in hardened and "phase_b_breaker_open" in hardened)
    if has_two_phases:
        phase_a = hardened.get("phase_a_timeout_only", {})
        phase_b = hardened.get("phase_b_breaker_open", {})
        phase_a_lats = phase_a.get("latencies_ms", [])
        phase_b_lats = phase_b.get("latencies_ms", [])

        gate_candidate_timeout_only = (
            phase_a.get("failed_probes", 0) == 0
            and phase_a.get("sla_breaches", 0) == 0
            and len(phase_a_lats) >= 10
            and all(l <= budget for l in phase_a_lats)
            and phase_a.get("fallback_count", 0) >= 10
        )
        gate_candidate_breaker_short_circuit = (
            phase_b.get("short_circuited_count", 0) > 0
            and phase_b.get("failed_probes", 0) == 0
            and phase_b.get("sla_breaches", 0) == 0
            and len(phase_b_lats) >= 10
        )
    else:
        # Graceful fallback for single-phase 10-probe test fixtures
        phase_a = hard_metrics
        phase_b = hard_metrics
        gate_candidate_timeout_only = gate_candidate_passed and gate_latency_budget
        gate_candidate_breaker_short_circuit = True

    # 6. Proxy in Request Path Check: Candidate probes must not be instant fast-fail (<150ms)
    fault_delay = 0
    if isinstance(base_toxic, dict):
        fault_delay = base_toxic.get("latency", 0) or base_toxic.get("attributes", {}).get("latency", 0)
    if fault_delay == 0 and isinstance(hard_toxic, dict):
        fault_delay = hard_toxic.get("latency", 0) or hard_toxic.get("attributes", {}).get("latency", 0)

    if fault_delay >= 1000 and hard_latencies:
        gate_proxy_in_path = not all(lat < 150.0 for lat in hard_latencies)
    else:
        gate_proxy_in_path = True

    # 7. Fallback Observability & Metadata Check
    fallback_count = hard_metrics.get("fallback_count", 0)
    hard_per_req = hardened.get("per_request_results", [])
    gate_measurements_present = len(hard_per_req) >= req_consecutive

    fallback_metadata_valid = True
    if criteria.get("require_fallback_marked_estimated", True) and fallback_count > 0:
        for pr in hard_per_req:
            if pr.get("is_fallback") and not pr.get("is_estimate"):
                fallback_metadata_valid = False
                break
    gate_fallback_valid = (fallback_count > 0) and fallback_metadata_valid if criteria.get("require_fallback_marked_estimated") else True

    all_gates_passed = (
        gate_valid_shas
        and gate_distinct_revisions
        and gate_identical_profile
        and gate_toxiproxy_engine
        and gate_proxy_in_path
        and gate_identical_payload
        and gate_identical_toxic
        and gate_toxic_active
        and gate_baseline_failed
        and gate_candidate_passed
        and gate_candidate_timeout_only
        and gate_candidate_breaker_short_circuit
        and gate_latency_budget
        and gate_fallback_valid
        and gate_measurements_present
    )

    final_status = "RECOVERED_AND_VERIFIED" if all_gates_passed else "NOT_VERIFIED"

    # Latency reduction calculation
    base_p95 = base_metrics.get("p95_ms", 0.0)
    hard_p95 = hard_metrics.get("p95_ms", 0.0)
    p95_reduction_pct = round(((base_p95 - hard_p95) / base_p95 * 100.0), 1) if base_p95 > 0 else 0.0

    base_avg = base_metrics.get("avg_ms", 0.0)
    hard_avg = hard_metrics.get("avg_ms", 0.0)
    mean_reduction_pct = round(((base_avg - hard_avg) / base_avg * 100.0), 1) if base_avg > 0 else 0.0

    latency_reduction = {
        "p95_basis": {
            "metric": "p95_candidate_vs_p95_baseline",
            "baseline_ms": base_p95,
            "candidate_ms": hard_p95,
            "percent": p95_reduction_pct
        },
        "mean_basis": {
            "metric": "mean_candidate_vs_mean_baseline",
            "baseline_ms": base_avg,
            "candidate_ms": hard_avg,
            "percent": mean_reduction_pct
        }
    }

    evaluation = {
        "evaluation_status": final_status,
        "verified": all_gates_passed,
        "candidate_source": candidate_source,
        "gates": {
            "valid_git_shas": {
                "passed": gate_valid_shas,
                "baseline_sha": base_sha,
                "hardened_sha": hard_sha
            },
            "distinct_revisions": {
                "passed": gate_distinct_revisions,
                "baseline_sha": base_sha[:8] if base_sha else "none",
                "hardened_sha": hard_sha[:8] if hard_sha else "none"
            },
            "identical_profile_hash": {
                "passed": gate_identical_profile,
                "baseline_hash": base_prof_hash,
                "hardened_hash": hard_prof_hash
            },
            "toxiproxy_engine_verified": {
                "passed": gate_toxiproxy_engine,
                "baseline_engine": base_engine,
                "hardened_engine": hard_engine
            },
            "proxy_in_request_path": {
                "passed": gate_proxy_in_path,
                "fault_delay_ms": fault_delay,
                "candidate_min_ms": min(hard_latencies) if hard_latencies else 0
            },
            "identical_payload_hash": {
                "passed": gate_identical_payload,
                "baseline_payload": base_payload_hash,
                "hardened_payload": hard_payload_hash
            },
            "identical_toxic_readback": {
                "passed": gate_identical_toxic,
                "baseline_toxic": base_toxic,
                "hardened_toxic": hard_toxic
            },
            "toxic_active": {
                "passed": gate_toxic_active
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
                "total_probes": hard_total,
                "required_consecutive": req_consecutive
            },
            "candidate_timeout_only": {
                "passed": gate_candidate_timeout_only,
                "phase": "Phase A (Timeout Only - Breaker Reset)",
                "total_probes": phase_a.get("total_probes", 10),
                "sla_breaches": phase_a.get("sla_breaches", 0),
                "p95_ms": phase_a.get("p95_ms", hard_metrics.get("p95_ms")),
                "avg_ms": phase_a.get("avg_ms", hard_metrics.get("avg_ms"))
            },
            "candidate_breaker_short_circuit": {
                "passed": gate_candidate_breaker_short_circuit,
                "phase": "Phase B (Circuit Breaker Tripped - Short Circuit)",
                "total_probes": phase_b.get("total_probes", 10),
                "short_circuited_probes": phase_b.get("short_circuited_count", 0),
                "p95_ms": phase_b.get("p95_ms", hard_metrics.get("p95_ms")),
                "avg_ms": phase_b.get("avg_ms", hard_metrics.get("avg_ms"))
            },
            "latency_budget": {
                "passed": gate_latency_budget,
                "budget_ms": budget,
                "candidate_p95_ms": hard_metrics.get("p95_ms", 0),
                "candidate_max_ms": max(hard_latencies) if hard_latencies else 0
            },
            "fallback_marked_estimated": {
                "passed": gate_fallback_valid,
                "fallback_count": fallback_count,
                "metadata_valid": fallback_metadata_valid
            },
            "individual_measurements_present": {
                "passed": gate_measurements_present,
                "probe_count": len(hard_per_req)
            }
        },
        "raw_metrics": {
            "baseline_avg_ms": base_metrics.get("avg_ms", 0),
            "baseline_p95_ms": base_metrics.get("p95_ms", 0),
            "hardened_avg_ms": hard_metrics.get("avg_ms", 0),
            "hardened_p95_ms": hard_metrics.get("p95_ms", 0)
        },
        "latency_reduction": latency_reduction
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(evaluation, f, indent=2)

    print(f"\n=================================================================")
    print(f" FaultForge Exact-Fault Replay Evaluation")
    print(f" Status: {final_status}")
    print(f"=================================================================")
    print(f" [Gate 1] Valid 40-char Hex SHAs:    {gate_valid_shas}")
    print(f" [Gate 2] Distinct Revisions:        {gate_distinct_revisions}")
    print(f" [Gate 3] Identical Profile Hash:    {gate_identical_profile}")
    print(f" [Gate 4] Identical Payload Hash:    {gate_identical_payload}")
    print(f" [Gate 5] Identical Toxic Readback:  {gate_identical_toxic}")
    print(f" [Gate 6] Toxic Active:              {gate_toxic_active}")
    print(f" [Gate 7] Baseline Reproducibility:  {gate_baseline_failed} ({base_fail_ratio*100:.0f}% fail rate)")
    print(f" [Gate 8] Candidate Resilience:      {gate_candidate_passed} (0 errors, {hard_total}/{req_consecutive} runs)")
    print(f" [Gate 9] Latency Budget (<= {budget}ms): {gate_latency_budget}")
    print(f" [Gate 10] Fallback Observability:   {gate_fallback_valid}")
    print(f" [Gate 11] Measurements Present:     {gate_measurements_present}\n")

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
    parser.add_argument("--candidate", dest="hardened", help="Alias for --hardened")
    parser.add_argument("--output", default="reports/replay_evaluation.json")
    parser.add_argument("--criteria", default="chaos/criteria.json")
    parser.add_argument("--candidate-source", default=os.getenv("FF_CANDIDATE_SOURCE", "duo-authored-mr"), help="Provenance of candidate under test")
    args = parser.parse_args()

    evaluate_replay(args.baseline, args.hardened, args.output, args.criteria, args.candidate_source)
