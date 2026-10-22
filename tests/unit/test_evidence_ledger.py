# SPDX-License-Identifier: MIT
import os
import json
import pytest
from scripts.evidence_ledger import record_stage, load_ledger, hash_file_sha256

def test_hash_file_sha256(tmp_path):
    p = tmp_path / "test.txt"
    p.write_bytes(b"hello faultforge")
    h = hash_file_sha256(str(p))
    assert len(h) == 64
    assert isinstance(h, str)

def test_evidence_ledger_records_verified_artifacts(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    art1 = reports_dir / "art1.json"
    art1.write_text('{"foo": "bar"}', encoding="utf-8")

    ledger_path = str(reports_dir / "stage_ledger.json")
    entry = record_stage(
        stage="plan",
        job="plan:incident_tracking",
        status="SUCCESS",
        artifacts=[str(art1)],
        ledger_path=ledger_path
    )

    assert entry["status"] == "SUCCESS"
    assert len(entry["artifacts_details"]) == 1
    assert entry["artifacts_details"][0]["path"] == str(art1)
    assert entry["artifacts_details"][0]["size_bytes"] > 0
    assert len(entry["artifacts_details"][0]["sha256"]) == 64

    # Verify ledger file
    ledger = load_ledger(ledger_path)
    assert "plan" in ledger["stages"]
    assert ledger["stages"]["plan"]["status"] == "SUCCESS"

def test_evidence_ledger_refuses_success_on_missing_or_empty_artifact(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    empty_art = reports_dir / "empty.txt"
    empty_art.touch() # 0 bytes
    missing_art = reports_dir / "missing.txt"

    ledger_path = str(reports_dir / "stage_ledger.json")

    # Empty artifact must fail
    with pytest.raises(SystemExit):
        record_stage(
            stage="verify",
            job="verify:test",
            status="SUCCESS",
            artifacts=[str(empty_art)],
            ledger_path=ledger_path
        )

    # Missing artifact must fail
    with pytest.raises(SystemExit):
        record_stage(
            stage="verify",
            job="verify:test",
            status="SUCCESS",
            artifacts=[str(missing_art)],
            ledger_path=ledger_path
        )

def test_evidence_ledger_accepts_skipped_and_failed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    ledger_path = str(reports_dir / "stage_ledger.json")

    skip_entry = record_stage(
        stage="release",
        job="release:cloudrun_candidate_deploy",
        status="SKIPPED",
        artifacts=[],
        notes="No GCP credentials",
        ledger_path=ledger_path
    )
    assert skip_entry["status"] == "SKIPPED"

    fail_entry = record_stage(
        stage="verify",
        job="verify:exact_fault_replay_proof",
        status="FAILED",
        artifacts=[],
        notes="Regression detected",
        ledger_path=ledger_path
    )
    assert fail_entry["status"] == "FAILED"

    ledger = load_ledger(ledger_path)
    assert ledger["stages"]["release"]["status"] == "SKIPPED"
    assert ledger["stages"]["verify"]["status"] == "FAILED"

def test_evidence_ledger_accepts_partial_and_not_executed(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()
    ledger_path = str(reports_dir / "stage_ledger.json")

    partial_entry = record_stage(
        stage="create",
        job="create:duo_remediation_mr",
        status="PARTIAL",
        artifacts=[],
        notes="Duo flow not executed",
        ledger_path=ledger_path
    )
    assert partial_entry["status"] == "PARTIAL"

    not_exec_entry = record_stage(
        stage="create",
        job="create:duo_remediation_mr",
        status="NOT_EXECUTED",
        artifacts=[],
        notes="No Duo credits",
        ledger_path=ledger_path
    )
    assert not_exec_entry["status"] == "NOT_EXECUTED"

    ledger = load_ledger(ledger_path)
    assert ledger["stages"]["create"]["status"] == "NOT_EXECUTED"
