# SPDX-License-Identifier: MIT
import os
import json
import pytest
from scripts.run_fault import compute_profile_hash

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
