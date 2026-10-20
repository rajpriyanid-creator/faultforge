# SPDX-License-Identifier: MIT
import os
import json
import pytest
from scripts.record_duo_evidence import query_duo_evidence, determine_candidate_source

def test_determine_candidate_source_duo_authored():
    evidence = {
        "found": True,
        "author_username": "ai-faultforge_resilience_flow",
        "run_url": "https://gitlab.com/test/runs/101",
        "mr_iid": 42
    }
    src = determine_candidate_source(evidence)
    assert src == "duo-authored (MR !42)"

def test_determine_candidate_source_missing_run_url():
    evidence = {
        "found": True,
        "author_username": "ai-faultforge_resilience_flow",
        "run_url": None,
        "mr_iid": 42
    }
    src = determine_candidate_source(evidence)
    assert src == "reference-fix (not Duo-authored)"

def test_determine_candidate_source_human_author():
    evidence = {
        "found": True,
        "author_username": "rajpriyanid",
        "run_url": "https://gitlab.com/test/runs/101",
        "mr_iid": 42
    }
    src = determine_candidate_source(evidence)
    assert src == "reference-fix (not Duo-authored)"

def test_determine_candidate_source_not_found():
    evidence = {"found": False}
    src = determine_candidate_source(evidence)
    assert src == "reference-fix (not Duo-authored)"

def test_record_duo_evidence_no_credentials(tmp_path):
    output_file = str(tmp_path / "duo_evidence.json")
    evidence = query_duo_evidence(token=None, project_id=None, output_path=output_file)
    assert os.path.exists(output_file)
    assert evidence["found"] is False
    assert "Missing" in evidence["reason"]

def test_record_duo_evidence_require_flag_fails_when_missing(tmp_path):
    output_file = str(tmp_path / "duo_evidence.json")
    with pytest.raises(SystemExit):
        query_duo_evidence(token=None, project_id=None, require=True, output_path=output_file)

def test_record_duo_evidence_parses_matching_mr(tmp_path, monkeypatch):
    output_file = str(tmp_path / "duo_evidence.json")

    class MockResponse:
        def __init__(self, data, status_code=200):
            self.data = data
            self.status_code = status_code
        def json(self):
            return self.data

    def mock_get(url, *args, **kwargs):
        if "merge_requests" in url:
            return MockResponse([
                {
                    "iid": 42,
                    "title": "Fix: Add timeout to shipping client",
                    "web_url": "https://gitlab.com/test/project/-/merge_requests/42",
                    "source_branch": "fix/resilience-shipping-timeout",
                    "author": {"username": "ai-faultforge_resilience_flow"},
                    "labels": ["duo-agent", "resilience"],
                    "created_at": "2026-10-19T20:00:00Z"
                }
            ])
        return MockResponse([], status_code=404)

    monkeypatch.setattr("requests.get", mock_get)

    evidence = query_duo_evidence(
        token="test-token",
        project_id="12345",
        output_path=output_file,
        bot_user="ai-faultforge_resilience_flow"
    )

    assert evidence["found"] is True
    assert evidence["mr_iid"] == 42
    assert evidence["source_branch"] == "fix/resilience-shipping-timeout"
    assert evidence["author_username"] == "ai-faultforge_resilience_flow"

def test_trigger_duo_flow_no_confirmed_status():
    trigger_script = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "trigger_duo_flow.py")
    with open(trigger_script, "r", encoding="utf-8") as f:
        content = f.read()

    import re
    matches = re.findall(r'["\']status["\']\s*:\s*["\']CONFIRMED["\']', content)
    assert len(matches) == 0, "trigger_duo_flow.py must not emit 'CONFIRMED' as Duo status"
