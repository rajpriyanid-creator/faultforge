# SPDX-License-Identifier: MIT
import os
import json
import pytest
from scripts.cloudrun_traffic import rollback_to_stable

def test_rollback_dry_run(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    result = rollback_to_stable(
        service="faultforge-checkout",
        region="us-central1",
        stable_revision="faultforge-checkout-00001",
        dry_run=True,
        provider="docker-compose"
    )

    assert result["rollback_executed"] is True
    assert result["provider"] == "docker-compose"
    assert result["target_service"] == "faultforge-checkout"
    assert result["restored_revision"] == "faultforge-checkout-00001"
    assert result["traffic_allocation"] == {"faultforge-checkout-00001": 100}
    assert result["health_reverified"] is True
    assert os.path.exists("reports/rollback.json")

    with open("reports/rollback.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["target_service"] == "faultforge-checkout"
    assert data["restored_revision"] == "faultforge-checkout-00001"
