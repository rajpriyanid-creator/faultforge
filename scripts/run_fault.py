#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
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
from typing import Tuple

def get_real_git_sha(explicit_sha: Optional[str] = None) -> Tuple[str, bool]:
    if explicit_sha and len(explicit_sha) == 40 and all(c in "0123456789abcdefABCDEF" for c in explicit_sha):
        return explicit_sha, True
    commit_sha = os.getenv("CI_COMMIT_SHA")
    if commit_sha and len(commit_sha) == 40 and all(c in "0123456789abcdefABCDEF" for c in commit_sha):
        return commit_sha, True
    try:
        commit_sha = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
        if commit_sha and len(commit_sha) == 40 and all(c in "0123456789abcdefABCDEF" for c in commit_sha):
            return commit_sha, True
    except Exception:
        pass
    return "UNKNOWN_NO_GIT", False

def verify_proxy_in_path(engine: ChaosEngine, profile: Dict[str, Any], proxy_listen_url: str = "http://127.0.0.1:8082") -> bool:
    """
    Proxy-in-path guard:
    Verifies that the chaos proxy is enabled, listening, and that the fault is actively in the path.
    Prevents false-greens from instant connection-refused fallbacks.
    """
    if engine.use_toxi:
        proxy_name = profile.get("proxy_name", "shipping_api_proxy")
        try:
            r = requests.get(f"{engine.toxi_client.api_url}/proxies/{proxy_name}", timeout=2.0)
            if r.status_code != 200:
                print(f"[-] Proxy guard failed: Proxy '{proxy_name}' not found on Toxiproxy API (HTTP {r.status_code})", file=sys.stderr)
                return False
            p_data = r.json()
            if not p_data.get("enabled"):
                print(f"[-] Proxy guard failed: Proxy '{proxy_name}' is disabled in Toxiproxy", file=sys.stderr)
                return False
            toxics = p_data.get("toxics", [])
            fault_type = profile.get("fault_type", "latency")
            if not any(fault_type in str(t.get("type", "")) for t in toxics):
                print(f"[-] Proxy guard failed: Toxic '{fault_type}' is not attached to proxy '{proxy_name}'", file=sys.stderr)
                return False
        except Exception as exc:
            print(f"[-] Proxy guard failed: Unable to query Toxiproxy API: {exc}", file=sys.stderr)
            return False

    # Also verify that a probe through proxy listen port is delayed as expected
    configured_latency = profile.get("attributes", {}).get("latency", 0)
    if configured_latency > 500:
        t0 = time.perf_counter()
        try:
            r = requests.get(f"{proxy_listen_url.rstrip('/')}/health", timeout=(configured_latency / 1000.0) + 3.0)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
            min_expected_ms = configured_latency * 0.4
            if elapsed_ms < min_expected_ms:
                print(f"[-] Proxy guard failed: Probe through {proxy_listen_url} completed in {elapsed_ms:.1f}ms (< expected {min_expected_ms:.1f}ms). Fault is not in path!", file=sys.stderr)
                return False
            print(f"[+] Proxy-in-path guard passed: {proxy_listen_url} confirmed active with delay ({elapsed_ms:.1f}ms).")
        except requests.exceptions.ConnectionError as ce:
            print(f"[-] Proxy guard failed: Connection refused on proxy listen port {proxy_listen_url}: {ce}", file=sys.stderr)
            return False
        except requests.exceptions.Timeout:
            print(f"[+] Proxy-in-path guard passed: Proxy {proxy_listen_url} timed out as expected under latency toxic.")
        except Exception as exc:
            print(f"[-] Proxy guard failed: Unexpected error probing {proxy_listen_url}: {exc}", file=sys.stderr)
            return False
    else:
        print("[+] Proxy-in-path guard passed: API and toxic presence confirmed.")
    return True

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

