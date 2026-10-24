# SPDX-License-Identifier: MIT
import os
import json
import pytest
from scripts.verify_tree_parity import verify_tree_parity, get_tree_sha
from scripts.generate_receipt import generate_evidence_receipt

def test_get_tree_sha_from_valid_file(tmp_path):
    f = tmp_path / "tree.txt"
    valid_sha = "a" * 40
    f.write_text(valid_sha + "\n", encoding="utf-8")
    assert get_tree_sha(str(f)) == valid_sha

def test_get_tree_sha_from_invalid_file(tmp_path):
    f = tmp_path / "bad_tree.txt"
    f.write_text("not-a-40-char-sha", encoding="utf-8")
    # File is invalid so it won't return it as a valid sha
    assert get_tree_sha(str(f)) != "not-a-40-char-sha"

def test_verify_tree_parity_matching(tmp_path):
    replay_file = tmp_path / "replay_tree.txt"
    deployed_file = tmp_path / "deployed_tree.txt"
    sha = "b" * 40
    replay_file.write_text(sha + "\n", encoding="utf-8")
    deployed_file.write_text(sha + "\n", encoding="utf-8")

    result = verify_tree_parity(
        replay_tree_path=str(replay_file),
        deployed_tree_path=str(deployed_file),
        fail_on_mismatch=True
    )
    assert result is True

def test_verify_tree_parity_mismatch(tmp_path):
    replay_file = tmp_path / "replay_tree.txt"
    deployed_file = tmp_path / "deployed_tree.txt"
    replay_file.write_text("c" * 40 + "\n", encoding="utf-8")
    deployed_file.write_text("d" * 40 + "\n", encoding="utf-8")

    with pytest.raises(SystemExit) as excinfo:
        verify_tree_parity(
            replay_tree_path=str(replay_file),
            deployed_tree_path=str(deployed_file),
            fail_on_mismatch=True
        )
    assert excinfo.value.code == 1

def test_verify_tree_parity_missing_fails(tmp_path):
    replay_file = tmp_path / "nonexistent_replay.txt"
    deployed_file = tmp_path / "nonexistent_deployed.txt"

    # In a dir without git repo, missing files exit 1
    with pytest.raises(SystemExit) as excinfo:
        verify_tree_parity(
            replay_tree_path=str(replay_file),
            deployed_tree_path=str(deployed_file),
            fail_on_mismatch=True
        )
    assert excinfo.value.code == 1

def test_receipt_top_level_tree_parity_fields(tmp_path):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    sha = "e" * 40
    (reports_dir / "replay_tree_sha.txt").write_text(sha + "\n", encoding="utf-8")
    (reports_dir / "deployed_tree_sha.txt").write_text(sha + "\n", encoding="utf-8")

    receipt_json = str(reports_dir / "evidence_receipt.json")
    receipt_md = str(reports_dir / "EVIDENCE_RECEIPT.md")

    receipt = generate_evidence_receipt(
        reports_dir=str(reports_dir),
        receipt_json_path=receipt_json,
        receipt_md_path=receipt_md
    )

    # Verify top-level fields
    assert "replay_tree_sha" in receipt
    assert "deployed_tree_sha" in receipt
    assert "app_tree_matches_deployed" in receipt
    assert receipt["replay_tree_sha"] == sha
    assert receipt["deployed_tree_sha"] == sha
    assert receipt["app_tree_matches_deployed"] is True

    # Verify EVIDENCE_RECEIPT.md contains the tree lines
    with open(receipt_md, "r", encoding="utf-8") as f:
        md_text = f.read()
    assert sha in md_text
    assert "**App Tree Parity Verified:** `True`" in md_text
