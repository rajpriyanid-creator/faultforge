# SPDX-License-Identifier: MIT
import pytest
from scripts.autonomy_router import route_change

def test_route_low_risk_auto_apply():
    """Low risk changes (timeout, fallback, retry in allowed paths) route to auto-apply."""
    files = ["app/clients/shipping_client.py", "tests/chaos/test_resilience.py"]
    res = route_change(files, lines_changed=30)
    assert res["tier"] == "LOW"
    assert res["route"] == "auto-apply"
    assert res["requires_approval_at_each_step"] is False

def test_route_medium_risk_supervised():
    """Medium risk changes (dependency bumps, Dockerfile) route to supervised."""
    files = ["requirements.txt"]
    res = route_change(files, lines_changed=5)
    assert res["tier"] == "MEDIUM"
    assert res["route"] == "supervised"
    assert res["requires_approval_at_each_step"] is False

def test_route_medium_risk_outside_prefix():
    """Changes outside allowed low-risk paths route to supervised."""
    files = ["app/main.py"]
    res = route_change(files, lines_changed=10)
    assert res["tier"] == "MEDIUM"
    assert res["route"] == "supervised"

def test_route_high_risk_assisted_auth():
    """High risk changes (auth, payment, schema, secret) route to assisted."""
    files = ["app/auth/tokens.py"]
    res = route_change(files, lines_changed=10)
    assert res["tier"] == "HIGH"
    assert res["route"] == "assisted"
    assert res["requires_approval_at_each_step"] is True

def test_route_high_risk_diff_size():
    """Diffs exceeding the line limit route to assisted."""
    files = ["app/clients/shipping_client.py"]
    res = route_change(files, lines_changed=250)
    assert res["tier"] == "HIGH"
    assert res["route"] == "assisted"
    assert res["requires_approval_at_each_step"] is True
