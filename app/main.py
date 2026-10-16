import time
import logging
from typing import List, Optional
from fastapi import FastAPI, HTTPException, status, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.config import settings
from app.health import router as health_router
from app.clients.shipping_client import shipping_client
from app.resilience.metrics import global_metrics

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("faultforge.main")

app = FastAPI(
    title="FaultForge Checkout Service",
    description="Resilience-hardened checkout microservice for GitLab Transcend 2026",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)

# Request models
class OrderItem(BaseModel):
    item_id: str
    name: str
    price: float = Field(..., gt=0)
    quantity: int = Field(..., gt=0)

class CheckoutRequest(BaseModel):
    order_id: str
    customer_id: str
    destination_zip: str = Field(..., description="5-digit destination postal code", min_length=3)
    weight_kg: float = Field(default=1.5, gt=0)
    items: List[OrderItem]

class CheckoutResponse(BaseModel):
    order_id: str
    status: str
    items_subtotal: float
    shipping_fee: float
    total_amount: float
    shipping_details: dict
    processed_at_ms: float
    revision: str

@app.middleware("http")
async def add_timing_header(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - start) * 1000, 2)
    response.headers["X-Response-Time-Ms"] = str(duration_ms)
    response.headers["X-Service-Revision"] = settings.REVISION_ID
    return response

@app.get("/")
async def root():
    return {
        "service": settings.SERVICE_NAME,
        "tagline": "Rehearse a failure. Recover safely. Prove the service is stronger.",
        "version": "1.0.0",
        "revision": settings.REVISION_ID,
        "docs_url": "/docs"
    }

@app.get("/api/v1/shipping/rate")
async def get_shipping_rate(destination_zip: str, weight_kg: float = 1.0):
    try:
        rate_info = await shipping_client.get_shipping_rate(destination_zip, weight_kg)
        return rate_info
    except Exception as exc:
        logger.error(f"Failed to fetch shipping rate: {exc}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Downstream dependency unavailable or timed out: {str(exc)}"
        )

@app.post("/api/v1/checkout", response_model=CheckoutResponse)
async def process_checkout(payload: CheckoutRequest):
    start_time = time.perf_counter()
    items_subtotal = round(sum(item.price * item.quantity for item in payload.items), 2)

    try:
        # Call downstream shipping dependency via resilience-hardened client
        shipping_result = await shipping_client.get_shipping_rate(
            destination_zip=payload.destination_zip,
            weight_kg=payload.weight_kg
        )
    except Exception as exc:
        logger.error(f"Checkout aborted due to unrecoverable dependency failure: {exc}")
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail=f"Checkout failed: Shipping rate service timed out or unavailable. {str(exc)}"
        )

    shipping_fee = float(shipping_result.get("rate", 0.0))
    total_amount = round(items_subtotal + shipping_fee, 2)
    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    order_status = "CONFIRMED_ESTIMATED_SHIPPING" if shipping_result.get("is_fallback") else "CONFIRMED"

    return CheckoutResponse(
        order_id=payload.order_id,
        status=order_status,
        items_subtotal=items_subtotal,
        shipping_fee=shipping_fee,
        total_amount=total_amount,
        shipping_details=shipping_result,
        processed_at_ms=duration_ms,
        revision=settings.REVISION_ID
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.APP_HOST, port=settings.APP_PORT, reload=False)
