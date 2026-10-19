#!/bin/bash
# SPDX-License-Identifier: MIT
# FaultForge Local Supervised Gate Controller
# Simulates human approval and instant rollback without GCP credentials

set -euo pipefail

GATE_DIR="gate_data"
mkdir -p "$GATE_DIR"

ACTION="${1:-status}"

case "$ACTION" in
  start)
    echo "[+] Starting Local Supervised Staging Stack..."
    rm -f "$GATE_DIR/APPROVE" "$GATE_DIR/ROLLBACK"
    docker compose -f docker-compose.supervised.yml up -d
    echo "[+] Staging candidate active at http://localhost:8080"
    echo "[+] Supervised gate waiting for human approval. Run: ./scripts/local_gate.sh approve"
    ;;
  approve)
    echo "[+] Emitting Human Approval Signal..."
    touch "$GATE_DIR/APPROVE"
    rm -f "$GATE_DIR/ROLLBACK"
    echo "[✓] Human approval detected! Candidate promoted to 100% production traffic."
    ;;
  rollback)
    echo "[!] Emitting Rollback Signal..."
    touch "$GATE_DIR/ROLLBACK"
    rm -f "$GATE_DIR/APPROVE"
    echo "[!] Reverting candidate container to last-known-good stable..."
    docker compose -f docker-compose.supervised.yml down
    echo "[✓] Rollback complete. Stable restored."
    ;;
  status)
    if [ -f "$GATE_DIR/APPROVE" ]; then
      echo "Status: PROMOTED (Human approved for 100% production traffic)"
    elif [ -f "$GATE_DIR/ROLLBACK" ]; then
      echo "Status: ROLLED_BACK (Reverted to stable)"
    else
      echo "Status: BLOCKED_PENDING_APPROVAL (Staging active, awaiting human review)"
    fi
    ;;
  stop)
    echo "[+] Stopping Supervised Staging Stack..."
    docker compose -f docker-compose.supervised.yml down
    rm -f "$GATE_DIR/APPROVE" "$GATE_DIR/ROLLBACK"
    ;;
  *)
    echo "Usage: $0 {start|approve|rollback|status|stop}"
    exit 1
    ;;
esac
