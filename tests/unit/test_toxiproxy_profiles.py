# SPDX-License-Identifier: MIT
"""
Tests for Toxiproxy chaos configurations and canonical hash integrity.
Validates multi-profile coverage (latency and connection reset) and deterministic hashing.
"""
import os
import json
import pytest
from scripts.run_fault import compute_profile_hash

def test_toxiproxy_latency_profile():
    profile_path = "chaos/profiles/latency_cascading_hang.json"
    assert os.path.exists(profile_path), f"Missing latency profile: {profile_path}"

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    assert profile["name"] == "latency_cascading_hang"
    assert profile["fault_type"] == "latency"
    assert profile["listen"] == "0.0.0.0:8082"
    assert profile["upstream"] == "127.0.0.1:8081"
    assert profile["attributes"]["latency"] == 3500
    assert profile["attributes"]["jitter"] == 250
    assert profile["sla_budget_ms"] == 1500

    calc_hash = compute_profile_hash(profile)
    assert calc_hash == "644a89784316", f"Canonical latency profile hash mismatch: got {calc_hash}"

def test_toxiproxy_connection_reset_profile():
    profile_path = "chaos/profiles/connection_reset.json"
    assert os.path.exists(profile_path), f"Missing connection reset profile: {profile_path}"

    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    assert profile["name"] == "connection_reset"
    assert profile["fault_type"] == "reset_peer"
    assert profile["listen"] == "0.0.0.0:8082"
    assert profile["upstream"] == "127.0.0.1:8081"
    assert profile["toxicity"] == 1.0

    calc_hash = compute_profile_hash(profile)
    assert len(calc_hash) == 12, "Profile hash must be 12-char SHA-256 slice"
    assert calc_hash == "0496439547a1"

def test_toxiproxy_profile_hash_determinism():
    """Validates that compute_profile_hash produces identical hashes regardless of key order."""
    profile_a = {
        "name": "test_profile",
        "fault_type": "latency",
        "listen": "0.0.0.0:8082",
        "upstream": "127.0.0.1:8081",
        "attributes": {"latency": 1000, "jitter": 100}
    }
    profile_b = {
        "upstream": "127.0.0.1:8081",
        "attributes": {"jitter": 100, "latency": 1000},
        "name": "test_profile",
        "listen": "0.0.0.0:8082",
        "fault_type": "latency"
    }
    assert compute_profile_hash(profile_a) == compute_profile_hash(profile_b)
