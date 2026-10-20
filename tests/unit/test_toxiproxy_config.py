# SPDX-License-Identifier: MIT
import os
import json
import pytest
from scripts.run_fault import compute_profile_hash, verify_proxy_in_path, get_real_git_sha
from chaos.toxiproxy_helper import ChaosEngine

def test_toxiproxy_profile_canonical_hash():
    profile_path = "chaos/profiles/latency_cascading_hang.json"
    assert os.path.exists(profile_path), f"Fault profile not found: {profile_path}"

    with open(profile_path, "r", encoding="utf-8") as f:
        profile_data = json.load(f)

    # Validate essential chaos parameters
    assert profile_data.get("name") == "latency_cascading_hang"
    assert profile_data.get("fault_type") == "latency"
    attrs = profile_data.get("attributes", {})
    assert attrs.get("latency") == 3500
    assert attrs.get("jitter") == 250

    # Validate canonical profile hash calculation matches ground truth
    calculated_hash = compute_profile_hash(profile_data)
    assert calculated_hash == "644a89784316", f"Canonical hash mismatch: got {calculated_hash}"

def test_verify_proxy_in_path_fails_when_connection_refused(monkeypatch):
    class MockClient:
        api_url = "http://127.0.0.1:8474"
    class MockEngine:
        use_toxi = True
        toxi_client = MockClient()

    # If Toxiproxy API returns disabled or proxy connection is refused
    profile = {
        "proxy_name": "nonexistent_proxy",
        "fault_type": "latency",
        "attributes": {"latency": 3500}
    }
    # Unreachable port ensures connection refused
    passed = verify_proxy_in_path(MockEngine(), profile, proxy_listen_url="http://127.0.0.1:59999")
    assert passed is False

def test_get_real_git_sha_fallback_unknown_no_git(monkeypatch):
    monkeypatch.delenv("CI_COMMIT_SHA", raising=False)
    # Mock subprocess to fail
    import subprocess
    def mock_subprocess(*args, **kwargs):
        raise FileNotFoundError("git not found")
    monkeypatch.setattr(subprocess, "check_output", mock_subprocess)

    sha, verified = get_real_git_sha()
    assert sha == "UNKNOWN_NO_GIT"
    assert verified is False

def test_get_real_git_sha_explicit():
    test_sha = "c" * 40
    sha, verified = get_real_git_sha(explicit_sha=test_sha)
    assert sha == test_sha
    assert verified is True
