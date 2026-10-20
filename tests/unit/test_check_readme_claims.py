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
| **`create`** | Duo Remediation | `reports/diagnosis_report.json` | ✅ SUCCESS |
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

def test_validate_claims_passes_when_consistent(tmp_path):
    readme = tmp_path / "README.md"
    readme.write_text(SAMPLE_README, encoding="utf-8")

    ledger_file = tmp_path / "stage_ledger.json"
    stages = {}
    for stg in ["plan", "create", "configure", "verify", "secure", "package", "monitor", "govern"]:
        stages[stg] = {"status": "SUCCESS"}
    stages["release"] = {"status": "SKIPPED"}

    ledger_file.write_text(json.dumps({"stages": stages}), encoding="utf-8")

    assert validate_claims(
        readme_path=str(readme),
        ledger_path=str(ledger_file),
        receipt_path=str(tmp_path / "nonexistent.json"),
        strict_all_stages=True
    ) is True

def test_validate_claims_fails_when_inflated_claim(tmp_path):
    # README claims bare SUCCESS for release, but ledger says SKIPPED
    inflated_readme = SAMPLE_README.replace("✅ SUCCESS / SKIPPED", "✅ SUCCESS")
    readme = tmp_path / "README.md"
    readme.write_text(inflated_readme, encoding="utf-8")

    ledger_file = tmp_path / "stage_ledger.json"
    stages = {}
    for stg in ["plan", "create", "configure", "verify", "secure", "package", "monitor", "govern"]:
        stages[stg] = {"status": "SUCCESS"}
    stages["release"] = {"status": "SKIPPED"}

    ledger_file.write_text(json.dumps({"stages": stages}), encoding="utf-8")

    assert validate_claims(
        readme_path=str(readme),
        ledger_path=str(ledger_file),
        receipt_path=str(tmp_path / "nonexistent.json"),
        strict_all_stages=True
    ) is False
