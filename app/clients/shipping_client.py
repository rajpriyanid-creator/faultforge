# SPDX-License-Identifier: MIT
# Copyright (c) 2026 FaultForge Authors

import asyncio
import time
import logging
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.resilience.metrics import global_metrics
from app.resilience.policy import (
    shipping_circuit_breaker,
    get_graceful_shipping_fallback,
)

logger = logging.getLogger("faultforge.client")

# Strict SLA budget for the shipping dependency (seconds).
SHIPPING_TIMEOUT_SECONDS = 0.8

class ShippingClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.SHIPPING_SERVICE_URL
        self.timeout = httpx.Timeout(SHIPPING_TIMEOUT_SECONDS)

    def _fallback(self, destination_zip: str, weight_kg: float, reason: str, start_time: float) -> Dict[str, Any]:
        duration_ms = (time.perf_counter() - start_time) * 1000
        data = get_graceful_shipping_fallback(destination_zip, weight_kg, reason)
        data["latency_ms"] = round(duration_ms, 2)
        global_metrics.record_request(duration_ms, success=True, used_fallback=True)
        return data

    async def _fetch(self, url: str, params: Dict[str, Any]) -> Dict[str, Any]:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()

    async def get_shipping_rate(self, destination_zip: str, weight_kg: float) -> Dict[str, Any]:
        """
        Fetch a shipping rate with a strict 0.8s bounded timeout, circuit breaker,
        and deterministic graceful fallback (is_fallback=True, is_estimate=True).
        This is an idempotent read, so no retries are applied.
        """
        start_time = time.perf_counter()
        url = f"{self.base_url.rstrip('/')}/rates"
        params = {"destination_zip": destination_zip, "weight_kg": weight_kg}

        if settings.CIRCUIT_BREAKER_ENABLED and not shipping_circuit_breaker.can_execute():
            logger.warning("Shipping circuit breaker OPEN: shedding load, serving fallback estimate")
            return self._fallback(
                destination_zip, weight_kg,
                "Circuit breaker OPEN: shipping dependency degraded", start_time,
            )

        try:
            # Overall wall-clock bound in addition to per-phase httpx timeouts.
            data = await asyncio.wait_for(
                self._fetch(url, params), timeout=SHIPPING_TIMEOUT_SECONDS
            )
        except (asyncio.TimeoutError, httpx.TimeoutException) as exc:
            logger.warning(f"Shipping call exceeded {SHIPPING_TIMEOUT_SECONDS}s budget: {exc!r}")
            shipping_circuit_breaker.record_failure()
            return self._fallback(
                destination_zip, weight_kg,
                f"Shipping dependency timed out after {SHIPPING_TIMEOUT_SECONDS}s", start_time,
            )
        except (httpx.TransportError, httpx.HTTPStatusError, ValueError) as exc:
            logger.warning(f"Shipping dependency error: {exc!r}")
            shipping_circuit_breaker.record_failure()
            return self._fallback(
                destination_zip, weight_kg,
                f"Shipping dependency error: {type(exc).__name__}", start_time,
            )

        shipping_circuit_breaker.record_success()
        duration_ms = (time.perf_counter() - start_time) * 1000
        global_metrics.record_request(duration_ms, success=True, used_fallback=False)
        data["is_fallback"] = False
        data["latency_ms"] = round(duration_ms, 2)
        return data

shipping_client = ShippingClient()
