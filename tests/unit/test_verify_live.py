# SPDX-License-Identifier: MIT
import json
import os
import pytest
from scripts.verify_live import verify_live_service

def test_verify_live_identifies_majority_production_revision(tmp_path, monkeypatch):
    """
    Test that verify_live_service picks the true majority revision (highest percent)
    as production_revision, rather than just the last non-candidate item in the list.
    """
    out_file = str(tmp_path / "live_verification.json")

    mock_gcloud_payload = {
        "status": {
            "traffic": [
                {"percent": 49, "revisionName": "faultforge-checkout-00002-kpl"},
                {"percent": 6, "revisionName": "faultforge-checkout-00010-baz"},
                {"percent": 5, "revisionName": "faultforge-checkout-00012-xoc"},
                {"percent": 6, "revisionName": "faultforge-checkout-00014-vey"},
                {"percent": 7, "revisionName": "faultforge-checkout-00016-sav"},
                {"percent": 8, "revisionName": "faultforge-checkout-00018-tox"},
                {"percent": 9, "revisionName": "faultforge-checkout-00020-woy"},
                {
                    "percent": 10,
                    "revisionName": "faultforge-checkout-00022-dej",
                    "tag": "candidate",
                    "url": "https://candidate---faultforge-checkout.run.app"
                }
            ]
        }
    }

    class MockSubprocess:
        returncode = 0
        stdout = json.dumps(mock_gcloud_payload)
        stderr = ""

    def mock_run(cmd, *args, **kwargs):
        return MockSubprocess()

    import subprocess
    monkeypatch.setattr(subprocess, "run", mock_run)

    record = verify_live_service(
        service_url="http://mock-service",
        output_path=out_file
    )

    assert os.path.exists(out_file)
    assert record["traffic_split"]["verified"] is True
    assert record["traffic_split"]["candidate_percent"] == 10
    assert record["traffic_split"]["production_percent"] == 90
    assert record["traffic_split"]["candidate_revision"] == "faultforge-checkout-00022-dej"
    # Must be the majority revision with 49%, NOT the last revision with 9% (00020-woy)
    assert record["traffic_split"]["production_revision"] == "faultforge-checkout-00002-kpl"

def test_verify_live_clean_90_10_traffic_split(tmp_path, monkeypatch):
    """
    Test clean 90/10 traffic split with exactly one stable and one candidate revision.
    """
    out_file = str(tmp_path / "live_verification.json")

    mock_gcloud_payload = {
        "status": {
            "traffic": [
                {"percent": 90, "revisionName": "faultforge-checkout-00002-kpl"},
                {
                    "percent": 10,
                    "revisionName": "faultforge-checkout-00024-can",
                    "tag": "candidate",
                    "url": "https://candidate---faultforge-checkout.run.app"
                }
            ]
        }
    }

    class MockSubprocess:
        returncode = 0
        stdout = json.dumps(mock_gcloud_payload)
        stderr = ""

    def mock_run(cmd, *args, **kwargs):
        return MockSubprocess()

    import subprocess
    monkeypatch.setattr(subprocess, "run", mock_run)

    record = verify_live_service(
        service_url="http://mock-service",
        output_path=out_file
    )

    assert record["traffic_split"]["verified"] is True
    assert record["traffic_split"]["candidate_percent"] == 10
    assert record["traffic_split"]["production_percent"] == 90
    assert record["traffic_split"]["production_revision"] == "faultforge-checkout-00002-kpl"
    assert record["traffic_split"]["candidate_revision"] == "faultforge-checkout-00024-can"
