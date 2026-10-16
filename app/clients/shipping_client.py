import time
import logging
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.resilience.policy import (
    shipping_circuit_breaker,
    get_graceful_shipping_fallback,
    CircuitBreakerOpenException
)
from app.resilience.metrics import global_metrics

logger = logging.getLogger("faultforge.client")

class ShippingClient:
    def __init__(self, base_url: Optional[str] = None, timeout_seconds: Optional[float] = None):
        self.base_url = base_url or settings.SHIPPING_SERVICE_URL
        self.timeout_seconds = timeout_seconds if timeout_seconds is not None else settings.HTTP_TIMEOUT_SECONDS

    async def get_shipping_rate(self, destination_zip: str, weight_kg: float) -> Dict[str, Any]:
        """
        Fetches shipping rate from downstream carrier API with circuit breaker,
        strict bounded timeout, and graceful fallback resilience.
        """
        start_time = time.perf_counter()

        # 1. Check Circuit Breaker Gate
        if settings.CIRCUIT_BREAKER_ENABLED and not shipping_circuit_breaker.can_execute():
            duration_ms = (time.perf_counter() - start_time) * 1000
            global_metrics.record_request(duration_ms, success=True, used_fallback=True)
            logger.warning(f"Circuit Breaker is OPEN. Short-circuiting request for zip={destination_zip}")
            return get_graceful_shipping_fallback(
                destination_zip=destination_zip,
                weight_kg=weight_kg,
                reason="Circuit Breaker Open (Downstream Degraded)"
            )

        url = f"{self.base_url.rstrip('/')}/rates"
        params = {"destination_zip": destination_zip, "weight_kg": weight_kg}

        # 2. Outbound Request with Enforced Bounded Timeout
        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                response = await client.get(url, params=params)
                response.raise_for_status()
                data = response.json()

                duration_ms = (time.perf_counter() - start_time) * 1000
                if settings.CIRCUIT_BREAKER_ENABLED:
                    shipping_circuit_breaker.record_success()
                global_metrics.record_request(duration_ms, success=True, used_fallback=False)
                data["is_fallback"] = False
                data["latency_ms"] = round(duration_ms, 2)
                return data

        except httpx.TimeoutException as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(
                f"Downstream shipping API timed out after {self.timeout_seconds}s (elapsed: {duration_ms:.1f}ms): {exc}"
            )
            if settings.CIRCUIT_BREAKER_ENABLED:
                shipping_circuit_breaker.record_failure()

            if settings.FALLBACK_ENABLED:
                global_metrics.record_request(duration_ms, success=True, used_fallback=True)
                fallback_data = get_graceful_shipping_fallback(
                    destination_zip=destination_zip,
                    weight_kg=weight_kg,
                    reason=f"Timeout ({self.timeout_seconds}s SLA exceeded)"
                )
                fallback_data["latency_ms"] = round(duration_ms, 2)
                return fallback_data
            else:
                global_metrics.record_request(duration_ms, success=False, used_fallback=False)
                raise

        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            logger.error(f"Downstream shipping API call failed: {exc}")
            if settings.CIRCUIT_BREAKER_ENABLED:
                shipping_circuit_breaker.record_failure()

            if settings.FALLBACK_ENABLED:
                global_metrics.record_request(duration_ms, success=True, used_fallback=True)
                fallback_data = get_graceful_shipping_fallback(
                    destination_zip=destination_zip,
                    weight_kg=weight_kg,
                    reason=f"Downstream Error: {str(exc)}"
                )
                fallback_data["latency_ms"] = round(duration_ms, 2)
                return fallback_data
            else:
                global_metrics.record_request(duration_ms, success=False, used_fallback=False)
                raise

shipping_client = ShippingClient()
