# SPDX-License-Identifier: MIT
# Copyright (c) 2026 FaultForge Authors

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

    def _fallback(self, destination_zip: str, weight_kg: float, reason: str, start_time: float) -> Dict[str, Any]:
        duration_ms = (time.perf_counter() - start_time) * 1000
        data = get_graceful_shipping_fallback(destination_zip, weight_kg, reason)
        data["latency_ms"] = round(duration_ms, 2)
        global_metrics.record_request(duration_ms, success=True, used_fallback=True)
        return data

    async def get_shipping_rate(self, destination_zip: str, weight_kg: float) -> Dict[str, Any]:
        """
        Fetch a shipping rate with a strict 0.8s bounded timeout, circuit breaking,
        and a deterministic fallback estimate (is_fallback=True, is_estimate=True).
        This is a safe idempotent read; no retries are applied to preserve the SLA budget.
        """
        start_time = time.perf_counter()
        url = f"{self.base_url.rstrip('/')}/rates"
        params = {"destination_zip": destination_zip, "weight_kg": weight_kg}

        use_breaker = settings.CIRCUIT_BREAKER_ENABLED

        # Shed load: skip the degraded dependency while the circuit is OPEN.
        if use_breaker and not shipping_circuit_breaker.can_execute():
            logger.warning("Shipping circuit breaker OPEN; serving fallback estimate")
            return self._fallback(
                destination_zip, weight_kg, "Circuit breaker OPEN: shipping dependency shed", start_time
            )

        timeout = httpx.Timeout(SHIPPING_TIMEOUT_SECONDS)  # connect/read/write/pool = 0.8s

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code < 500:
                # Client errors are not dependency degradation; surface them.
                raise
            logger.warning(f"Shipping dependency returned {exc.response.status_code}; using fallback")
            if use_breaker:
                shipping_circuit_breaker.record_failure()
            if not settings.FALLBACK_ENABLED:
                raise
            return self._fallback(
                destination_zip, weight_kg, f"Shipping dependency HTTP {exc.response.status_code}", start_time
            )
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            logger.warning(f"Shipping dependency timed out or unreachable ({type(exc).__name__}); using fallback")
            if use_breaker:
                shipping_circuit_breaker.record_failure()
            if not settings.FALLBACK_ENABLED:
                raise
            return self._fallback(
                destination_zip,
                weight_kg,
                f"Shipping dependency exceeded {SHIPPING_TIMEOUT_SECONDS}s timeout ({type(exc).__name__})",
                start_time,
            )

        if use_breaker:
            shipping_circuit_breaker.record_success()

        duration_ms = (time.perf_counter() - start_time) * 1000
        global_metrics.record_request(duration_ms, success=True, used_fallback=False)
        data["is_fallback"] = False
        data["latency_ms"] = round(duration_ms, 2)
        return data


shipping_client = ShippingClient()
