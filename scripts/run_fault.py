#!/usr/bin/env python3
import os
import sys
import time
import json
import uuid
import random
import hashlib
import argparse
import subprocess
import requests
from typing import Dict, Any, List, Optional

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chaos.toxiproxy_helper import ChaosEngine

def get_real_git_sha() -> str:
    commit_sha = os.getenv("CI_COMMIT_SHA")
    if not commit_sha or len(commit_sha) != 40:
        try:
            commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        except Exception as exc:
            print(f"[-] Error: Unable to determine git commit SHA: {exc}", file=sys.stderr)
            sys.exit(1)
    if not commit_sha or len(commit_sha) != 40:
        print(f"[-] Error: Invalid git commit SHA '{commit_sha}' (must be 40 hex chars)", file=sys.stderr)
        sys.exit(1)
    return commit_sha

def compute_profile_hash(profile: Dict[str, Any]) -> str:
    canonical = json.dumps(profile, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

CANONICAL_PAYLOAD_TEMPLATE = {
    "customer_id": "CUST-HACKATHON-2026",
    "destination_zip": "94103",
    "weight_kg": 2.5,
    "items": [
        {"item_id": "ITEM-1", "name": "Cloud Native Microservice Guide", "price": 49.99, "quantity": 1}
    ]
}

def compute_payload_hash(payload_dict: Dict[str, Any]) -> str:
    canonical = json.dumps(payload_dict, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

def run_probe(target_url: str, iterations: int = 5, timeout_sec: float = 6.0) -> Dict[str, Any]:
    latencies = []
    status_codes = []
    errors = []
    fallbacks = 0
    success_count = 0
    per_request = []

    # Strict target health check: target must be reachable and return 200
    try:
        r_ping = requests.get(f"{target_url.rstrip('/')}/health", timeout=2.0)
        if r_ping.status_code != 200:
            print(f"[-] Target {target_url}/health returned status {r_ping.status_code}. Aborting probe.")
            sys.exit(1)
    except Exception as exc:
        print(f"[-] Target {target_url}/health is unreachable: {exc}. Aborting probe.")
        sys.exit(1)

    for i in range(iterations):
        req_id = f"ORD-{uuid.uuid4().hex[:8]}"
        payload = dict(CANONICAL_PAYLOAD_TEMPLATE)
        payload["order_id"] = req_id
        is_fallback = False
        is_estimate = False
        status_code = None
        error_msg = None

        t0 = time.perf_counter()
        try:
            r = requests.post(
                f"{target_url.rstrip('/')}/api/v1/checkout",
                json=payload,
                timeout=timeout_sec
            )
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            status_code = r.status_code
            latencies.append(elapsed_ms)
            status_codes.append(status_code)

            if r.status_code == 200:
                success_count += 1
                data = r.json()
                shipping = data.get("shipping_details", {})
                if shipping.get("is_fallback"):
                    fallbacks += 1
                    is_fallback = True
                if shipping.get("is_estimate"):
                    is_estimate = True
            else:
                error_msg = f"HTTP {r.status_code}: {r.text[:100]}"
                errors.append(error_msg)
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            status_code = 504
            latencies.append(elapsed_ms)
            status_codes.append(504)
            error_msg = str(exc)[:120]
            errors.append(error_msg)

        per_request.append({
            "probe_index": i + 1,
            "order_id": req_id,
            "latency_ms": elapsed_ms,
            "status_code": status_code,
            "is_fallback": is_fallback,
            "is_estimate": is_estimate,
            "error": error_msg
        })

    n = len(latencies)
    sorted_lat = sorted(latencies)
    p50 = sorted_lat[int(n * 0.50)] if n > 0 else 0
    p95 = sorted_lat[min(int(n * 0.95), n - 1)] if n > 0 else 0
    p99 = sorted_lat[min(int(n * 0.99), n - 1)] if n > 0 else 0
    avg = round(sum(latencies) / n, 2) if n > 0 else 0

    return {
        "total_probes": iterations,
        "successful_probes": success_count,
        "failed_probes": iterations - success_count,
        "fallback_count": fallbacks,
        "status_codes": status_codes,
        "errors": errors,
        "latencies_ms": latencies,
        "p50_ms": p50,
        "p95_ms": p95,
        "p99_ms": p99,
        "avg_ms": avg,
        "per_request_results": per_request
    }

def main():
    random.seed(42)
    parser = argparse.ArgumentParser(description="FaultForge Chaos Experiment Runner")
    parser.add_argument("--profile", default="chaos/profiles/latency_cascading_hang.json", help="Path to chaos fault profile")
    parser.add_argument("--target", default="http://127.0.0.1:8090", help="Target application URL")
    parser.add_argument("--iterations", type=int, default=5, help="Number of probe iterations")
    parser.add_argument("--label", choices=["baseline", "candidate"], default=None, help="Experiment execution label (baseline or candidate)")
    parser.add_argument("--mode", choices=["baseline", "candidate", "hardened"], default=None, help="Legacy alias for --label")
    parser.add_argument("--expect-fail", action="store_true", help="Expect the run to fail (used for baseline verification without || true)")
    parser.add_argument("--allow-standalone-proxy", action="store_true", help="Allow StandaloneChaosProxy when Toxiproxy Docker daemon is unavailable")
    parser.add_argument("--output", default="reports/fault_run_result.json", help="Path to save probe results")
    args = parser.parse_args()

    # Determine execution label
    label = args.label
    if not label:
        if args.mode:
            label = "candidate" if args.mode in ("hardened", "candidate") else "baseline"
        else:
            label = "baseline"

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    if not os.path.exists(args.profile):
        print(f"[-] Profile not found: {args.profile}")
        sys.exit(1)

    with open(args.profile, "r", encoding="utf-8") as f:
        profile = json.load(f)

    profile_hash = compute_profile_hash(profile)
    payload_hash = compute_payload_hash(CANONICAL_PAYLOAD_TEMPLATE)
    git_sha = get_real_git_sha()
    run_id = f"run-{uuid.uuid4().hex[:8]}"

    print(f"\n=================================================================")
    print(f" FaultForge Chaos Injection Engine")
    print(f" Label: {label.upper()} | Fault: {profile.get('name')} ({profile_hash})")
    print(f" Payload Hash: {payload_hash} | Git SHA: {git_sha[:8]}")
    print(f" Target: {args.target} | SLA Budget: {profile.get('sla_budget_ms')}ms")
    print(f"=================================================================\n")

    engine = ChaosEngine()
    if not engine.use_toxi:
        if not args.allow_standalone_proxy:
            print("[-] Error: Official Toxiproxy API (port 8474) is not reachable.")
            print("    Real Toxiproxy is required. Pass --allow-standalone-proxy only for local dev without Docker.")
            sys.exit(1)
        print("[!] Warning: Using StandaloneChaosProxy (--allow-standalone-proxy set).")

    engine.start()

    print(f"[*] Applying fault toxic: {profile.get('fault_type')} ...")
    engine.apply_profile(profile)

    toxic_readback = engine.read_back_toxic(profile)
    toxiproxy_ver = engine.get_version()

    try:
        print(f"[*] Executing {args.iterations} probes against target ...")
        probe_results = run_probe(args.target, iterations=args.iterations)

        sla_budget = profile.get("sla_budget_ms", 1500)
        sla_breaches = sum(1 for lat in probe_results["latencies_ms"] if lat > sla_budget)
        passed_sla = (sla_breaches == 0) and (probe_results["failed_probes"] == 0)

        result_payload = {
            "run_id": run_id,
            "timestamp": time.time(),
            "label": label,
            "git_sha": git_sha,
            "proxy_engine": "toxiproxy" if engine.use_toxi else "standalone",
            "toxiproxy_version": toxiproxy_ver,
            "profile_name": profile.get("name"),
            "profile_hash": profile_hash,
            "payload_hash": payload_hash,
            "fault_type": profile.get("fault_type"),
            "toxic_readback": toxic_readback,
            "sla_budget_ms": sla_budget,
            "sla_breaches": sla_breaches,
            "passed_sla": passed_sla,
            "per_request_results": probe_results.get("per_request_results", []),
            "metrics": {
                "total_probes": probe_results["total_probes"],
                "successful_probes": probe_results["successful_probes"],
                "failed_probes": probe_results["failed_probes"],
                "fallback_count": probe_results["fallback_count"],
                "status_codes": probe_results["status_codes"],
                "errors": probe_results["errors"],
                "latencies_ms": probe_results["latencies_ms"],
                "p50_ms": probe_results["p50_ms"],
                "p95_ms": probe_results["p95_ms"],
                "p99_ms": probe_results["p99_ms"],
                "avg_ms": probe_results["avg_ms"]
            }
        }

        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result_payload, f, indent=2)

        print(f"\n[+] Probe results saved to {args.output}")
        print(f"    Total: {probe_results['total_probes']} | Success: {probe_results['successful_probes']} | Fallbacks: {probe_results['fallback_count']}")
        print(f"    Avg Latency: {probe_results['avg_ms']}ms | p95: {probe_results['p95_ms']}ms | SLA Breaches: {sla_breaches}")
        print(f"    Status: {'PASS (SLA Met)' if passed_sla else 'FAIL (SLA Breached / Errors Occurred)'}\n")

        if args.expect_fail:
            if not passed_sla:
                print("[+] Baseline failure confirmed as expected under chaos.")
                sys.exit(0)
            else:
                print("[-] Expected baseline failure, but probes unexpectedly passed!")
                sys.exit(1)
        else:
            if passed_sla:
                sys.exit(0)
            else:
                print("[-] Probe failed SLA or had errors.")
                sys.exit(1)

    finally:
        print("[*] Clearing fault injection and restoring baseline...")
        engine.clear()
        engine.stop()

if __name__ == "__main__":
    main()
