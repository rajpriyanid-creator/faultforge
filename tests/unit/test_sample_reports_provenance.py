# SPDX-License-Identifier: MIT
import os
import json
import pytest
from datetime import datetime, timezone
from scripts.truth_audit import audit_sample_reports_provenance

def test_pipeline_window_validator_fails_when_timestamps_outside_window(tmp_path):
    """
    Test that audit_sample_reports_provenance fails if sample README claims
    a pipeline window that doesn't contain the timestamps in fault_run_*.json.
    """
    sample_dir = tmp_path / "sample_reports"
    sample_dir.mkdir(parents=True, exist_ok=True)

    baseline_ts = 1792690699.0870512
    hardened_ts = 1792690765.4687574

    (sample_dir / "fault_run_baseline.json").write_text(
        json.dumps({"timestamp": baseline_ts, "git_sha": "d64c35d4"}),
        encoding="utf-8"
    )
    (sample_dir / "fault_run_hardened.json").write_text(
        json.dumps({"timestamp": hardened_ts, "git_sha": "a1702b00"}),
        encoding="utf-8"
    )

    # Contradicting window
    readme_content = """# Sample Reports
## Provenance
- Pipeline Execution Window: `2026-10-22T18:00:55Z` to `2026-10-22T18:08:00Z`
"""
    (sample_dir / "README.md").write_text(readme_content, encoding="utf-8")

    violations = audit_sample_reports_provenance(str(sample_dir))
    assert len(violations) >= 2
    assert any("does not contain fault_run_baseline.json timestamp" in v for v in violations)
    assert any("does not contain fault_run_hardened.json timestamp" in v for v in violations)

def test_pipeline_window_validator_passes_when_timestamps_inside_window(tmp_path):
    """
    Test that audit_sample_reports_provenance passes when the claimed window
    accurately encloses the timestamps.
    """
    sample_dir = tmp_path / "sample_reports"
    sample_dir.mkdir(parents=True, exist_ok=True)

    baseline_ts = 1792766928.0  # 2026-10-23 14:48:48 UTC
    (sample_dir / "fault_run_baseline.json").write_text(
        json.dumps({"timestamp": baseline_ts, "git_sha": "d64c35d4"}),
        encoding="utf-8"
    )

    readme_content = """# Sample Reports
## Provenance
- Pipeline Execution Window: `2026-10-23T14:47:30Z` to `2026-10-23T14:55:01Z`
"""
    (sample_dir / "README.md").write_text(readme_content, encoding="utf-8")

    violations = audit_sample_reports_provenance(str(sample_dir))
    assert violations == []

def test_table_row_pipeline_window_fails_when_timestamp_outside(tmp_path):
    """
    Test that audit_sample_reports_provenance fails when a table row attributes
    a file to a pipeline whose execution window does not contain the row timestamp.
    """
    sample_dir = tmp_path / "sample_reports"
    sample_dir.mkdir(parents=True, exist_ok=True)

    readme_content = """# Sample Reports
## 1. Pipelines
- Pipeline ID: [2981670120](https://gitlab.com/...)
  Execution Window: `2026-10-23T14:47:30Z` to `2026-10-23T14:55:01Z`

## 2. Table
| Artifact File | Stage | SHA | Source Pipeline / Execution Context | Generation Time (UTC) | Notes |
|---|---|---|---|---|---|
| `issue.json` | `plan` | `d64c35d4` | Pipeline [2981670120] | 2026-10-22 16:46:39 | False attribution outside window |
"""
    (sample_dir / "README.md").write_text(readme_content, encoding="utf-8")

    violations = audit_sample_reports_provenance(str(sample_dir))
    assert len(violations) >= 1
    assert any("table row 'issue.json' attributes generation to pipeline 2981670120" in v for v in violations)
    assert any("falls outside this window" in v for v in violations)

def test_table_row_fails_when_pipeline_not_declared(tmp_path):
    """
    Test that audit_sample_reports_provenance fails when a table row references
    a pipeline that has no declared execution window in Section 1.
    """
    sample_dir = tmp_path / "sample_reports"
    sample_dir.mkdir(parents=True, exist_ok=True)

    readme_content = """# Sample Reports
## 1. Pipelines
- Pipeline ID: [2981670120](https://gitlab.com/...)
  Execution Window: `2026-10-23T14:47:30Z` to `2026-10-23T14:55:01Z`

## 2. Table
| Artifact File | Stage | SHA | Source Pipeline / Execution Context | Generation Time (UTC) | Notes |
|---|---|---|---|---|---|
| `fake_artifact.json` | `verify` | `d64c35d4` | Pipeline [2999999999] | 2026-10-23 14:50:00 | Undeclared pipeline |
"""
    (sample_dir / "README.md").write_text(readme_content, encoding="utf-8")

    violations = audit_sample_reports_provenance(str(sample_dir))
    assert len(violations) >= 1
    assert any("references pipeline 2999999999 which has no declared execution window" in v for v in violations)

def test_table_row_fails_when_missing_pipeline_and_local_run(tmp_path):
    """
    Test that audit_sample_reports_provenance fails when a table row has no pipeline
    reference and does not disclose 'Local run (pipeline not recorded)'.
    """
    sample_dir = tmp_path / "sample_reports"
    sample_dir.mkdir(parents=True, exist_ok=True)

    readme_content = """# Sample Reports
## 1. Pipelines
- Pipeline ID: [2981670120](https://gitlab.com/...)
  Execution Window: `2026-10-23T14:47:30Z` to `2026-10-23T14:55:01Z`

## 2. Table
| Artifact File | Stage | SHA | Source Pipeline / Execution Context | Generation Time (UTC) | Notes |
|---|---|---|---|---|---|
| `orphan_file.json` | `monitor` | `d64c35d4` | External host audit run | 2026-10-23 14:52:00 | Missing provenance |
"""
    (sample_dir / "README.md").write_text(readme_content, encoding="utf-8")

    violations = audit_sample_reports_provenance(str(sample_dir))
    assert len(violations) >= 1
    assert any("does not name a pipeline and does not disclose 'Local run (pipeline not recorded)'" in v for v in violations)

