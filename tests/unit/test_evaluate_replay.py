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
