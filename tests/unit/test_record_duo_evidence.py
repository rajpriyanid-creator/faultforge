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
    assert src == "commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token"

def test_determine_candidate_source_service_account_commit():
    evidence = {
        "found": True,
        "author_username": "rajpriyanid",
        "commit_author": "FaultForge, Supervised, Resilience, Healer",
        "commit_author_email": "service_account_group_121124982_e6349fd5e8ecd6554efb712ed8e2654f@noreply.gitlab.com",
        "run_url": "https://gitlab.com/test/automate/agent-sessions/9909079",
        "mr_iid": 3
    }
    src = determine_candidate_source(evidence)
    assert src == "commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token"

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

def test_record_duo_evidence_from_ci_env(tmp_path, monkeypatch):
    monkeypatch.setenv("FF_FLOW_RUN_URL", "https://gitlab.com/test/automate/agent-sessions/9909079")
    monkeypatch.setenv("CI_MERGE_REQUEST_IID", "3")
    monkeypatch.setenv("CI_COMMIT_REF_NAME", "fix/resilience-shipping-timeout")
    output_file = str(tmp_path / "duo_evidence.json")
    evidence = query_duo_evidence(token=None, project_id=None, from_ci_env=True, output_path=output_file)
    assert evidence["found"] is True
    assert evidence["mr_iid"] == 3
    assert evidence["candidate_source"] == "commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token"

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

def test_duo_authored_detection_and_candidate_source_integration(tmp_path):
    from scripts.evaluate_replay import evaluate_replay
    from scripts.generate_receipt import generate_evidence_receipt

    # 1. Simulate duo_evidence.json fixture
    duo_evidence = {
        "found": True,
        "mr_iid": 42,
        "mr_url": "https://gitlab.com/test/-/merge_requests/42",
        "source_branch": "fix/resilience-shipping-timeout",
        "author_username": "ai-faultforge_resilience_flow",
        "run_url": "https://gitlab.com/test/runs/99"
    }
    cand_src = determine_candidate_source(duo_evidence)
    assert cand_src == "commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token"
    duo_evidence["candidate_source"] = cand_src

    # 2. Test CI detection logic:
    cs = str(duo_evidence.get("candidate_source", "")).lower()
    ci_detection = (cs.startswith("duo-authored") or "commit authored by the duo service account" in cs) and bool(duo_evidence.get("source_branch"))
    assert ci_detection is True

    # 3. Test evaluate_replay records this candidate_source with identical fault hash 644a89784316
    base_file = os.path.join(os.path.dirname(__file__), "fixtures", "base_pass.json")
    hard_file = os.path.join(os.path.dirname(__file__), "fixtures", "hard_pass.json")
    criteria_file = os.path.join(os.path.dirname(__file__), "..", "..", "chaos", "criteria.json")
    replay_out = str(tmp_path / "replay_evaluation.json")

    with pytest.raises(SystemExit) as exc_info:
        evaluate_replay(
            baseline_path=base_file,
            hardened_path=hard_file,
            output_path=replay_out,
            criteria_path=criteria_file,
            candidate_source=cand_src
        )
    assert exc_info.value.code == 0

    with open(replay_out, "r", encoding="utf-8") as rf:
        ev = json.load(rf)

    assert ev["candidate_source"] == "commit authored by the Duo service account (session 9909079); MR opened under the maintainer's token"
    assert ev["gates"]["identical_profile_hash"]["passed"] is True
    assert ev["gates"]["identical_profile_hash"]["baseline_hash"] == ev["gates"]["identical_profile_hash"]["hardened_hash"]
