#!/usr/bin/env python3
import os
import sys
import shutil
import subprocess

def main():
    print("=================================================================")
    print(" FaultForge Chaos Test Suite: Real Toxiproxy Execution")
    print("=================================================================")

    compose_file = "chaos/docker-compose.chaos.yml"
    docker_bin = shutil.which("docker")
    if not docker_bin:
        print("[-] ERROR: Docker CLI / daemon not found in PATH.")
        print("    Real Toxiproxy execution requires Docker Desktop or Docker Engine.")
        print("    Exact command to run on a Docker host:")
        print("      docker compose -f chaos/docker-compose.chaos.yml up -d --build --wait")
        print("      python scripts/run_fault.py --label baseline --iterations 5 --expect-fail --output reports/fault_run_baseline.json")
        print("      docker compose -f chaos/docker-compose.chaos.yml down -v")
        sys.exit(1)

    try:
        print("[*] Bringing up chaos services: shipping-stub, toxiproxy, app...")
        subprocess.check_call(["docker", "compose", "-f", compose_file, "up", "-d", "--build", "--wait"])

        print("[*] Executing baseline fault experiment (5 iterations, expect failure on SLA budget)...")
        subprocess.check_call([
            sys.executable, "scripts/run_fault.py",
            "--label", "baseline",
            "--iterations", "5",
            "--expect-fail",
            "--output", "reports/fault_run_baseline.json"
        ])
        print("[+] Chaos suite baseline verification PASSED: Real failure confirmed without masks.")
    finally:
        print("[*] Tearing down chaos stack and ensuring toxics reset...")
        try:
            sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
            from chaos.toxiproxy_helper import ChaosEngine
            engine = ChaosEngine()
            engine.clear()
            engine.stop()
        except Exception:
            pass
        subprocess.run(["docker", "compose", "-f", compose_file, "down", "-v", "--remove-orphans"])

if __name__ == "__main__":
    main()
