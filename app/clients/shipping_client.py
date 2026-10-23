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

# Strict SLA budget for the downstream shipping dependency (seconds).
SHIPPING_TIMEOUT_SECONDS = 0.8


class ShippingClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.SHIPPING_SERVICE_URL

    def _fallback(self, destination_zip: str, weight_kg: float, reason: str, start_time: float) -> Dict[str, Any]:
        duration_ms = (time.perf_counter() - start_time) * 1000
        global_metrics.record_request(duration_ms, success=True, used_fallback=True)
        result = get_graceful_shipping_fallback(destination_zip, weight_kg, reason)
        result["latency_ms"] = round(duration_ms, 2)
        return result

    async def get_shipping_rate(self, destination_zip: str, weight_kg: float) -> Dict[str, Any]:
        """
        Fetch a shipping rate (idempotent read) with a strict 0.8s bounded timeout,
        circuit breaker load shedding and a deterministic, clearly-labelled fallback
        (is_fallback=True, is_estimate=True) when the dependency is degraded.
        """
        start_time = time.perf_counter()
        url = f"{self.base_url.rstrip('/')}/rates"
        params = {"destination_zip": destination_zip, "weight_kg": weight_kg}
        use_breaker = settings.CIRCUIT_BREAKER_ENABLED

        # Shed load: while the circuit is OPEN, skip the degraded dependency entirely.
        if use_breaker and not shipping_circuit_breaker.can_execute():
            logger.warning("Shipping circuit breaker OPEN; serving fallback estimate")
            return self._fallback(destination_zip, weight_kg, "Circuit breaker OPEN: shipping dependency shed", start_time)

        timeout = httpx.Timeout(SHIPPING_TIMEOUT_SECONDS)  # connect/read/write/pool = 0.8s
        try:
            # asyncio.wait_for enforces 0.8s as a hard total deadline, not just per-phase.
            async def _call() -> Dict[str, Any]:
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.get(url, params=params)
                    response.raise_for_status()
                    return response.json()

            data = await asyncio.wait_for(_call(), timeout=SHIPPING_TIMEOUT_SECONDS)
        except (asyncio.TimeoutError, httpx.TimeoutException) as exc:
            if use_breaker:
                shipping_circuit_breaker.record_failure()
            logger.warning(f"Shipping dependency timed out after {SHIPPING_TIMEOUT_SECONDS}s: {exc!r}")
            if not settings.FALLBACK_ENABLED:
                raise
            return self._fallback(
                destination_zip, weight_kg,
                f"Shipping dependency timed out after {SHIPPING_TIMEOUT_SECONDS}s", start_time,
            )
        except httpx.HTTPError as exc:
            if use_breaker:
                shipping_circuit_breaker.record_failure()
            logger.warning(f"Shipping dependency error: {exc!r}")
            if not settings.FALLBACK_ENABLED:
                raise
            return self._fallback(
                destination_zip, weight_kg,
                f"Shipping dependency error: {type(exc).__name__}", start_time,
            )

        if use_breaker:
            shipping_circuit_breaker.record_success()
        duration_ms = (time.perf_counter() - start_time) * 1000
        global_metrics.record_request(duration_ms, success=True, used_fallback=False)
        data["is_fallback"] = False
        data["is_estimate"] = False
        data["latency_ms"] = round(duration_ms, 2)
        return data


shipping_client = ShippingClient()
