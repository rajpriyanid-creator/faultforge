import os
import pytest
from scripts.classify_risk import classify_diff, load_policy

POLICY = {
    "high_risk_patterns": ["auth", "payment", "schema", "migration", "secret", "iam", "infra/cloudrun"],
    "max_low_risk_diff_lines": 150,
    "medium_risk_patterns": ["requirements.txt", "Dockerfile", "docker-compose", "flows/"],
    "allowed_low_risk_prefixes": ["app/clients/", "app/resilience/", "tests/"],
    "require_regression_test_in_tests": True
}

def test_classify_diff_low_risk():
    files = ["app/clients/shipping_client.py", "tests/chaos/test_resilience.py"]
    lines = 45
    result = classify_diff(files, lines, POLICY)
    assert result["tier"] == "LOW"
    assert result["requires_human_approval"] is False

def test_classify_diff_medium_risk_dependency():
    files = ["requirements.txt", "app/clients/shipping_client.py", "tests/chaos/test_resilience.py"]
    lines = 30
    result = classify_diff(files, lines, POLICY)
    assert result["tier"] == "MEDIUM"
    assert result["requires_human_approval"] is True

def test_classify_diff_medium_risk_outside_prefix():
    files = ["app/main.py", "tests/chaos/test_resilience.py"]
    lines = 25
    result = classify_diff(files, lines, POLICY)
    assert result["tier"] == "MEDIUM"

def test_classify_diff_high_risk_pattern():
    files = ["app/clients/shipping_client.py", "infra/cloudrun/service.yaml"]
    lines = 20
    result = classify_diff(files, lines, POLICY)
    assert result["tier"] == "HIGH"
    assert result["requires_human_approval"] is True

def test_classify_diff_high_risk_diff_size():
    files = ["app/clients/shipping_client.py", "tests/chaos/test_resilience.py"]
    lines = 300 # Exceeds 150 lines limit
    result = classify_diff(files, lines, POLICY)
    assert result["tier"] == "HIGH"
    assert result["requires_human_approval"] is True
