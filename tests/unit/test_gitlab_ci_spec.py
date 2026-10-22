# SPDX-License-Identifier: MIT
"""
Unit tests validating .gitlab-ci.yml specification and governance contracts.
Verifies git fetch preceding git diff in replay verification, pinned release-cli,
and valid CODEOWNERS configurations.
"""
import os
import yaml
import pytest

def test_replay_verification_fetches_main_before_diff():
    ci_path = ".gitlab-ci.yml"
    assert os.path.exists(ci_path), f"Missing CI file at {ci_path}"

    with open(ci_path, "r", encoding="utf-8") as f:
        content = f.read()
        ci_yaml = yaml.safe_load(content)

    replay_job = ci_yaml.get("verify:exact_fault_replay_proof")
    assert replay_job is not None, "verify:exact_fault_replay_proof job must exist"

    # 1. Assert GIT_DEPTH is "0" to support unshallow history
    variables = replay_job.get("variables", {})
    assert str(variables.get("GIT_DEPTH")) == "0", "GIT_DEPTH must be set to '0' for replay verification"

    # 2. Extract script block and assert git fetch origin main precedes git diff
    script = "\n".join(replay_job.get("script", []))
    fetch_main_pos = script.find("git fetch origin main")
    diff_pos = script.find("git diff")

    assert fetch_main_pos != -1, "Replay job script must execute 'git fetch origin main'"
    assert diff_pos != -1, "Replay job script must execute 'git diff'"
    assert fetch_main_pos < diff_pos, "git fetch origin main must precede git diff in replay job script"

def test_release_job_pinned_and_asset_links():
    ci_path = ".gitlab-ci.yml"
    with open(ci_path, "r", encoding="utf-8") as f:
        ci_yaml = yaml.safe_load(f)

    rel_job = ci_yaml.get("release:official_gitlab_release")
    assert rel_job is not None, "release:official_gitlab_release must exist"
    assert ":latest" not in rel_job.get("image", ""), "release-cli image must be pinned to specific version tag"

    links = rel_job.get("release", {}).get("assets", {}).get("links", [])
    digest_link = next((l for l in links if "Digest" in l.get("name", "")), None)
    assert digest_link is not None, "Container Image Digest asset link must exist"
    assert digest_link.get("link_type") == "other", "Digest asset link_type must be 'other'"

def test_codeowners_configured_with_valid_username():
    codeowners_path = ".gitlab/CODEOWNERS"
    assert os.path.exists(codeowners_path), f"Missing {codeowners_path}"

    with open(codeowners_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    assert any("@rajpriyanid" in line for line in lines), "CODEOWNERS must assign ownership to @rajpriyanid"
    assert not any("@rajpr9698" in line for line in lines), "CODEOWNERS must not contain stale @rajpr9698 handle"
