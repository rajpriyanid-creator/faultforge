# SPDX-License-Identifier: MIT
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
