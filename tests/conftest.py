import os
import pytest
import asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.resilience.policy import shipping_circuit_breaker
from app.resilience.metrics import global_metrics

@pytest.fixture(autouse=True)
def reset_resilience_state():
    """Reset circuit breaker and metrics before every test."""
    shipping_circuit_breaker.state = shipping_circuit_breaker.state.CLOSED
    shipping_circuit_breaker.failure_count = 0
    shipping_circuit_breaker.last_failure_time = 0.0
    global_metrics.reset()
    yield

@pytest.fixture
async def async_client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
