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
| **`create`** | Duo Remediation | `reports/diagnosis_report.json` | ✅ SUCCESS (Duo: not executed) |
| **`configure`** | Chaos Wiring | `reports/fault_config.json` | ✅ SUCCESS |
| **`verify`** | Exact Replay | `reports/fault_run_baseline.json` | ✅ SUCCESS |
| **`secure`** | Secret Detection | `reports/bandit_security_report.json` | ✅ SUCCESS |
| **`package`** | Docker Build | `reports/image_digest.txt` | ✅ SUCCESS |
| **`release`** | Cloud Run Deploy | `reports/release.json` | ✅ SUCCESS / SKIPPED |
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
    assert claims["release"] == "✅ SUCCESS / SKIPPED"
    assert "Duo: not executed" in claims["create"]

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

def test_validate_claims_fails_when_inflated_claim(tmp_path):
    # README claims bare SUCCESS for release, but ledger says SKIPPED
    inflated_readme = SAMPLE_README.replace("✅ SUCCESS / SKIPPED", "✅ SUCCESS")
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

def test_validate_claims_fails_when_create_duo_unacknowledged(tmp_path):
    # README claims bare SUCCESS for create without noting Duo status
    unacknowledged_readme = SAMPLE_README.replace("✅ SUCCESS (Duo: not executed)", "✅ SUCCESS")
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
