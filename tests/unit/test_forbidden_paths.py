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

def test_stdin_subprocess_added_test_and_modified_shipping_client_exits_zero():
    import sys, subprocess
    stdin_data = "A\ttests/unit/test_new_patch.py\nM\tapp/clients/shipping_client.py\n"
    res = subprocess.run(
        [sys.executable, "scripts/check_forbidden_paths.py", "--mode", "automated_remediation"],
        input=stdin_data,
        text=True,
        capture_output=True
    )
    assert res.returncode == 0, f"Expected exit 0, got {res.returncode}. Output:\n{res.stdout}\n{res.stderr}"

def test_stdin_subprocess_modified_existing_test_exits_one():
    import sys, subprocess
    stdin_data = "M\ttests/chaos/test_resilience.py\n"
    res = subprocess.run(
        [sys.executable, "scripts/check_forbidden_paths.py", "--mode", "automated_remediation"],
        input=stdin_data,
        text=True,
        capture_output=True
    )
    assert res.returncode == 1, f"Expected exit 1, got {res.returncode}. Output:\n{res.stdout}\n{res.stderr}"

def test_stdin_subprocess_deleted_existing_test_exits_one():
    import sys, subprocess
    stdin_data = "D\ttests/unit/test_shipping_client.py\n"
    res = subprocess.run(
        [sys.executable, "scripts/check_forbidden_paths.py", "--mode", "automated_remediation"],
        input=stdin_data,
        text=True,
        capture_output=True
    )
    assert res.returncode == 1, f"Expected exit 1, got {res.returncode}. Output:\n{res.stdout}\n{res.stderr}"

def test_stdin_subprocess_renamed_existing_test_exits_one():
    import sys, subprocess
    stdin_data = "R100\ttests/old_test.py\ttests/new_test.py\n"
    res = subprocess.run(
        [sys.executable, "scripts/check_forbidden_paths.py", "--mode", "automated_remediation"],
        input=stdin_data,
        text=True,
        capture_output=True
    )
    assert res.returncode == 1, f"Expected exit 1, got {res.returncode}. Output:\n{res.stdout}\n{res.stderr}"

def test_gitlab_ci_no_unquoted_changed_files_after_name_status():
    import re
    with open(".gitlab-ci.yml", "r", encoding="utf-8") as f:
        ci_content = f.read()

    # Find the MR pipeline safety check block
    mr_match = re.search(r'if\s+\[\s+-n\s+"\$CI_MERGE_REQUEST_DIFF_BASE_SHA"\s+\];\s*then(.*?)\belse\b', ci_content, re.DOTALL)
    assert mr_match, "MR safety check block not found in .gitlab-ci.yml"
    mr_block = mr_match.group(1)

    # Ensure --name-status is used
    assert "--name-status" in mr_block
    # Ensure unquoted $CHANGED_FILES is NOT passed via --files in this MR block
    assert "--files $CHANGED_FILES" not in mr_block, (
        "Found unquoted $CHANGED_FILES passed via --files after --name-status diff in .gitlab-ci.yml. "
        "Must pipe via stdin to preserve tab separation."
    )
    # Ensure piping via stdin is used instead
    assert "printf '%s\\n' \"$CHANGED_FILES\" | python scripts/check_forbidden_paths.py --mode automated_remediation" in mr_block
