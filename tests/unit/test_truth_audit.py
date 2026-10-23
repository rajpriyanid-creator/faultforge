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

def test_audit_docs_claims_detects_stale_numbers(tmp_path, monkeypatch):
    from scripts.truth_audit import audit_docs_claims
    monkeypatch.chdir(tmp_path)

    # Create dummy README with stale metric 3446.08 ms
    (tmp_path / "README.md").write_text("Observed baseline latency 3446.08 ms under 1500ms SLA budget with culprit 974035c and 9 Stages", encoding="utf-8")
    violations = audit_docs_claims()
    assert any("Stale metric detected" in v and "3446" in v for v in violations)

def test_audit_docs_claims_detects_mismatched_replay_metrics(tmp_path, monkeypatch):
    from scripts.truth_audit import audit_docs_claims
    monkeypatch.chdir(tmp_path)

    docs_dir = tmp_path / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    sample_dir = docs_dir / "sample_reports"
    sample_dir.mkdir(parents=True, exist_ok=True)

    # Create replay_evaluation.json with specific baseline_avg_ms
    (sample_dir / "replay_evaluation.json").write_text(json.dumps({
        "raw_metrics": {
            "baseline_avg_ms": 4212.32,
            "hardened_avg_ms": 825.56,
            "hardened_p95_ms": 1472.12
        }
    }), encoding="utf-8")

    # README with mismatched number (e.g. 5000.00ms instead of 4212.32)
    (tmp_path / "README.md").write_text("SLA budget 1500ms, 9 Stages, culprit 974035c, mean 5000.00ms", encoding="utf-8")
    violations = audit_docs_claims()
    assert any("Baseline mean 4212.32ms from replay_evaluation.json missing in README" in v for v in violations)

def test_audit_docs_claims_clean_on_repo():
    from scripts.truth_audit import audit_docs_claims
    violations = audit_docs_claims()
    assert len(violations) == 0, f"Expected clean audit on repo, got: {violations}"
