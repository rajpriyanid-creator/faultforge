# SPDX-License-Identifier: MIT
import os
import json
import pytest
from scripts.check_readme_claims import parse_readme_stages_table, validate_claims

SAMPLE_README = """
## 4. The 9 Covered Lifecycle Stages

| Stage | FaultForge Action | Output Artifact / Evidence | Status |
|---|---|---|---|
| **`plan`** | Incident Tracking | `reports/issue.json` | ✅ SUCCESS |
| **`create`** | Duo Remediation | `reports/diagnosis_report.json` | ⚠️ PARTIAL (Duo flow: not executed) |
| **`configure`** | Chaos Wiring | `reports/fault_config.json` | ✅ SUCCESS |
| **`verify`** | Exact Replay | `reports/fault_run_baseline.json` | ✅ SUCCESS |
| **`secure`** | Secret Detection | `reports/bandit_security_report.json` | ✅ SUCCESS |
| **`package`** | Docker Build | `reports/image_digest.txt` | ✅ SUCCESS |
| **`release`** | Cloud Run Deploy | `reports/release.json` | ⚠️ SKIPPED (no GCP credentials) |
| **`monitor`** | Telemetry Probes | `reports/monitor.json` | ✅ SUCCESS |
| **`govern`** | Supervised Gate | `reports/evidence_receipt.json` | ✅ SUCCESS |

## 5. Quickstart
"""

