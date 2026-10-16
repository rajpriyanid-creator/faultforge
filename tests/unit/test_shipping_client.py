import pytest
import httpx
from unittest.mock import patch, AsyncMock
from app.clients.shipping_client import ShippingClient
from app.config import settings

@pytest.mark.asyncio
async def test_shipping_client_success():
    client = ShippingClient(base_url="http://mock-shipping")
    mock_response = httpx.Response(
        status_code=200,
        json={"carrier": "TestCarrier", "rate": 12.50, "currency": "USD"},
        request=httpx.Request("GET", "http://mock-shipping/rates")
    )

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        result = await client.get_shipping_rate(destination_zip="10001", weight_kg=1.0)
        assert result["carrier"] == "TestCarrier"
        assert result["rate"] == 12.50
        assert result["is_fallback"] is False

@pytest.mark.asyncio
async def test_shipping_client_timeout_triggers_fallback():
    client = ShippingClient(base_url="http://mock-shipping", timeout_seconds=0.5)

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = httpx.TimeoutException("Connection timed out")
        result = await client.get_shipping_rate(destination_zip="10001", weight_kg=2.0)
        assert result["is_fallback"] is True
        assert "Timeout" in result["fallback_reason"]
        assert result["rate"] == 10.00
