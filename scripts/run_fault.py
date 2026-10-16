#!/usr/bin/env python3
import os
import sys
import time
import json
import uuid
import hashlib
import argparse
import requests
from typing import Dict, Any, List

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from chaos.toxiproxy_helper import ChaosEngine

def compute_profile_hash(profile: Dict[str, Any]) -> str:
    canonical = json.dumps(profile, sort_keys=True)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:12]

def run_probe(target_url: str, iterations: int = 5, timeout_sec: float = 6.0) -> Dict[str, Any]:
    latencies = []
    status_codes = []
    errors = []
    fallbacks = 0
    success_count = 0

    # Strict target health check: target must be reachable and return 200
    try:
        r_ping = requests.get(f"{target_url.rstrip('/')}/health", timeout=2.0)
        if r_ping.status_code != 200:
            print(f"[-] Target {target_url}/health returned status {r_ping.status_code}. Aborting probe.")
            sys.exit(1)
    except Exception as exc:
        print(f"[-] Target {target_url}/health is unreachable: {exc}. Aborting probe.")
        sys.exit(1)

    checkout_payload = {
        "order_id": f"ORD-{uuid.uuid4().hex[:8]}",
        "customer_id": "CUST-HACKATHON-2026",
        "destination_zip": "94103",
        "weight_kg": 2.5,
        "items": [
            {"item_id": "ITEM-1", "name": "Cloud Native Microservice Guide", "price": 49.99, "quantity": 1}
        ]
    }

    for _ in range(iterations):
        t0 = time.perf_counter()
        try:
            r = requests.post(
                f"{target_url.rstrip('/')}/api/v1/checkout",
                json=checkout_payload,
                timeout=timeout_sec
            )
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            latencies.append(elapsed_ms)
            status_codes.append(r.status_code)

            if r.status_code == 200:
                success_count += 1
                data = r.json()
                if data.get("shipping_details", {}).get("is_fallback"):
                    fallbacks += 1
            else:
                errors.append(f"HTTP {r.status_code}: {r.text[:100]}")
        except Exception as exc:
            elapsed_ms = round((time.perf_counter() - t0) * 1000, 2)
            latencies.append(elapsed_ms)
            status_codes.append(504)
            errors.append(str(exc)[:120])

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
        "avg_ms": avg
    }

def main():
    parser = argparse.ArgumentParser(description="FaultForge Chaos Experiment Runner")
    parser.add_argument("--profile", default="chaos/profiles/latency_cascading_hang.json", help="Path to chaos fault profile")
    parser.add_argument("--target", default="http://127.0.0.1:8090", help="Target application URL")
    parser.add_argument("--iterations", type=int, default=5, help="Number of probe iterations")
    parser.add_argument("--mode", choices=["baseline", "hardened"], default="baseline", help="Experiment execution mode")
    parser.add_argument("--expect-fail", action="store_true", help="Expect the run to fail (used for baseline verification without || true)")
    parser.add_argument("--allow-standalone-proxy", action="store_true", help="Allow StandaloneChaosProxy when Toxiproxy Docker daemon is unavailable")
    parser.add_argument("--output", default="reports/fault_run_result.json", help="Path to save probe results")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output), exist_ok=True)

    if not os.path.exists(args.profile):
        print(f"[-] Profile not found: {args.profile}")
        sys.exit(1)

    with open(args.profile, "r") as f:
        profile = json.load(f)

    profile_hash = compute_profile_hash(profile)
    run_id = f"run-{uuid.uuid4().hex[:8]}"

    print(f"\n=================================================================")
    print(f" FaultForge Chaos Injection Engine")
    print(f" Mode: {args.mode.upper()} | Fault: {profile.get('name')} ({profile_hash})")
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

    try:
        print(f"[*] Executing {args.iterations} probes against target ...")
        probe_results = run_probe(args.target, iterations=args.iterations)

        sla_budget = profile.get("sla_budget_ms", 1500)
        sla_breaches = sum(1 for lat in probe_results["latencies_ms"] if lat > sla_budget)
        passed_sla = (sla_breaches == 0) and (probe_results["failed_probes"] == 0)

        result_payload = {
            "run_id": run_id,
            "timestamp": time.time(),
            "mode": args.mode,
            "proxy_engine": "toxiproxy" if engine.use_toxi else "standalone",
            "profile_name": profile.get("name"),
            "profile_hash": profile_hash,
            "fault_type": profile.get("fault_type"),
            "sla_budget_ms": sla_budget,
            "sla_breaches": sla_breaches,
            "passed_sla": passed_sla,
            "metrics": probe_results
        }

        with open(args.output, "w") as f:
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
