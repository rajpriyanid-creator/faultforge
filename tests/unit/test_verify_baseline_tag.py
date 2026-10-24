# SPDX-License-Identifier: MIT
import os
import subprocess
import pytest
from scripts.verify_baseline_tag import verify_baseline_tag, PINNED_TAG_OBJECT_SHA, PINNED_TAG_COMMIT_SHA

def test_verify_baseline_tag_passes_in_repo():
    if not os.path.exists(".git"):
        pytest.skip("Skipping git tag object verification outside git repo (.git absent in clean git archive export)")
    assert verify_baseline_tag() is True

def test_verify_baseline_tag_fails_on_wrong_commit(monkeypatch):
    if not os.path.exists(".git"):
        pytest.skip("Skipping git tag object verification outside git repo (.git absent in clean git archive export)")
    import scripts.verify_baseline_tag as vbt
    monkeypatch.setattr(vbt, "PINNED_TAG_COMMIT_SHA", "0" * 40)
    assert vbt.verify_baseline_tag() is False

def test_verify_baseline_tag_fails_on_wrong_tag_object(monkeypatch):
    if not os.path.exists(".git"):
        pytest.skip("Skipping git tag object verification outside git repo (.git absent in clean git archive export)")
    import scripts.verify_baseline_tag as vbt
    monkeypatch.setattr(vbt, "PINNED_TAG_OBJECT_SHA", "0" * 40)
    assert vbt.verify_baseline_tag() is False
