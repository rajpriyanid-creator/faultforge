# SPDX-License-Identifier: MIT
import os
import json
import hashlib
import pytest
from scripts.generate_receipt import generate_evidence_receipt

def test_generate_receipt_creates_valid_seal(tmp_path):
    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)

    json_path = str(tmp_path / "evidence_receipt.json")
    md_path = str(tmp_path / "EVIDENCE_RECEIPT.md")

    receipt = generate_evidence_receipt(reports_dir, json_path, md_path)
    assert os.path.exists(json_path)
    assert os.path.exists(md_path)
    assert len(receipt["tamper_evident_seal_sha256"]) == 64

    # Recalculate canonical hash
    seal = receipt.pop("tamper_evident_seal_sha256")
    calc_seal = hashlib.sha256(json.dumps(receipt, sort_keys=True).encode("utf-8")).hexdigest()
    assert seal == calc_seal

def test_generate_receipt_refuses_recovered_when_inputs_missing(tmp_path):
    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)

    json_path = str(tmp_path / "evidence_receipt.json")
    md_path = str(tmp_path / "EVIDENCE_RECEIPT.md")

    receipt = generate_evidence_receipt(reports_dir, json_path, md_path)
    assert receipt["final_status"] != "RECOVERED_AND_VERIFIED"
    assert len(receipt["not_established"]) > 0

def test_generate_receipt_fully_verified_when_all_consistent(tmp_path, monkeypatch):
    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)

    git_sha = "e53f1d3576bbdf1f9adb17f012beba101f92376a"
    monkeypatch.setenv("CI_COMMIT_SHA", git_sha)

    # 1. Dossier
    with open(os.path.join(reports_dir, "incident_dossier.json"), "w") as f:
        json.dump({
            "incident_id": "inc-test",
            "commit_sha": git_sha,
            "project_path": "faultforge/checkout-service",
            "fault": {"profile_name": "latency_cascading_hang", "type": "latency", "profile_hash": "hash123"}
        }, f)

    # 2. Replay evaluation
    with open(os.path.join(reports_dir, "replay_evaluation.json"), "w") as f:
        json.dump({
            "evaluation_status": "RECOVERED_AND_VERIFIED",
            "verified": True,
            "gates": {
                "identical_profile_hash": {"baseline_hash": "hash123", "hardened_hash": "hash123"}
            },
            "raw_metrics": {"baseline_avg_ms": 3600.0, "hardened_avg_ms": 820.0}
        }, f)

    # 3. Duo run
    with open(os.path.join(reports_dir, "duo_run.json"), "w") as f:
        json.dump({"run_id": "duo-run-12345", "status": "CONFIRMED", "executed": True, "web_url": "https://gitlab.com/mr/1"}, f)

    # 4. 15 probe runs (5 base, 10 hard)
    with open(os.path.join(reports_dir, "fault_run_baseline.json"), "w") as f:
        json.dump({"per_request_results": [{"probe_index": i} for i in range(1, 6)]}, f)

    with open(os.path.join(reports_dir, "fault_run_hardened.json"), "w") as f:
        json.dump({"per_request_results": [{"probe_index": i} for i in range(1, 11)]}, f)

    # 5. Image digest & release
    with open(os.path.join(reports_dir, "image_digest.txt"), "w") as f:
        f.write("sha256:fedcba9876543210")

    with open(os.path.join(reports_dir, "release.json"), "w") as f:
        json.dump({"revision": "faultforge-checkout-00002", "status": "STAGED"}, f)

    json_path = str(tmp_path / "evidence_receipt.json")
    md_path = str(tmp_path / "EVIDENCE_RECEIPT.md")

    receipt = generate_evidence_receipt(reports_dir, json_path, md_path)
    assert receipt["final_status"] == "RECOVERED_AND_VERIFIED"
    assert receipt["not_established"] == []
    assert receipt["governance"]["promotion_gate"] == "BLOCKED_PENDING_APPROVAL"
    assert receipt["governance"]["requires_human_approval_to_promote"] is True
    assert receipt["duo_execution"]["executed"] is True

