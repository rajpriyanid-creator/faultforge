# SPDX-License-Identifier: MIT
import pytest
from scripts.check_forbidden_paths import validate_changed_files, check_file

def test_check_file_allowed():
    assert len(check_file("app/clients/shipping_client.py")) == 0
    assert len(check_file("app/resilience/policy.py")) == 0
    assert len(check_file("tests/chaos/test_resilience.py")) == 0

def test_check_file_forbidden_auth():
    violations = check_file("app/auth/login.py")
    assert len(violations) > 0
    assert "Authentication" in violations[0][1]

def test_check_file_forbidden_payment():
    violations = check_file("app/payments/billing.py")
    assert len(violations) > 0
    assert "Payment" in violations[0][1]

def test_check_file_forbidden_db_schema():
    violations = check_file("app/db/schema.sql")
    assert len(violations) > 0
    assert "Database" in violations[0][1]

def test_check_file_forbidden_ci_and_flows():
    assert len(check_file(".gitlab-ci.yml")) > 0
    assert len(check_file("flows/faultforge-flow.yaml")) > 0
    assert len(check_file(".gitlab/CODEOWNERS")) > 0

def test_validate_changed_files_passes_on_valid_scope():
    files = [
        "app/clients/shipping_client.py",
        "app/resilience/policy.py",
        "A tests/unit/test_new_resilience.py"
    ]
    assert validate_changed_files(files) is True

def test_automated_remediation_allows_adding_tests():
    files = [
        "app/clients/shipping_client.py",
        "A tests/unit/test_duo_resilience.py"
    ]
    assert validate_changed_files(files) is True

def test_automated_remediation_forbids_modifying_existing_tests():
    files = [
        "app/clients/shipping_client.py",
        "M tests/chaos/test_resilience.py"
    ]
    assert validate_changed_files(files) is False

def test_automated_remediation_forbids_deleting_existing_tests():
    files = [
        "app/clients/shipping_client.py",
        "D tests/unit/test_shipping_client.py"
    ]
    assert validate_changed_files(files) is False

def test_automated_remediation_mode_flag_forbids_modifying_tracked_tests():
    # In automated remediation mode, existing tracked test files without status prefix are recognized as modifications
    assert validate_changed_files(["tests/chaos/test_resilience.py"], mode="automated_remediation") is False

def test_automated_remediation_mode_flag_allows_new_untracked_tests():
    # In automated remediation mode, newly added test files are permitted
    assert validate_changed_files(["tests/unit/test_completely_new_proof.py"], mode="automated_remediation") is True

def test_validate_changed_files_fails_on_forbidden():
    files = [
        "app/clients/shipping_client.py",
        ".gitlab-ci.yml"
    ]
    assert validate_changed_files(files) is False

def test_validate_changed_files_fails_on_out_of_scope():
    files = [
        "app/clients/shipping_client.py",
        "infra/cloudrun/service.yaml"
    ]
    assert validate_changed_files(files) is False

def test_validate_changed_files_passes_on_documented_orchestration():
    files = [
        "app/main.py",
        "app/dashboard.html",
        "app/clients/orbit_client.py"
    ]
    assert validate_changed_files(files) is True

def test_validate_changed_files_fails_on_unauthorized_app_file():
    files = [
        "app/clients/shipping_client.py",
        "app/unauthorized_service.py"
    ]
    assert validate_changed_files(files) is False
