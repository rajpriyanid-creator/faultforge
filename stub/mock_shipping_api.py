# SPDX-License-Identifier: MIT
# Copyright (c) 2026 FaultForge Authors

import os
import time
import asyncio
from fastapi import FastAPI, Query, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="Mock External Shipping Carrier API", version="1.0.0")

# Simulation controls (can be set via endpoints or environment)
SIMULATED_DELAY_SECONDS = float(os.getenv("STUB_DELAY_SECONDS", "0.0"))
SIMULATED_STATUS_CODE = int(os.getenv("STUB_STATUS_CODE", "200"))

class SimulationConfig(BaseModel):
    delay_seconds: float = 0.0
    status_code: int = 200

@app.get("/health")
async def health():
    return {"status": "ok", "service": "mock-shipping-api"}

@app.post("/simulate")
async def set_simulation(config: SimulationConfig):
    global SIMULATED_DELAY_SECONDS, SIMULATED_STATUS_CODE
    SIMULATED_DELAY_SECONDS = config.delay_seconds
    SIMULATED_STATUS_CODE = config.status_code
    return {
        "message": "Simulation configuration updated",
        "delay_seconds": SIMULATED_DELAY_SECONDS,
        "status_code": SIMULATED_STATUS_CODE
    }

@app.get("/rates")
async def get_rates(
    destination_zip: str = Query(..., description="Destination ZIP code"),
    weight_kg: float = Query(1.0, description="Package weight in kg")
):
    # Apply simulated delay if configured
    if SIMULATED_DELAY_SECONDS > 0:
        await asyncio.sleep(SIMULATED_DELAY_SECONDS)

    if SIMULATED_STATUS_CODE != 200:
        raise HTTPException(
            status_code=SIMULATED_STATUS_CODE,
            detail=f"Simulated downstream failure code: {SIMULATED_STATUS_CODE}"
        )

    # Carrier pricing logic
    base_rate = 8.50
    per_kg = 1.75
    rate = round(base_rate + (weight_kg * per_kg), 2)

    return {
        "carrier": "GlobalExpress Carrier",
        "service_level": "express_ground",
        "destination_zip": destination_zip,
        "weight_kg": weight_kg,
        "rate": rate,
        "currency": "USD",
        "estimated_days": 2,
        "is_fallback": False,
        "provider_timestamp": time.time()
    }

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8081"))
    uvicorn.run("stub.mock_shipping_api:app", host="0.0.0.0", port=port, reload=False)
