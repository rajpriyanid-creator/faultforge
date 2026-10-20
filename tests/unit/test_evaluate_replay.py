# SPDX-License-Identifier: MIT
import os
import json
import pytest
from scripts.evaluate_replay import evaluate_replay, load_criteria

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
CRITERIA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "chaos", "criteria.json")

def test_load_criteria_fallback_when_file_missing(tmp_path):
    # Verify fallback dict does not crash on 'true' NameError
    missing_path = str(tmp_path / "does_not_exist.json")
    criteria = load_criteria(missing_path)
    assert criteria["fallback_counts_as_success"] is True
    assert criteria["require_fallback_marked_estimated"] is True
    assert criteria["latency_budget_ms"] == 1500

def test_evaluate_replay_all_gates_pass(tmp_path):
    base_file = os.path.join(FIXTURES_DIR, "base_pass.json")
    hard_file = os.path.join(FIXTURES_DIR, "hard_pass.json")
    out_file = str(tmp_path / "eval_pass.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(base_file, hard_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 0

    with open(out_file, "r") as f:
        data = json.load(f)
    assert data["evaluation_status"] == "RECOVERED_AND_VERIFIED"
    assert data["verified"] is True

def test_evaluate_replay_profile_hash_mismatch(tmp_path):
    base_file = os.path.join(FIXTURES_DIR, "base_pass.json")
    hard_file = os.path.join(FIXTURES_DIR, "hard_hash_mismatch.json")
    out_file = str(tmp_path / "eval_mismatch.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(base_file, hard_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 1

def test_evaluate_replay_weak_baseline_failure_ratio(tmp_path):
    base_file = os.path.join(FIXTURES_DIR, "base_weak_fail.json")
    hard_file = os.path.join(FIXTURES_DIR, "hard_pass.json")
    out_file = str(tmp_path / "eval_weak_base.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(base_file, hard_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 1

def test_evaluate_replay_candidate_imperfect_nine_of_ten(tmp_path):
    base_file = os.path.join(FIXTURES_DIR, "base_pass.json")
    hard_file = os.path.join(FIXTURES_DIR, "hard_imperfect.json")
    out_file = str(tmp_path / "eval_imperfect.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(base_file, hard_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 1

def test_evaluate_replay_missing_file(tmp_path):
    out_file = str(tmp_path / "eval_missing.json")
    with pytest.raises(SystemExit) as exc:
        evaluate_replay("nonexistent_base.json", "nonexistent_hard.json", out_file, CRITERIA_PATH)
    assert exc.value.code == 1

def test_evaluate_replay_malformed_json(tmp_path):
    bad_json = tmp_path / "bad.json"
    bad_json.write_text("NOT_VALID_JSON{{{")
    hard_file = os.path.join(FIXTURES_DIR, "hard_pass.json")
    out_file = str(tmp_path / "eval_bad_json.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(str(bad_json), hard_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 1

def test_evaluate_replay_same_revision_fails(tmp_path):
    base_file = os.path.join(FIXTURES_DIR, "base_pass.json")
    # Write a copy with identical git_sha as base_pass
    with open(base_file, "r") as f:
        base_data = json.load(f)
    hard_file = os.path.join(FIXTURES_DIR, "hard_pass.json")
    with open(hard_file, "r") as f:
        hard_data = json.load(f)
    hard_data["git_sha"] = base_data["git_sha"] # Identical revision

    same_rev_file = str(tmp_path / "same_rev.json")
    with open(same_rev_file, "w") as f:
        json.dump(hard_data, f)
    out_file = str(tmp_path / "eval_same_rev.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(base_file, same_rev_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 1

def test_evaluate_replay_missing_fallback_flag(tmp_path):
    base_file = os.path.join(FIXTURES_DIR, "base_pass.json")
    hard_file = os.path.join(FIXTURES_DIR, "hard_pass.json")
    with open(hard_file, "r") as f:
        hard_data = json.load(f)
    # Strip is_estimate flag
    for pr in hard_data["per_request_results"]:
        pr["is_estimate"] = False

    no_est_file = str(tmp_path / "no_estimate.json")
    with open(no_est_file, "w") as f:
        json.dump(hard_data, f)
    out_file = str(tmp_path / "eval_no_est.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(base_file, no_est_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 1

def test_evaluate_replay_fast_fail_not_in_path(tmp_path):
    base_file = os.path.join(FIXTURES_DIR, "base_pass.json")
    hard_file = os.path.join(FIXTURES_DIR, "hard_not_in_path.json")
    out_file = str(tmp_path / "eval_fast_fail.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(base_file, hard_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 1

def test_evaluate_replay_non_toxiproxy_engine_fails(tmp_path):
    base_file = os.path.join(FIXTURES_DIR, "base_pass.json")
    hard_file = os.path.join(FIXTURES_DIR, "hard_pass.json")
    with open(hard_file, "r") as f:
        hard_data = json.load(f)
    hard_data["proxy_engine"] = "standalone"

    standalone_file = str(tmp_path / "hard_standalone.json")
    with open(standalone_file, "w") as f:
        json.dump(hard_data, f)
    out_file = str(tmp_path / "eval_standalone.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(base_file, standalone_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 1

def test_evaluate_replay_two_phase_success(tmp_path):
    base_file = os.path.join(FIXTURES_DIR, "base_pass.json")
    with open(os.path.join(FIXTURES_DIR, "hard_pass.json"), "r") as f:
        hard_data = json.load(f)

    hard_data["phase_a_timeout_only"] = {
        "total_probes": 10,
        "successful_probes": 10,
        "failed_probes": 0,
        "fallback_count": 10,
        "sla_breaches": 0,
        "latencies_ms": [812.0] * 10,
        "avg_ms": 812.0,
        "p95_ms": 815.0
    }
    hard_data["phase_b_breaker_open"] = {
        "total_probes": 10,
        "successful_probes": 10,
        "failed_probes": 0,
        "fallback_count": 10,
        "short_circuited_count": 7,
        "sla_breaches": 0,
        "latencies_ms": [812.0, 814.0, 810.0] + [2.1] * 7,
        "avg_ms": 245.0,
        "p95_ms": 814.0
    }

    two_phase_file = str(tmp_path / "hard_two_phase.json")
    with open(two_phase_file, "w") as f:
        json.dump(hard_data, f)
    out_file = str(tmp_path / "eval_two_phase.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(base_file, two_phase_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 0

    with open(out_file, "r") as f:
        eval_res = json.load(f)
    assert eval_res["gates"]["candidate_timeout_only"]["passed"] is True
    assert eval_res["gates"]["candidate_breaker_short_circuit"]["passed"] is True
    assert "latency_reduction" in eval_res
    assert "p95_basis" in eval_res["latency_reduction"]
    assert "mean_basis" in eval_res["latency_reduction"]
