# SPDX-License-Identifier: MIT
import os
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
    """Verify /api/v1/evidence returns exactly the sealed receipt with zero synthesized or extra keys/values."""
    import json
    receipt_path = "reports/evidence_receipt.json" if os.path.exists("reports/evidence_receipt.json") else "docs/sample_reports/evidence_receipt.json"
    assert os.path.exists(receipt_path)
    with open(receipt_path, "r", encoding="utf-8") as f:
        stored_receipt = json.load(f)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        res = await client.get("/api/v1/evidence")
        assert res.status_code == 200
        api_data = res.json()
        assert api_data == stored_receipt
        for k in api_data:
            assert k in stored_receipt
            assert api_data[k] == stored_receipt[k]

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

def test_dashboard_has_no_hardcoded_prices_or_pipelines():
    dashboard_path = os.path.join(os.path.dirname(__file__), "..", "..", "app", "dashboard.html")
    with open(dashboard_path, "r", encoding="utf-8") as f:
        content = f.read()
    assert "14.99" not in content, "dashboard.html must not hardcode $14.99 fallback price"
    assert "2965823054" not in content, "dashboard.html must not hardcode pipeline ID 2965823054"
    assert "2965807846" not in content, "dashboard.html must not hardcode pipeline ID 2965807846"
    assert "2963430484" not in content, "dashboard.html must not hardcode pipeline ID 2963430484"
    assert "78.4%" not in content, "dashboard.html must not hardcode static '78.4%' reduction percentage"
    assert "78.3%" not in content, "dashboard.html must not hardcode static '78.3%' reduction percentage"
    assert "77.6%" not in content, "dashboard.html must not hardcode static '77.6%' reduction percentage"
    assert "92.9%" not in content, "dashboard.html must not hardcode static '92.9%' reduction percentage"
    assert "93.2%" not in content, "dashboard.html must not hardcode static '93.2%' reduction percentage"

    # Verify no static percentage in HTML markup outside of scripts
    html_markup = content.split("<script")[0]
    import re
    pct_matches = re.findall(r">\s*(\d{2}\.\d%)\s*(?:MEAN\s+)?REDUCTION", html_markup, re.IGNORECASE)
    assert not pct_matches, f"dashboard.html markup contains hardcoded reduction percentage: {pct_matches}"


