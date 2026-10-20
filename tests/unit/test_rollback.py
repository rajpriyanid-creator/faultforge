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

def test_cloudrun_traffic_refuses_promotion_without_approval_flag(monkeypatch):
    import sys
    from scripts import cloudrun_traffic
    monkeypatch.setattr(sys, "argv", [
        "cloudrun_traffic.py",
        "--action", "route",
        "--service", "faultforge-checkout",
        "--revisions", "candidate=100",
        "--provider", "cloudrun"
    ])
    with pytest.raises(SystemExit) as exc:
        cloudrun_traffic.main()
    assert exc.value.code == 1

def test_gitlab_ci_manual_promotion_gate_defined():
    ci_file = os.path.join(os.path.dirname(__file__), "..", "..", ".gitlab-ci.yml")
    with open(ci_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert "govern:promote_to_production:" in content
    assert "when: manual" in content
    assert "allow_failure: false" in content