def test_parse_readme_stages_table(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(SAMPLE_README, encoding="utf-8")
    claims = parse_readme_stages_table(str(readme))
    assert len(claims) == 9
    assert claims["plan"] == "✅ SUCCESS"
    assert claims["release"] == "⚠️ SKIPPED (no GCP credentials)"
    assert "Duo flow: not executed" in claims["create"]

def test_validate_claims_fails_when_no_ci_evidence(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(SAMPLE_README, encoding="utf-8")
    assert validate_claims(
        readme_path=str(readme),
        ledger_path=str(tmp_path / "missing_ledger.json"),
        receipt_path=str(tmp_path / "missing_receipt.json"),
        strict_all_stages=True
    ) is False

def test_validate_claims_passes_when_consistent(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(SAMPLE_README, encoding="utf-8")

    ledger_file = tmp_path / "stage_ledger.json"
    receipt_file = tmp_path / "evidence_receipt.json"

    stages = {}
    for stg in ["plan", "create", "configure", "verify", "secure", "package", "monitor", "govern"]:
        stages[stg] = {"status": "SUCCESS", "duo_executed": False}
    stages["release"] = {"status": "SKIPPED"}

    ledger_file.write_text(json.dumps({"stages": stages}), encoding="utf-8")
    receipt_file.write_text(json.dumps({"final_status": "CONTAINED_NEEDS_REVIEW", "not_established": ["GitLab Duo flow execution"]}), encoding="utf-8")

    assert validate_claims(
        readme_path=str(readme),
        ledger_path=str(ledger_file),
        receipt_path=str(receipt_file),
        strict_all_stages=True
    ) is True

def test_audit_ci_claims_fails_on_nonexistent_job(tmp_path):
    from scripts.check_readme_claims import audit_ci_claims_and_citations
    readme = tmp_path / "README.md"
    readme.write_text("Enforced by nonexistent:fake_job in stage verification.\n", encoding="utf-8")
    ci_yml = tmp_path / ".gitlab-ci.yml"
    ci_yml.write_text("verify:job:\n  script: echo 1\n", encoding="utf-8")

    passed, discrepancies = audit_ci_claims_and_citations(
        readme_path=str(readme),
        gitlab_ci_path=str(ci_yml),
        docs_dir=str(tmp_path / "nonexistent_docs")
    )
    assert passed is False
    assert any("does not exist in .gitlab-ci.yml" in d for d in discrepancies)

def test_audit_ci_claims_fails_on_job_not_executing_script(tmp_path):
    from scripts.check_readme_claims import audit_ci_claims_and_citations
    readme = tmp_path / "README.md"
    readme.write_text("Stage verify:job enforces scripts/uncalled_guard.py.\n", encoding="utf-8")
    ci_yml = tmp_path / ".gitlab-ci.yml"
    ci_yml.write_text("verify:job:\n  script: echo 1\n", encoding="utf-8")

    passed, discrepancies = audit_ci_claims_and_citations(
        readme_path=str(readme),
        gitlab_ci_path=str(ci_yml),
        docs_dir=str(tmp_path / "nonexistent_docs")
    )
    assert passed is False
    assert any("not called in verify:job's CI script" in d for d in discrepancies)

def test_audit_ci_claims_fails_on_stale_pipeline_id(tmp_path):
    from scripts.check_readme_claims import audit_ci_claims_and_citations
    readme = tmp_path / "README.md"
    readme.write_text("Verified in Pipeline #2982183259.\n", encoding="utf-8")
    ci_yml = tmp_path / ".gitlab-ci.yml"
    ci_yml.write_text("job:1:\n  script: echo 1\n", encoding="utf-8")

    passed, discrepancies = audit_ci_claims_and_citations(
        readme_path=str(readme),
        gitlab_ci_path=str(ci_yml),
        docs_dir=str(tmp_path / "nonexistent_docs")
    )
    assert passed is False
    assert any("stale pipeline ID 2982183259" in d for d in discrepancies)

def test_audit_ci_claims_fails_on_stale_issue_number(tmp_path):
    from scripts.check_readme_claims import audit_ci_claims_and_citations
    readme = tmp_path / "README.md"
    readme.write_text("Tracks Incident Work Item #50 in CI.\n", encoding="utf-8")
    ci_yml = tmp_path / ".gitlab-ci.yml"
    ci_yml.write_text("job:1:\n  script: echo 1\n", encoding="utf-8")

    passed, discrepancies = audit_ci_claims_and_citations(
        readme_path=str(readme),
        gitlab_ci_path=str(ci_yml),
        docs_dir=str(tmp_path / "nonexistent_docs")
    )
    assert passed is False
    assert any("stale incident Work Item #50" in d for d in discrepancies)

def test_audit_ci_claims_fails_on_stale_cloud_run_revision(tmp_path):
    from scripts.check_readme_claims import audit_ci_claims_and_citations
    readme = tmp_path / "README.md"
    readme.write_text("Deployed revision faultforge-checkout-00030-dit to staging.\n", encoding="utf-8")
    ci_yml = tmp_path / ".gitlab-ci.yml"
    ci_yml.write_text("job:1:\n  script: echo 1\n", encoding="utf-8")

    passed, discrepancies = audit_ci_claims_and_citations(
        readme_path=str(readme),
        gitlab_ci_path=str(ci_yml),
        docs_dir=str(tmp_path / "nonexistent_docs")
    )
    assert passed is False
    assert any("stale Cloud Run revision 'faultforge-checkout-00030-dit'" in d for d in discrepancies)

def test_validate_claims_fails_when_inflated_claim(tmp_path):
    # README claims bare SUCCESS for release, but ledger says SKIPPED
    inflated_readme = SAMPLE_README.replace("⚠️ SKIPPED (no GCP credentials)", "✅ SUCCESS")
    readme = tmp_path / "README.md"
    readme.write_text(inflated_readme, encoding="utf-8")

    ledger_file = tmp_path / "stage_ledger.json"
    receipt_file = tmp_path / "evidence_receipt.json"

    stages = {}
    for stg in ["plan", "create", "configure", "verify", "secure", "package", "monitor", "govern"]:
        stages[stg] = {"status": "SUCCESS", "duo_executed": False}
    stages["release"] = {"status": "SKIPPED"}

    ledger_file.write_text(json.dumps({"stages": stages}), encoding="utf-8")
    receipt_file.write_text(json.dumps({"final_status": "CONTAINED_NEEDS_REVIEW"}), encoding="utf-8")

    assert validate_claims(
        readme_path=str(readme),
        ledger_path=str(ledger_file),
        receipt_path=str(receipt_file),
        strict_all_stages=True
    ) is False

def test_validate_claims_fails_when_hedged_skipped_claim(tmp_path):
    # README hedges with "SUCCESS or SKIPPED" when ledger is strictly SKIPPED
    hedged_readme = SAMPLE_README.replace("⚠️ SKIPPED (no GCP credentials)", "✅ SUCCESS or SKIPPED")
    readme = tmp_path / "README.md"
    readme.write_text(hedged_readme, encoding="utf-8")

    ledger_file = tmp_path / "stage_ledger.json"
    receipt_file = tmp_path / "evidence_receipt.json"

    stages = {}
    for stg in ["plan", "create", "configure", "verify", "secure", "package", "monitor", "govern"]:
        stages[stg] = {"status": "SUCCESS", "duo_executed": False}
    stages["release"] = {"status": "SKIPPED"}

    ledger_file.write_text(json.dumps({"stages": stages}), encoding="utf-8")
    receipt_file.write_text(json.dumps({"final_status": "CONTAINED_NEEDS_REVIEW"}), encoding="utf-8")

    assert validate_claims(
        readme_path=str(readme),
        ledger_path=str(ledger_file),
        receipt_path=str(receipt_file),
        strict_all_stages=True
    ) is False

def test_validate_claims_fails_when_create_duo_unacknowledged(tmp_path):
    # README claims bare SUCCESS for create without noting Duo status
    unacknowledged_readme = SAMPLE_README.replace("⚠️ PARTIAL (Duo flow: not executed)", "✅ SUCCESS")
    readme = tmp_path / "README.md"
    readme.write_text(unacknowledged_readme, encoding="utf-8")

    ledger_file = tmp_path / "stage_ledger.json"
    receipt_file = tmp_path / "evidence_receipt.json"

    stages = {}
    for stg in ["plan", "create", "configure", "verify", "secure", "package", "monitor", "govern"]:
        stages[stg] = {"status": "SUCCESS", "duo_executed": False}
    stages["release"] = {"status": "SKIPPED"}

    ledger_file.write_text(json.dumps({"stages": stages}), encoding="utf-8")
    receipt_file.write_text(json.dumps({"final_status": "CONTAINED_NEEDS_REVIEW"}), encoding="utf-8")

    assert validate_claims(
        readme_path=str(readme),
        ledger_path=str(ledger_file),
        receipt_path=str(receipt_file),
        strict_all_stages=True
    ) is False

def test_validate_claims_fails_when_stage_failed_in_ledger(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(SAMPLE_README, encoding="utf-8")

    ledger_file = tmp_path / "stage_ledger.json"
    receipt_file = tmp_path / "evidence_receipt.json"

    stages = {}
    for stg in ["plan", "create", "configure", "verify", "secure", "package", "monitor", "govern"]:
        stages[stg] = {"status": "SUCCESS"}
    stages["verify"] = {"status": "FAILED"} # verify failed
    stages["release"] = {"status": "SKIPPED"}

    ledger_file.write_text(json.dumps({"stages": stages}), encoding="utf-8")
    receipt_file.write_text(json.dumps({"final_status": "NOT_VERIFIED"}), encoding="utf-8")

    assert validate_claims(
        readme_path=str(readme),
        ledger_path=str(ledger_file),
        receipt_path=str(receipt_file),
        strict_all_stages=True
    ) is False

def test_validate_claims_passes_when_create_marked_partial_in_ledger(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(SAMPLE_README, encoding="utf-8")

    ledger_file = tmp_path / "stage_ledger.json"
    receipt_file = tmp_path / "evidence_receipt.json"

    stages = {}
    for stg in ["plan", "configure", "verify", "secure", "package", "monitor", "govern"]:
        stages[stg] = {"status": "SUCCESS"}
    stages["create"] = {"status": "PARTIAL"}
    stages["release"] = {"status": "SKIPPED"}

    ledger_file.write_text(json.dumps({"stages": stages}), encoding="utf-8")
    receipt_file.write_text(json.dumps({"final_status": "CONTAINED_NEEDS_REVIEW", "not_established": ["GitLab Duo flow execution"]}), encoding="utf-8")

    assert validate_claims(
        readme_path=str(readme),
        ledger_path=str(ledger_file),
        receipt_path=str(receipt_file),
        strict_all_stages=True
    ) is True

def test_audit_ci_claims_fails_on_nonexistent_job(tmp_path):
    from scripts.check_readme_claims import audit_ci_claims_and_citations
    readme = tmp_path / "README.md"
    readme.write_text("Enforced by nonexistent:fake_job in stage verification.\n", encoding="utf-8")
    ci_yml = tmp_path / ".gitlab-ci.yml"
    ci_yml.write_text("verify:job:\n  script: echo 1\n", encoding="utf-8")

    passed, discrepancies = audit_ci_claims_and_citations(
        readme_path=str(readme),
        gitlab_ci_path=str(ci_yml),
        docs_dir=str(tmp_path / "nonexistent_docs")
    )
    assert passed is False
    assert any("does not exist in .gitlab-ci.yml" in d for d in discrepancies)

def test_audit_ci_claims_fails_on_job_not_executing_script(tmp_path):
    from scripts.check_readme_claims import audit_ci_claims_and_citations
    readme = tmp_path / "README.md"
    readme.write_text("Stage verify:job enforces scripts/uncalled_guard.py.\n", encoding="utf-8")
    ci_yml = tmp_path / ".gitlab-ci.yml"
    ci_yml.write_text("verify:job:\n  script: echo 1\n", encoding="utf-8")

    passed, discrepancies = audit_ci_claims_and_citations(
        readme_path=str(readme),
        gitlab_ci_path=str(ci_yml),
        docs_dir=str(tmp_path / "nonexistent_docs")
    )
    assert passed is False
    assert any("not called in verify:job's CI script" in d for d in discrepancies)

def test_audit_ci_claims_fails_on_stale_pipeline_id(tmp_path):
    from scripts.check_readme_claims import audit_ci_claims_and_citations
    readme = tmp_path / "README.md"
    readme.write_text("Verified in Pipeline #2982183259.\n", encoding="utf-8")
    ci_yml = tmp_path / ".gitlab-ci.yml"
    ci_yml.write_text("job:1:\n  script: echo 1\n", encoding="utf-8")

    passed, discrepancies = audit_ci_claims_and_citations(
        readme_path=str(readme),
        gitlab_ci_path=str(ci_yml),
        docs_dir=str(tmp_path / "nonexistent_docs")
    )
    assert passed is False
    assert any("stale pipeline ID 2982183259" in d for d in discrepancies)

def test_audit_ci_claims_fails_on_stale_issue_number(tmp_path):
    from scripts.check_readme_claims import audit_ci_claims_and_citations
    readme = tmp_path / "README.md"
    readme.write_text("Tracks Incident Work Item #50 in CI.\n", encoding="utf-8")
    ci_yml = tmp_path / ".gitlab-ci.yml"
    ci_yml.write_text("job:1:\n  script: echo 1\n", encoding="utf-8")

    passed, discrepancies = audit_ci_claims_and_citations(
        readme_path=str(readme),
        gitlab_ci_path=str(ci_yml),
        docs_dir=str(tmp_path / "nonexistent_docs")
    )
    assert passed is False
    assert any("stale incident Work Item #50" in d for d in discrepancies)

def test_audit_ci_claims_fails_on_stale_cloud_run_revision(tmp_path):
    from scripts.check_readme_claims import audit_ci_claims_and_citations
    readme = tmp_path / "README.md"
    readme.write_text("Deployed revision faultforge-checkout-00030-dit to staging.\n", encoding="utf-8")
    ci_yml = tmp_path / ".gitlab-ci.yml"
    ci_yml.write_text("job:1:\n  script: echo 1\n", encoding="utf-8")

    passed, discrepancies = audit_ci_claims_and_citations(
        readme_path=str(readme),
        gitlab_ci_path=str(ci_yml),
        docs_dir=str(tmp_path / "nonexistent_docs")
    )
    assert passed is False
    assert any("stale Cloud Run revision 'faultforge-checkout-00030-dit'" in d for d in discrepancies)
