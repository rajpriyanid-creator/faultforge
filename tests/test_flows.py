# SPDX-License-Identifier: MIT
"""
Tests for GitLab Duo Agent Platform Custom Flow specification.
Validates flow topology, component tools, prompts, and schema contracts.
"""
import os
import yaml
import pytest

def test_flow_schema_and_supervised_contract():
    flow_path = "flows/faultforge-flow.yaml"
    assert os.path.exists(flow_path), f"Missing flow specification at {flow_path}"

    with open(flow_path, "r", encoding="utf-8") as f:
        flow = yaml.safe_load(f)

    # 1. Top-level schema contract
    assert flow.get("version") == "v1"
    assert flow.get("environment") == "ambient"
    assert flow.get("coding_environment") == "full"

    # 2. Prompts definitions & constraints
    prompts = flow.get("prompts", {})
    assert "diagnose_prompt" in prompts
    assert "heal_prompt" in prompts
    assert "hardener_prompt" in prompts

    # Assert bounded timeouts and fallback flags in healer prompt
    heal_system = prompts["heal_prompt"]["system"]
    assert "0.8s" in heal_system, "Healer prompt must enforce bounded 0.8s timeout"
    assert "is_fallback=True" in heal_system, "Healer prompt must enforce is_fallback flag"
    assert "is_estimate=True" in heal_system, "Healer prompt must enforce is_estimate flag"

    # Assert regression assertions and MR review link in hardener prompt
    hardener_system = prompts["hardener_prompt"]["system"]
    assert "tests/chaos/test_resilience.py" in hardener_system
    assert "Merge Request" in hardener_system

    # 3. Component topology & toolsets
    components = {c["name"]: c for c in flow.get("components", [])}
    assert set(components.keys()) == {"diagnostician", "resilience_healer", "chaos_hardener"}

    for name, comp in components.items():
        assert comp.get("type") == "AgentComponent"
        toolset = comp.get("toolset", [])
        assert "read_file" in toolset
        assert "list_dir" in toolset
        assert "run_command" in toolset

    # 4. Routers & Linear Execution
    assert flow.get("flow", {}).get("entry_point") == "diagnostician"
    routers = flow.get("routers", [])
    expected_hops = [
        {"from": "diagnostician", "to": "resilience_healer"},
        {"from": "resilience_healer", "to": "chaos_hardener"},
        {"from": "chaos_hardener", "to": "end"}
    ]
    for hop in expected_hops:
        assert hop in routers, f"Missing router transition: {hop}"

    # 5. Zero hardcoded model anti-pattern
    with open(flow_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "claude-3-5" not in content
    assert "gpt-4" not in content
