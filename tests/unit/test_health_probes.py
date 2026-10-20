# SPDX-License-Identifier: MIT
import os
import json
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_probe_payload():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert data["service"] == "faultforge-checkout"
        assert "uptime_seconds" in data
        assert "revision" in data

@pytest.mark.asyncio
async def test_readiness_probe_circuit_status():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["ready"] is True
        assert data["circuit_breaker"]["state"] in ("CLOSED", "OPEN", "HALF_OPEN")

@pytest.mark.asyncio
async def test_metrics_telemetry_fields():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "resilience_metrics" in data
        rm = data["resilience_metrics"]
        assert "total_requests" in rm
        assert "fallback_invocations" in rm
        assert "latency_p95_ms" in rm

def test_verify_live_unauthenticated(tmp_path):
    from scripts.verify_live import verify_live_service
    out_file = str(tmp_path / "live_verification.json")
    rec = verify_live_service(service_url="http://127.0.0.1:9999", output_path=out_file)
    assert os.path.exists(out_file)
    assert rec["traffic_split"]["status"] in ("UNVERIFIED_NO_GCP_AUTH", "GCLOUD_DESCRIBE_FAILED")

def test_resolve_target_url_release_json(tmp_path, monkeypatch):
    from scripts.monitor_service import resolve_target_url
    monkeypatch.chdir(tmp_path)
    os.makedirs("reports", exist_ok=True)
    with open("reports/release.json", "w", encoding="utf-8") as f:
        json.dump({"status": "STAGED", "url": "https://candidate.run.app"}, f)
    url = resolve_target_url("http://fallback")
    assert url == "https://candidate.run.app"

def test_verify_live_with_gcloud_traffic_split(tmp_path, monkeypatch):
    import subprocess
    from scripts.verify_live import verify_live_service

    mock_gcloud_data = {
        "status": {
            "traffic": [
                {
                    "percent": 100,
                    "revisionName": "faultforge-checkout-00002-kpl"
                },
                {
                    "percent": 0,
                    "revisionName": "faultforge-checkout-00003-can",
                    "tag": "candidate",
                    "url": "https://candidate---faultforge-checkout.run.app"
                }
            ]
        }
    }

    class MockSubprocessResult:
        returncode = 0
        stdout = json.dumps(mock_gcloud_data)
        stderr = ""

    monkeypatch.setattr(subprocess, "run", lambda *args, **kwargs: MockSubprocessResult())

    out_file = str(tmp_path / "live_verification.json")
    rec = verify_live_service(service_url="http://127.0.0.1:9999", output_path=out_file)

    assert rec["traffic_split"]["verified"] is True
    assert rec["traffic_split"]["status"] == "VERIFIED"
    assert rec["traffic_split"]["candidate_percent"] == 0
    assert rec["traffic_split"]["production_percent"] == 100
    assert rec["traffic_split"]["candidate_tag"] == "candidate"
    assert rec["traffic_split"]["candidate_url"] == "https://candidate---faultforge-checkout.run.app"
    assert rec["traffic_split"]["candidate_revision"] == "faultforge-checkout-00003-can"
    assert rec["traffic_split"]["production_revision"] == "faultforge-checkout-00002-kpl"