def test_generate_receipt_marks_not_established_when_duo_unexecuted(tmp_path, monkeypatch):
    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)

    git_sha = "e53f1d3576bbdf1f9adb17f012beba101f92376a"
    monkeypatch.setenv("CI_COMMIT_SHA", git_sha)

    with open(os.path.join(reports_dir, "incident_dossier.json"), "w") as f:
        json.dump({"incident_id": "inc-test", "commit_sha": git_sha, "fault": {"profile_name": "latency", "profile_hash": "hash123"}}, f)

    with open(os.path.join(reports_dir, "replay_evaluation.json"), "w") as f:
        json.dump({"evaluation_status": "RECOVERED_AND_VERIFIED", "verified": True, "gates": {"identical_profile_hash": {"baseline_hash": "hash123", "hardened_hash": "hash123"}}, "raw_metrics": {}}, f)

    with open(os.path.join(reports_dir, "duo_run.json"), "w") as f:
        json.dump({"run_id": "reference-only", "status": "NOT_EXECUTED_NO_CREDENTIALS", "executed": False}, f)

    with open(os.path.join(reports_dir, "fault_run_baseline.json"), "w") as f:
        json.dump({"per_request_results": [{"probe_index": i} for i in range(1, 6)]}, f)

    with open(os.path.join(reports_dir, "fault_run_hardened.json"), "w") as f:
        json.dump({"per_request_results": [{"probe_index": i} for i in range(1, 11)]}, f)

    with open(os.path.join(reports_dir, "image_digest.txt"), "w") as f:
        f.write("sha256:fedcba9876543210")

    with open(os.path.join(reports_dir, "release.json"), "w") as f:
        json.dump({"revision": "faultforge-checkout-00002"}, f)

    receipt = generate_evidence_receipt(reports_dir, str(tmp_path / "receipt.json"), str(tmp_path / "receipt.md"))
    assert receipt["duo_execution"]["executed"] is False
    assert any("GitLab Duo" in item for item in receipt["not_established"])
    assert receipt["final_status"] == "CONTAINED_NEEDS_REVIEW"

def test_generate_receipt_marks_not_established_when_release_skipped(tmp_path, monkeypatch):
    reports_dir = str(tmp_path / "reports")
    os.makedirs(reports_dir, exist_ok=True)

    git_sha = "e53f1d3576bbdf1f9adb17f012beba101f92376a"
    monkeypatch.setenv("CI_COMMIT_SHA", git_sha)

    with open(os.path.join(reports_dir, "incident_dossier.json"), "w") as f:
        json.dump({"incident_id": "inc-test", "commit_sha": git_sha, "fault": {"profile_name": "latency", "profile_hash": "hash123"}}, f)

    with open(os.path.join(reports_dir, "replay_evaluation.json"), "w") as f:
        json.dump({"evaluation_status": "RECOVERED_AND_VERIFIED", "verified": True, "gates": {"identical_profile_hash": {"baseline_hash": "hash123", "hardened_hash": "hash123"}}, "raw_metrics": {}}, f)

    with open(os.path.join(reports_dir, "duo_run.json"), "w") as f:
        json.dump({"run_id": "duo-run-123", "status": "CONFIRMED", "executed": True, "web_url": "https://gitlab.com/mr/1"}, f)

    with open(os.path.join(reports_dir, "fault_run_baseline.json"), "w") as f:
        json.dump({"per_request_results": [{"probe_index": i} for i in range(1, 6)]}, f)

    with open(os.path.join(reports_dir, "fault_run_hardened.json"), "w") as f:
        json.dump({"per_request_results": [{"probe_index": i} for i in range(1, 11)]}, f)

    with open(os.path.join(reports_dir, "image_digest.txt"), "w") as f:
        f.write("sha256:fedcba9876543210")

    with open(os.path.join(reports_dir, "release.json"), "w") as f:
        json.dump({"status": "SKIPPED_NO_GCP_CREDENTIALS", "reason": "Missing credentials"}, f)

    receipt = generate_evidence_receipt(reports_dir, str(tmp_path / "receipt.json"), str(tmp_path / "receipt.md"))
    assert receipt["deployment"]["cloud_run_revision"] is None
    assert any("Cloud Run" in item for item in receipt["not_established"])
    assert receipt["final_status"] == "CONTAINED_NEEDS_REVIEW"
