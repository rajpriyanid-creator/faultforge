# SPDX-License-Identifier: MIT
import os
import json
import subprocess
import sys
import pytest

def test_render_metrics_success_on_sample_report():
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "render_metrics.py")
    sample_file = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "sample_reports", "replay_evaluation.json")
    res = subprocess.run([sys.executable, script_path, "--file", sample_file], capture_output=True, text=True)
    assert res.returncode == 0
    assert "FaultForge Empirical Resilience Metrics Ledger" in res.stdout
    assert "SLA breaches" in res.stdout

def test_render_metrics_exits_on_missing_baseline_fields(tmp_path):
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "render_metrics.py")
    bad_data = {
        "raw_metrics": {
            "hardened_avg_ms": 488.75,
            "hardened_p50_ms": 811.50,
            "hardened_p95_ms": 815.41,
            "hardened_max_ms": 815.41
        }
    }
    bad_file = tmp_path / "replay_evaluation.json"
    bad_file.write_text(json.dumps(bad_data), encoding="utf-8")
    res = subprocess.run([sys.executable, script_path, "--file", str(bad_file)], capture_output=True, text=True)
    assert res.returncode != 0
    assert "Missing required baseline metric fields" in res.stderr

def test_render_metrics_exits_on_missing_candidate_fields(tmp_path):
    script_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "render_metrics.py")
    bad_data = {
        "raw_metrics": {
            "baseline_avg_ms": 3652.00,
            "baseline_p50_ms": 3631.05,
            "baseline_p95_ms": 3718.82,
            "baseline_max_ms": 3718.82
        }
    }
    bad_file = tmp_path / "replay_evaluation.json"
    bad_file.write_text(json.dumps(bad_data), encoding="utf-8")
    res = subprocess.run([sys.executable, script_path, "--file", str(bad_file)], capture_output=True, text=True)
    assert res.returncode != 0
    assert "Missing required candidate metric fields" in res.stderr
