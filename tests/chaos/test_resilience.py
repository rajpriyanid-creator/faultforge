# SPDX-License-Identifier: MIT
import os
import time
import pytest
import requests
from app.config import settings

CHAOS_TARGET_URL = os.getenv("APP_TARGET_URL", "http://127.0.0.1:8090").rstrip("/")
TOXIPROXY_API = os.getenv("TOXIPROXY_URL", "http://127.0.0.1:8474").rstrip("/")

def is_chaos_stack_ready() -> bool:
    try:
        r_app = requests.get(f"{CHAOS_TARGET_URL}/health", timeout=1.0)
        r_toxi = requests.get(f"{TOXIPROXY_API}/version", timeout=1.0)
        return r_app.status_code == 200 and r_toxi.status_code == 200
    except Exception:
        return False

@pytest.mark.chaos
def test_shipping_dependency_chaos_resilience():
    """
    Real chaos resilience test:
    Sends real HTTP request to the service while Toxiproxy injects 3500ms downstream delay.
    Verifies that the service enforces SLA budget (<1500ms) and returns observable fallback.
    - FAILS on C5 (hangs for 3500ms exceeding SLA budget)
    - PASSES on fixed code (recovers via fallback within 840ms)
    """
    if not is_chaos_stack_ready():
        pytest.skip(
            f"Chaos environment not reachable at {CHAOS_TARGET_URL} or {TOXIPROXY_API}. "
            f"Run 'docker compose -f chaos/docker-compose.chaos.yml up' to execute real chaos tests."
        )

    payload = {
        "order_id": f"CHAOS-TEST-{int(time.time())}",
        "customer_id": "CUST-VERIFY",
        "destination_zip": "94103",
        "weight_kg": 2.0,
        "items": [
            {"item_id": "ITEM-1", "name": "Resilience Guide", "price": 49.99, "quantity": 1}
        ]
    }

    t0 = time.perf_counter()
    response = requests.post(f"{CHAOS_TARGET_URL}/api/v1/checkout", json=payload, timeout=5.0)
    elapsed_ms = (time.perf_counter() - t0) * 1000

    # 1. Assert SLA budget enforcement: Must NOT hang for the full 3500ms downstream delay
    assert elapsed_ms <= settings.LATENCY_BUDGET_MS, (
        f"SLA budget breach: Request took {elapsed_ms:.1f}ms, exceeding budget of {settings.LATENCY_BUDGET_MS}ms. "
        f"Service lacks bounded timeout."
    )

    # 2. Assert HTTP 200 with fallback status
    assert response.status_code == 200, f"Expected HTTP 200, got {response.status_code}: {response.text}"
    data = response.json()
    assert data["status"] == "CONFIRMED_ESTIMATED_SHIPPING"

    # 3. Assert shipping details carry fallback and estimate flags
    shipping = data.get("shipping_details", {})
    assert shipping.get("is_fallback") is True, "Expected is_fallback to be True under degraded dependency"
    assert shipping.get("is_estimate") is True, "Expected is_estimate to be True"
