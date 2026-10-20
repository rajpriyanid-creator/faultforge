# SPDX-License-Identifier: MIT
import os
import json
import pytest
from scripts.truth_audit import (
    audit_timestamps,
    audit_forbidden_patterns,
    audit_report_consistency
)

def test_audit_timestamps_detects_multiples_of_30():
    # 3 consecutive exact multiples of 30s
    stale_ts = [1729350000.0, 1729350030.0, 1729350060.0]
    violations = audit_timestamps(stale_ts, first_commit_ts=1700000000.0)
    assert any("exact multiples of 30/60s" in v for v in violations)

def test_audit_timestamps_detects_evenly_spaced_intervals():
    # Evenly spaced (e.g. exactly 15.00s apart)
    evenly_spaced = [1729350001.25, 1729350016.25, 1729350031.25]
    violations = audit_timestamps(evenly_spaced, first_commit_ts=1700000000.0)
    assert any("evenly spaced intervals" in v for v in violations)

def test_audit_timestamps_detects_future_timestamp():
    future_ts = [9999999999.0]
    violations = audit_timestamps(future_ts, first_commit_ts=1700000000.0)
    assert any("in the future" in v for v in violations)

def test_audit_timestamps_detects_pre_inception_timestamp():
    ancient_ts = [1000000000.0]  # Year 2001, prior to repo first commit
    violations = audit_timestamps(ancient_ts, first_commit_ts=1729000000.0)
    assert any("before repository's first commit date" in v for v in violations)

def test_audit_timestamps_passes_natural_durations():
    natural_ts = [1729350100.12, 1729350153.47, 1729350189.91]
    violations = audit_timestamps(natural_ts, first_commit_ts=1729000000.0)
    assert len(violations) == 0

def test_audit_report_consistency_detects_invalid_mr_url(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    receipt_file = reports_dir / "evidence_receipt.json"
    with open(receipt_file, "w") as f:
        json.dump({
            "commit_sha": "a" * 40,
            "generated_at": 1729350100.0,
            "urls": {
                "merge_request_url": "https://gitlab.com/project/-/work_items/30"
            }
        }, f)

    violations = audit_report_consistency(final_mode=False)
    assert any("Invalid merge_request_url" in v for v in violations)

def test_audit_report_consistency_detects_missing_verified_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    ledger_file = reports_dir / "stage_ledger.json"
    with open(ledger_file, "w") as f:
        json.dump({
            "stages": {
                "release": {
                    "stage": "release",
                    "commit_sha": "a" * 40,
                    "timestamp": 1729350100.0,
                    "artifacts_details": [
                        {"path": "reports/release.json", "sha256": "abc123def456"}
                    ]
                }
            }
        }, f)

    violations = audit_report_consistency(final_mode=False)
    assert any("verified artifact missing on disk: reports/release.json" in v for v in violations)
