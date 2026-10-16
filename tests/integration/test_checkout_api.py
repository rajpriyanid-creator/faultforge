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
async def test_checkout_endpoint_with_fallback(monkeypatch):
    # Ensure fallback works seamlessly end-to-end
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
        assert data["status"] in ("CONFIRMED", "CONFIRMED_ESTIMATED_SHIPPING")
        assert data["items_subtotal"] == 60.00
        assert data["total_amount"] > 60.00
        assert "X-Response-Time-Ms" in res.headers