def run_probe(
    target_url: str,
    iterations: int = 5,
    timeout_sec: float = 6.0,
    reset_breaker_before_each: bool = False,
    index_offset: int = 0
) -> Dict[str, Any]:
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
        if reset_breaker_before_each:
            try:
                requests.post(f"{target_url.rstrip('/')}/resilience/circuit-breaker/reset", timeout=1.0)
            except Exception:
                pass

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
            "probe_index": index_offset + i + 1,
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
    parser.add_argument("--git-sha", default=None, help="Explicit 40-char git commit SHA for provenance tracking")
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
    git_sha, git_sha_verified = get_real_git_sha(args.git_sha)
    run_id = f"run-{uuid.uuid4().hex[:8]}"

    print(f"\n=================================================================")
    print(f" FaultForge Chaos Injection Engine")
    print(f" Label: {label.upper()} | Fault: {profile.get('name')} ({profile_hash})")
    print(f" Payload Hash: {payload_hash} | Git SHA: {git_sha[:8]}")
    print(f" Target: {args.target} | SLA Budget: {profile.get('sla_budget_ms')}ms")
    print(f"=================================================================\n")

    engine = ChaosEngine()
    if not engine.use_toxi:
        # Attempt automatic boot of official Toxiproxy daemon if not running
        try:
            from scripts.start_toxiproxy import start_toxiproxy
            if start_toxiproxy():
                engine = ChaosEngine()
        except Exception:
            pass

    if not engine.use_toxi:
        if not args.allow_standalone_proxy:
            print("[-] Error: Official Toxiproxy API (port 8474) is not reachable.", file=sys.stderr)
            print("    Real Toxiproxy is required. Pass --allow-standalone-proxy only for local dev without Docker.", file=sys.stderr)
            sys.exit(1)
        print("[!] Warning: Using StandaloneChaosProxy (--allow-standalone-proxy set).")

    engine.start()

    print(f"[*] Applying fault toxic: {profile.get('fault_type')} ...")
    engine.apply_profile(profile)

    toxic_readback = engine.read_back_toxic(profile)
    toxiproxy_ver = engine.get_version()

    # Compute and assert profile hash directly from the live Toxiproxy API readback
    if engine.use_toxi and isinstance(toxic_readback, dict):
        readback_attrs = toxic_readback.get("attributes", toxic_readback)
        readback_profile = dict(profile)
        readback_profile["attributes"] = {
            "jitter": readback_attrs.get("jitter", profile.get("attributes", {}).get("jitter", 250)),
            "latency": readback_attrs.get("latency", profile.get("attributes", {}).get("latency", 3500))
        }
        live_profile_hash = compute_profile_hash(readback_profile)
    else:
        live_profile_hash = compute_profile_hash(profile)

    expected_hash = profile.get("expected_hash", "644a89784316")
    if profile.get("name") == "latency_cascading_hang" and live_profile_hash != expected_hash:
        print(f"[-] ERROR: Toxiproxy live readback profile hash mismatch: expected {expected_hash}, got {live_profile_hash}", file=sys.stderr)
        sys.exit(1)

    profile_hash = live_profile_hash
    print(f"[*] Verified profile hash from live API: {profile_hash}")

    proxy_listen = os.getenv("SHIPPING_SERVICE_URL", "http://127.0.0.1:8082")
    if not verify_proxy_in_path(engine, profile, proxy_listen_url=proxy_listen):
        print("[-] FATAL: Proxy-in-path guard failed. Aborting experiment to prevent false green.", file=sys.stderr)
        sys.exit(1)

    try:
        sla_budget = profile.get("sla_budget_ms", 1500)

        if label == "candidate":
            print(f"[*] Running Candidate Replay in Two Phases (Phase A: Timeout-Only, Phase B: Breaker-Open) ...")
            # Phase A: Timeout-only (10 probes, reset breaker before each probe)
            print("[*] Phase A (Timeout-only, breaker reset before each probe, 10 probes)...")
            phase_a = run_probe(args.target, iterations=10, reset_breaker_before_each=True, index_offset=0)
            phase_a_breaches = sum(1 for lat in phase_a["latencies_ms"] if lat > sla_budget)
            phase_a["sla_breaches"] = phase_a_breaches

            # Phase B: Breaker-open (10 probes, breaker enabled)
            print("[*] Phase B (Circuit-breaker active, 10 probes)...")
            phase_b = run_probe(args.target, iterations=10, reset_breaker_before_each=False, index_offset=10)
            phase_b_breaches = sum(1 for lat in phase_b["latencies_ms"] if lat > sla_budget)
            phase_b["sla_breaches"] = phase_b_breaches
            phase_b["short_circuited_count"] = sum(1 for lat in phase_b["latencies_ms"] if lat < 150.0)

            all_per_requests = phase_a["per_request_results"] + phase_b["per_request_results"]
            all_latencies = phase_a["latencies_ms"] + phase_b["latencies_ms"]
            total_probes = len(all_latencies)
            total_success = phase_a["successful_probes"] + phase_b["successful_probes"]
            total_failed = phase_a["failed_probes"] + phase_b["failed_probes"]
            total_fallbacks = phase_a["fallback_count"] + phase_b["fallback_count"]
            sla_breaches = phase_a_breaches + phase_b_breaches
            passed_sla = (sla_breaches == 0) and (total_failed == 0)

            sorted_lat = sorted(all_latencies)
            p50 = sorted_lat[int(total_probes * 0.50)] if total_probes > 0 else 0
            p95 = sorted_lat[min(int(total_probes * 0.95), total_probes - 1)] if total_probes > 0 else 0
            p99 = sorted_lat[min(int(total_probes * 0.99), total_probes - 1)] if total_probes > 0 else 0
            avg = round(sum(all_latencies) / total_probes, 2) if total_probes > 0 else 0

            combined_metrics = {
                "total_probes": total_probes,
                "successful_probes": total_success,
                "failed_probes": total_failed,
                "fallback_count": total_fallbacks,
                "status_codes": phase_a["status_codes"] + phase_b["status_codes"],
                "errors": phase_a["errors"] + phase_b["errors"],
                "latencies_ms": all_latencies,
                "p50_ms": p50,
                "p95_ms": p95,
                "p99_ms": p99,
                "avg_ms": avg
            }

            result_payload = {
                "run_id": run_id,
                "timestamp": time.time(),
                "label": label,
                "git_sha": git_sha,
                "git_sha_verified": git_sha_verified,
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
                "phase_a_timeout_only": phase_a,
                "phase_b_breaker_open": phase_b,
                "per_request_results": all_per_requests,
                "metrics": combined_metrics
            }
        else:
            print(f"[*] Executing {args.iterations} probes against target ...")
            probe_results = run_probe(args.target, iterations=args.iterations)

            sla_breaches = sum(1 for lat in probe_results["latencies_ms"] if lat > sla_budget)
            passed_sla = (sla_breaches == 0) and (probe_results["failed_probes"] == 0)

            result_payload = {
                "run_id": run_id,
                "timestamp": time.time(),
                "label": label,
                "git_sha": git_sha,
                "git_sha_verified": git_sha_verified,
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
