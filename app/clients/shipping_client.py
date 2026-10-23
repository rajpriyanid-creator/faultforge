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

# Strict SLA budget for the outbound shipping call (connect/read/write/pool).
SHIPPING_TIMEOUT_SECONDS = 0.8


class ShippingClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.SHIPPING_SERVICE_URL

    def _fallback(self, destination_zip: str, weight_kg: float, reason: str, start_time: float) -> Dict[str, Any]:
        duration_ms = (time.perf_counter() - start_time) * 1000
        global_metrics.record_request(duration_ms, success=True, used_fallback=True)
        data = get_graceful_shipping_fallback(destination_zip, weight_kg, reason)
        data["is_fallback"] = True
        data["is_estimate"] = True
        data["latency_ms"] = round(duration_ms, 2)
        return data

    async def get_shipping_rate(self, destination_zip: str, weight_kg: float) -> Dict[str, Any]:
        """
        Fetch a shipping rate (idempotent read) with a strict 0.8s timeout, a circuit
        breaker that sheds load on a degraded dependency, and a deterministic fallback.
        """
        start_time = time.perf_counter()
        url = f"{self.base_url.rstrip('/')}/rates"
        params = {"destination_zip": destination_zip, "weight_kg": weight_kg}

        if settings.CIRCUIT_BREAKER_ENABLED and not shipping_circuit_breaker.can_execute():
            logger.warning("Shipping circuit breaker OPEN: shedding load, serving fallback estimate")
            return self._fallback(destination_zip, weight_kg, "Circuit breaker OPEN", start_time)

        try:
            timeout = httpx.Timeout(SHIPPING_TIMEOUT_SECONDS, connect=SHIPPING_TIMEOUT_SECONDS)
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code < 500:
                # Caller error, not a dependency degradation: do not trip breaker or mask it.
                raise
            shipping_circuit_breaker.record_failure()
            logger.error(f"Shipping dependency returned {exc.response.status_code}")
            if not settings.FALLBACK_ENABLED:
                raise
            return self._fallback(destination_zip, weight_kg, f"Upstream HTTP {exc.response.status_code}", start_time)
        except (httpx.TimeoutException, httpx.TransportError) as exc:
            shipping_circuit_breaker.record_failure()
            logger.error(f"Shipping dependency timed out or unreachable: {type(exc).__name__}")
            if not settings.FALLBACK_ENABLED:
                raise
            return self._fallback(
                destination_zip,
                weight_kg,
                f"Timeout/transport error ({type(exc).__name__}) within {SHIPPING_TIMEOUT_SECONDS}s budget",
                start_time,
            )

        shipping_circuit_breaker.record_success()
        duration_ms = (time.perf_counter() - start_time) * 1000
        global_metrics.record_request(duration_ms, success=True, used_fallback=False)
        data["is_fallback"] = False
        data["latency_ms"] = round(duration_ms, 2)
        return data

shipping_client = ShippingClient()