def test_table_row_pipeline_window_passes_when_timestamp_inside(tmp_path):
    """
    Test that audit_sample_reports_provenance passes when a row timestamp falls
    accurately inside the pipeline's window, or is marked as Local run.
    """
    sample_dir = tmp_path / "sample_reports"
    sample_dir.mkdir(parents=True, exist_ok=True)

    readme_content = """# Sample Reports
## 1. Pipelines
- Pipeline ID: [2981670120](https://gitlab.com/...)
  Execution Window: `2026-10-23T14:47:30Z` to `2026-10-23T14:55:01Z`
- Pipeline ID: [2967640493](https://gitlab.com/...)
  Execution Window: `2026-10-20T13:12:30Z` to `2026-10-20T13:19:09Z`

## 2. Table
| Artifact File | Stage | SHA | Source Pipeline / Execution Context | Generation Time (UTC) | Notes |
|---|---|---|---|---|---|
| `image_digest.txt` | `package` | `d64c35d4` | Pipeline [2981670120] | 2026-10-23 14:52:19 | Inside window |
| `release.json` | `release` | `d64c35d4` | Pipeline [2981670120] | 2026-10-23 14:53:44 | Inside window |
| `old_reference.json` | `release` | `275c598c` | Pipeline [2967640493] | 2026-10-20 13:17:54 | Inside ref window |
| `local_audit.json` | `plan` | `d64c35d4` | Local run (pipeline not recorded) | 2026-10-22 16:46:39 | Local run |
"""
    (sample_dir / "README.md").write_text(readme_content, encoding="utf-8")

    violations = audit_sample_reports_provenance(str(sample_dir))
    assert violations == []

def test_live_sample_reports_provenance_clean():
    """
    Test that the live docs/sample_reports directory passes provenance validation
    with zero violations.
    """
    violations = audit_sample_reports_provenance("docs/sample_reports")
    assert violations == [], f"Found provenance violations in docs/sample_reports: {violations}"

def test_sample_reports_provenance_table_matches_real_files():
    """
    Verify that the per-file table in docs/sample_reports/README.md matches the
    actual metadata from the sample report files.
    """
    readme_path = os.path.join("docs", "sample_reports", "README.md")
    assert os.path.exists(readme_path), "docs/sample_reports/README.md must exist"

    with open(readme_path, "r", encoding="utf-8") as f:
        readme_text = f.read()

    # Verify baseline run
    with open(os.path.join("docs", "sample_reports", "fault_run_baseline.json"), "r", encoding="utf-8") as f:
        baseline_data = json.load(f)
    baseline_sha = baseline_data["git_sha"][:8]
    assert baseline_sha == "d64c35d4"
    assert "fault_run_baseline.json" in readme_text
    assert "d64c35d4" in readme_text
    assert "2026-10-23 14:48:48" in readme_text

    # Verify hardened run
    with open(os.path.join("docs", "sample_reports", "fault_run_hardened.json"), "r", encoding="utf-8") as f:
        hardened_data = json.load(f)
    hardened_sha = hardened_data["git_sha"][:8]
    assert hardened_sha == "a1702b00"
    assert "fault_run_hardened.json" in readme_text
    assert "a1702b00" in readme_text
    assert "2026-10-23 14:50:08" in readme_text

    # Verify evidence receipt
    with open(os.path.join("docs", "sample_reports", "evidence_receipt.json"), "r", encoding="utf-8") as f:
        receipt_data = json.load(f)
    receipt_sha = receipt_data["commit_sha"][:8]
    assert receipt_sha == "d64c35d4"
    assert "evidence_receipt.json" in readme_text
    assert "d64c35d4" in readme_text
    assert "2026-10-23 14:54:54" in readme_text
    assert receipt_data["deployment"]["cloud_run_revision"] == "faultforge-checkout-00012-xoc"
    assert receipt_data["tamper_evident_seal_sha256"] == "77fcdade74cbb5040bf7301b4bb8c55827e3c15fab3dbae8e679fe18e1ae8a40"

    # Verify live Cloud Run release and verification
    with open(os.path.join("docs", "sample_reports", "release.json"), "r", encoding="utf-8") as f:
        rel_data = json.load(f)
    assert rel_data["status"] == "STAGED"
    assert rel_data["revision"] == "faultforge-checkout-00012-xoc"

    with open(os.path.join("docs", "sample_reports", "live_verification.json"), "r", encoding="utf-8") as f:
        live_data = json.load(f)
    assert live_data["traffic_split"]["verified"] is True
    assert live_data["traffic_split"]["candidate_percent"] == 10

def test_sample_reports_explains_pipeline_and_commits():
    """
    Verify that docs/sample_reports/README.md explains the primary CI pipeline 2981670120
    and key commit SHAs.
    """
    readme_path = os.path.join("docs", "sample_reports", "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_text = f.read()

    for item in ["2981670120", "d64c35d4", "3294042", "faultforge-checkout-00012-xoc", "77fcdade"]:
        assert item in readme_text, f"{item} must be documented in docs/sample_reports/README.md"
