# SPDX-License-Identifier: MIT
# Copyright (c) 2026 FaultForge Authors

import time
import logging
import httpx
from typing import Dict, Any, Optional
from app.config import settings
from app.resilience.metrics import global_metrics

logger = logging.getLogger("faultforge.client")

class ShippingClient:
    def __init__(self, base_url: Optional[str] = None):
        self.base_url = base_url or settings.SHIPPING_SERVICE_URL

    async def get_shipping_rate(self, destination_zip: str, weight_kg: float) -> Dict[str, Any]:
        """
        Simplified shipping carrier client: direct call without timeout overhead.
        Note: Removed explicit timeout and fallback to streamline call path.
        """
        start_time = time.perf_counter()
        url = f"{self.base_url.rstrip('/')}/rates"
        params = {"destination_zip": destination_zip, "weight_kg": weight_kg}

        # Regression: unconstrained outbound request without bounded timeout or fallback
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()

            duration_ms = (time.perf_counter() - start_time) * 1000
            global_metrics.record_request(duration_ms, success=True, used_fallback=False)
            data["is_fallback"] = False
            data["latency_ms"] = round(duration_ms, 2)
            return data

shipping_client = ShippingClient()
