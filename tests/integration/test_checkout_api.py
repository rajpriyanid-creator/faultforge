# SPDX-License-Identifier: MIT
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/health")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "healthy"
        assert "uptime_seconds" in data

@pytest.mark.asyncio
async def test_ready_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/ready")
        assert res.status_code == 200
        data = res.json()
        assert data["ready"] is True
        assert "circuit_breaker" in data

@pytest.mark.asyncio
async def test_metrics_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/metrics")
        assert res.status_code == 200
        data = res.json()
        assert "resilience_metrics" in data
        assert "circuit_breaker" in data

@pytest.mark.asyncio
async def test_checkout_endpoint(monkeypatch):
    async def mock_get_shipping_rate(destination_zip, weight_kg):
        return {
            "carrier": "Standard Express",
            "rate": 10.00,
            "currency": "USD",
            "is_fallback": False,
            "is_estimate": False
        }

    monkeypatch.setattr("app.main.shipping_client.get_shipping_rate", mock_get_shipping_rate)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "order_id": "ORD-12345",
            "customer_id": "CUST-999",
            "destination_zip": "90210",
            "weight_kg": 2.0,
            "items": [
                {"item_id": "ITM-1", "name": "Widget A", "price": 25.00, "quantity": 2},
                {"item_id": "ITM-2", "name": "Widget B", "price": 10.00, "quantity": 1}
            ]
        }
        res = await client.post("/api/v1/checkout", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["order_id"] == "ORD-12345"
        assert data["status"] == "CONFIRMED"
        assert data["items_subtotal"] == 60.00
        assert data["total_amount"] == 70.00
        assert "X-Response-Time-Ms" in res.headers

@pytest.mark.asyncio
async def test_dashboard_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/dashboard")
        assert res.status_code == 200
        assert "FaultForge" in res.text
        assert "text/html" in res.headers["content-type"]

@pytest.mark.asyncio
async def test_resilience_checkout_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "order_id": "ORD-RESIL-1",
            "customer_id": "CUST-1",
            "destination_zip": "90210",
            "weight_kg": 2.0,
            "items": [{"item_id": "ITM-1", "name": "Test Item", "price": 50.00, "quantity": 1}]
        }
        res = await client.post("/api/v1/checkout/test-resilience", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "CONFIRMED_ESTIMATED_SHIPPING"
        assert data["shipping_details"]["is_fallback"] is True
        assert data["processed_at_ms"] <= 1500.0

@pytest.mark.asyncio
async def test_evidence_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/evidence")
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_ledger_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/ledger")
        assert res.status_code == 200

@pytest.mark.asyncio
async def test_reports_endpoint(tmp_path, monkeypatch):
    dummy_dir = tmp_path / "reports"
    dummy_dir.mkdir()
    (dummy_dir / "evidence_receipt.json").write_text('{"status": "TEST"}', encoding="utf-8")
    monkeypatch.chdir(tmp_path)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/reports/evidence_receipt")
        assert res.status_code == 200
        res_404 = await client.get("/api/v1/reports/nonexistent_report_xyz")
        assert res_404.status_code == 404


