# SPDX-License-Identifier: MIT
import os
import re
import json
import pytest
from scripts.plan_incident import plan_incident

def test_no_hardcoded_issue_numbers_in_script():
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "plan_incident.py")
    with open(script_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Must not contain hardcoded issue numbers like /issues/29 or /issues/42
    hardcoded_matches = re.findall(r'/-/(?:issues|work_items)/\d+', content)
    assert len(hardcoded_matches) == 0, f"plan_incident.py contains hardcoded issue numbers: {hardcoded_matches}"
    assert "/issues/29" not in content, "plan_incident.py must not hardcode stale /issues/29"

def test_plan_incident_resolves_from_env_url(tmp_path, monkeypatch):
    out_file = str(tmp_path / "issue.json")
    monkeypatch.setenv("FF_INCIDENT_ISSUE_URL", "https://gitlab.com/test/project/-/work_items/42")
    monkeypatch.setenv("FF_INCIDENT_ISSUE_IID", "42")
    data = plan_incident(dossier_path=str(tmp_path / "nonexistent.json"), output_path=out_file)
    assert data["web_url"] == "https://gitlab.com/test/project/-/work_items/42"
    assert data["issue_iid"] == 42
    assert os.path.exists(out_file)

def test_plan_incident_resolves_from_api_mock(tmp_path, monkeypatch):
    out_file = str(tmp_path / "issue.json")
    monkeypatch.delenv("FF_INCIDENT_ISSUE_URL", raising=False)
    monkeypatch.delenv("CI_INCIDENT_ISSUE_URL", raising=False)
    monkeypatch.delenv("FF_INCIDENT_ISSUE_IID", raising=False)
    monkeypatch.delenv("CI_INCIDENT_ISSUE_IID", raising=False)

    class MockResponse:
        status_code = 200
        def json(self):
            return [{
                "iid": 42,
                "title": "Incident inc-42: Shipping dependency SLA budget breach",
                "web_url": "https://gitlab.com/test/project/-/work_items/42"
            }]

    def mock_get(url, *args, **kwargs):
        return MockResponse()

    import requests
    monkeypatch.setattr(requests, "get", mock_get)

    data = plan_incident(dossier_path=str(tmp_path / "nonexistent.json"), output_path=out_file)
    assert data["issue_iid"] == 42
    assert data["web_url"] == "https://gitlab.com/test/project/-/work_items/42"
