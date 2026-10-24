# SPDX-License-Identifier: MIT
"""
Tests for automated and simulated rollback functionality.
Validates traffic reallocation, stable revision restoration, and local gate signaling.
"""
import os
import json
import pytest
from pathlib import Path
from scripts.cloudrun_traffic import rollback_to_stable
from scripts.local_gate import cmd_start, cmd_approve, cmd_rollback, cmd_status, cmd_stop, APPROVE_FILE, ROLLBACK_FILE

def test_cloudrun_traffic_rollback_simulation(tmp_path, monkeypatch):
    """Asserts rollback restores traffic to stable revision and records rollback receipt."""
    monkeypatch.chdir(tmp_path)
    res = rollback_to_stable(
        service="faultforge-checkout",
        region="us-central1",
        stable_revision="faultforge-checkout-00001",
        dry_run=True,
        provider="docker-compose"
    )

    assert res["rollback_executed"] is True
    assert res["provider"] == "docker-compose"
    assert res["target_service"] == "faultforge-checkout"
    assert res["restored_revision"] == "faultforge-checkout-00001"
    assert res["traffic_allocation"] == {"faultforge-checkout-00001": 100}
    assert res["health_reverified"] is True
    assert os.path.exists("reports/rollback.json")

    with open("reports/rollback.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["target_service"] == "faultforge-checkout"
    assert data["restored_revision"] == "faultforge-checkout-00001"
    assert data["traffic_allocation"] == {"faultforge-checkout-00001": 100}

def test_local_gate_controller_lifecycle(tmp_path, monkeypatch):
    """Asserts that local gate handles approve and rollback signals deterministically."""
    monkeypatch.chdir(tmp_path)

    # 1. Start gate -> both marker files absent
    cmd_start()
    assert not APPROVE_FILE.exists()
    assert not ROLLBACK_FILE.exists()

    # 2. Approve gate -> APPROVE file created
    cmd_approve()
    assert APPROVE_FILE.exists()
    assert not ROLLBACK_FILE.exists()

    # 3. Rollback gate -> ROLLBACK file created, APPROVE removed
    cmd_rollback()
    assert not APPROVE_FILE.exists()
    assert ROLLBACK_FILE.exists()

    # 4. Stop gate -> all cleaned up
    cmd_stop()
    assert not APPROVE_FILE.exists()
    assert not ROLLBACK_FILE.exists()
