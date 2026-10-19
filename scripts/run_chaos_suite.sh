#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail

echo "================================================================="
echo " FaultForge Chaos Test Suite: Real Toxiproxy Execution"
echo "================================================================="

COMPOSE_FILE="chaos/docker-compose.chaos.yml"

cleanup() {
  echo "[*] Tearing down chaos stack..."
  if command -v docker >/dev/null 2>&1; then
    docker compose -f "$COMPOSE_FILE" down -v --remove-orphans
  fi
}
trap cleanup EXIT

echo "[*] Checking Docker daemon availability..."
if ! command -v docker >/dev/null 2>&1; then
  echo "[-] ERROR: Docker daemon / CLI not available in environment."
  echo "    Run on a Docker-capable host or GitLab CI runner."
  exit 1
fi

echo "[*] Bringing up chaos stack (shipping-stub, toxiproxy, checkout app)..."
docker compose -f "$COMPOSE_FILE" up -d --build --wait

echo "[*] Executing baseline fault experiment (5 iterations, expect failure)..."
python3 scripts/run_fault.py --label baseline --iterations 5 --expect-fail --output reports/fault_run_baseline.json

echo "[+] Chaos suite baseline run successfully verified against real stack."
