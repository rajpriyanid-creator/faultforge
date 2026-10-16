import os
import pytest
from scripts.evaluate_replay import evaluate_replay

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")
CRITERIA_PATH = os.path.join(os.path.dirname(__file__), "..", "..", "chaos", "criteria.json")

def test_evaluate_replay_all_gates_pass(tmp_path):
    base_file = os.path.join(FIXTURES_DIR, "base_pass.json")
    hard_file = os.path.join(FIXTURES_DIR, "hard_pass.json")
    out_file = str(tmp_path / "eval_pass.json")

    with pytest.raises(SystemExit) as exc:
        evaluate_replay(base_file, hard_file, out_file, CRITERIA_PATH)
    assert exc.value.code == 0

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
