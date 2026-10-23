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

    # 17:38:19 UTC and 17:39:25 UTC on 2026-10-22
    baseline_ts = 1792690699.0870512
    hardened_ts = 1792690765.4687574

    (sample_dir / "fault_run_baseline.json").write_text(
        json.dumps({"timestamp": baseline_ts, "git_sha": "b063a91b"}),
        encoding="utf-8"
    )
    (sample_dir / "fault_run_hardened.json").write_text(
        json.dumps({"timestamp": hardened_ts, "git_sha": "f8aa9d98"}),
        encoding="utf-8"
    )

    # Contradicting window (18:00:55Z to 18:08:00Z)
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

    baseline_ts = 1792690699.0870512  # 17:38:19 UTC
    (sample_dir / "fault_run_baseline.json").write_text(
        json.dumps({"timestamp": baseline_ts, "git_sha": "b063a91b"}),
        encoding="utf-8"
    )

    readme_content = """# Sample Reports
## Provenance
- Pipeline Execution Window: `2026-10-22T17:30:00Z` to `2026-10-22T17:45:00Z`
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
- Pipeline ID: [2977803091](https://gitlab.com/...)
  Execution Window: `2026-10-22T18:00:55Z` to `2026-10-22T18:08:00Z`

## 2. Table
| Artifact File | Stage | SHA | Source Pipeline / Execution Context | Generation Time (UTC) | Notes |
|---|---|---|---|---|---|
| `issue.json` | `plan` | `b063a91b` | Pipeline [2977803091] | 2026-10-22 16:46:39 | False attribution outside window |
"""
    (sample_dir / "README.md").write_text(readme_content, encoding="utf-8")

    violations = audit_sample_reports_provenance(str(sample_dir))
    assert len(violations) >= 1
    assert any("table row 'issue.json' attributes generation to pipeline 2977803091" in v for v in violations)
    assert any("falls outside this window" in v for v in violations)

def test_table_row_pipeline_window_passes_when_timestamp_inside(tmp_path):
    """
    Test that audit_sample_reports_provenance passes when a row timestamp falls
    accurately inside the pipeline's window, or is marked as Local run.
    """
    sample_dir = tmp_path / "sample_reports"
    sample_dir.mkdir(parents=True, exist_ok=True)

    readme_content = """# Sample Reports
## 1. Pipelines
- Pipeline ID: [2977803091](https://gitlab.com/...)
  Execution Window: `2026-10-22T18:00:55Z` to `2026-10-22T18:08:00Z`
- Pipeline ID: [2967640493](https://gitlab.com/...)
  Execution Window: `2026-10-20T13:12:30Z` to `2026-10-20T13:19:09Z`

## 2. Table
| Artifact File | Stage | SHA | Source Pipeline / Execution Context | Generation Time (UTC) | Notes |
|---|---|---|---|---|---|
| `image_digest.txt` | `package` | `e5a9752b` | Pipeline [2977803091] | 2026-10-22 18:04:12 | Inside window |
| `release.json` | `release` | `275c598c` | Pipeline [2967640493] | 2026-10-20 13:17:54 | Inside window |
| `issue.json` | `plan` | `b063a91b` | Local run (pipeline not recorded) | 2026-10-22 16:46:39 | Local run |
"""
    (sample_dir / "README.md").write_text(readme_content, encoding="utf-8")

    violations = audit_sample_reports_provenance(str(sample_dir))
    assert violations == []

def test_table_row_fails_when_receipt_attributed_to_job(tmp_path):
    """
    Test that attributing evidence_receipt.json to job 17392416795 without
    disclosing local sealing fails.
    """
    sample_dir = tmp_path / "sample_reports"
    sample_dir.mkdir(parents=True, exist_ok=True)

    readme_content = """# Sample Reports
## 2. Table
| Artifact File | Stage | SHA | Source Pipeline / Execution Context | Generation Time (UTC) | Notes |
|---|---|---|---|---|---|
| `evidence_receipt.json` | `govern` | `372ef5f9` | Pipeline 2977803091 / Job 17392416795 | 2026-10-23 03:44:01 | Falsely attributed |
"""
    (sample_dir / "README.md").write_text(readme_content, encoding="utf-8")

    violations = audit_sample_reports_provenance(str(sample_dir))
    assert any("attributes evidence_receipt.json to job 17392416795" in v for v in violations)

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
    assert baseline_sha == "b063a91b"
    assert "fault_run_baseline.json" in readme_text
    assert "b063a91b" in readme_text
    assert "2026-10-22 17:38:19" in readme_text

    # Verify hardened run
    with open(os.path.join("docs", "sample_reports", "fault_run_hardened.json"), "r", encoding="utf-8") as f:
        hardened_data = json.load(f)
    hardened_sha = hardened_data["git_sha"][:8]
    assert hardened_sha == "f8aa9d98"
    assert "fault_run_hardened.json" in readme_text
    assert "f8aa9d98" in readme_text
    assert "2026-10-22 17:39:25" in readme_text

    # Verify evidence receipt
    with open(os.path.join("docs", "sample_reports", "evidence_receipt.json"), "r", encoding="utf-8") as f:
        receipt_data = json.load(f)
    receipt_sha = receipt_data["commit_sha"][:8]
    assert receipt_sha == "372ef5f9"
    assert "evidence_receipt.json" in readme_text
    assert "372ef5f9" in readme_text
    assert "2026-10-23 03:44:01" in readme_text

def test_sample_reports_explains_all_four_shas():
    """
    Verify that docs/sample_reports/README.md explains the 4 distinct SHAs:
    b063a91b (baseline), f8aa9d98 (candidate fix MR), 372ef5f9 (receipt sealing),
    and e5a9752b (GitLab CI pipeline).
    """
    readme_path = os.path.join("docs", "sample_reports", "README.md")
    with open(readme_path, "r", encoding="utf-8") as f:
        readme_text = f.read()

    for sha in ["b063a91b", "f8aa9d98", "372ef5f9", "e5a9752b"]:
        assert sha in readme_text, f"SHA {sha} must be documented and explained in docs/sample_reports/README.md"
