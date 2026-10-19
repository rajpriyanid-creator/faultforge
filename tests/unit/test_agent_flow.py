# SPDX-License-Identifier: MIT
import os
import yaml
import pytest

def test_flow_yaml_schema_and_components():
    flow_path = "flows/faultforge-flow.yaml"
    assert os.path.exists(flow_path), f"Flow specification not found: {flow_path}"

    with open(flow_path, "r", encoding="utf-8") as f:
        flow = yaml.safe_load(f)

    # 1. Validate top-level schema
    assert flow.get("version") == "v1"
    assert flow.get("environment") == "ambient"
    assert flow.get("coding_environment") == "full"

    # 2. Validate Prompts
    prompts = flow.get("prompts", {})
    assert "diagnose_prompt" in prompts
    assert "heal_prompt" in prompts
    assert "hardener_prompt" in prompts

    # 3. Validate Components
    components = {c["name"]: c for c in flow.get("components", [])}
    assert "diagnostician" in components
    assert "resilience_healer" in components
    assert "chaos_hardener" in components

    for comp_name, comp in components.items():
        assert comp.get("type") == "AgentComponent"
        assert len(comp.get("toolset", [])) > 0

    # 4. Validate Routers & Entry Point
    assert flow.get("flow", {}).get("entry_point") == "diagnostician"
    routers = flow.get("routers", [])
    assert len(routers) >= 3

    # Ensure no hardcoded model IDs exist in flow YAML
    with open(flow_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "claude-3-5" not in content
    assert "gpt-4" not in content
