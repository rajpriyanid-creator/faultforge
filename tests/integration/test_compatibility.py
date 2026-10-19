# SPDX-License-Identifier: MIT
"""
Backward compatibility contract test.
Verifies that older API client contracts (payload schemas and response fields)
continue to function without breaking changes after resilience hardening.
"""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_legacy_checkout_request_contract(monkeypatch):
    """Validates that a client payload processes successfully through hardened checkout."""
    async def mock_get_shipping_rate(destination_zip, weight_kg):
        return {
            "carrier": "Standard Carrier",
            "rate": 12.50,
            "currency": "USD",
            "is_fallback": False,
            "is_estimate": False
        }

    monkeypatch.setattr("app.main.shipping_client.get_shipping_rate", mock_get_shipping_rate)
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        legacy_payload = {
            "order_id": "ORD-COMPAT-001",
            "customer_id": "CUST-COMPAT-01",
            "destination_zip": "90210",
            "weight_kg": 1.5,
            "items": [
                {"item_id": "ITM-LEGACY", "name": "Legacy Item", "price": 40.0, "quantity": 1}
            ]
        }
        response = await client.post("/api/v1/checkout", json=legacy_payload)

        # HTTP contract must be 200 OK
        assert response.status_code == 200
        data = response.json()

        # Legacy required fields must exist
        assert data["order_id"] == "ORD-COMPAT-001"
        assert data["status"] in ("CONFIRMED", "CONFIRMED_ESTIMATED_SHIPPING")
        assert "items_subtotal" in data
        assert "shipping_fee" in data
        assert data["shipping_fee"] == 12.50
        assert data["total_amount"] == 52.50

        # Hardening fields are additive and do not alter existing schema contracts
        assert "shipping_details" in data
        assert "is_fallback" in data["shipping_details"]
        assert "is_estimate" in data["shipping_details"]

@pytest.mark.asyncio
async def test_legacy_health_and_metrics_contract():
    """Validates that monitoring agents consuming legacy /health endpoints receive expected keys."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        health_resp = await client.get("/health")
        assert health_resp.status_code == 200
        health_data = health_resp.json()
        assert health_data.get("status") == "healthy"
        assert "revision" in health_data
