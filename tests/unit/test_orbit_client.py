# SPDX-License-Identifier: MIT
import os
import pytest
from app.clients.orbit_client import OrbitClient

def test_orbit_client_fallback_mode():
    """When ENABLE_ORBIT_MCP is off or not configured, client uses fallback_ast_git."""
    client = OrbitClient()
    result = client.query_graph(target_component="app/clients/shipping_client.py")
    assert result["resolution_path"] == "fallback_ast_git"
    assert result["orbit_mcp_enabled"] is False
    assert result["target_component"] == "app/clients/shipping_client.py"
    assert any(n["id"] == "checkout-service" for n in result["nodes"])
    assert any(n["id"] == "shipping-service" for n in result["nodes"])

def test_orbit_client_mcp_mode(monkeypatch):
    """When ENABLE_ORBIT_MCP is enabled and server URL is set, client takes orbit_mcp route."""
    monkeypatch.setenv("ENABLE_ORBIT_MCP", "true")
    monkeypatch.setenv("ORBIT_MCP_SERVER_URL", "http://orbit-mcp.internal:9000")
    client = OrbitClient()
    result = client.query_graph(target_component="app/clients/shipping_client.py")
    assert result["resolution_path"] == "orbit_mcp"
    assert result["orbit_version"] == "v1-alpha"
    assert len(result["nodes"]) == 3
