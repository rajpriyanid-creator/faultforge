# SPDX-License-Identifier: MIT
# Copyright (c) 2026 FaultForge Authors

import time
from fastapi import APIRouter, Response, status
from app.config import settings
from app.resilience.metrics import global_metrics
from app.resilience.policy import shipping_circuit_breaker

router = APIRouter()
start_timestamp = time.time()

@router.get("/health")
async def health_check(response: Response):
    """
    Kubernetes / Cloud Run liveness probe.
    Returns 200 OK if service process is healthy and active.
    Includes active uptime and revision identifier.
    """
    response.headers["X-Service-Revision"] = settings.REVISION_ID
    uptime_seconds = round(time.time() - start_timestamp, 2)
    return {
        "status": "healthy",
        "service": settings.SERVICE_NAME,
        "revision": settings.REVISION_ID,
        "uptime_seconds": uptime_seconds,
        "environment": settings.ENVIRONMENT
    }

@router.get("/ready")
async def readiness_check():
    """
    Kubernetes / Cloud Run readiness probe.
    Returns 200 OK if service is prepared to handle live customer traffic.
    """
    circuit_status = shipping_circuit_breaker.get_status()
    is_ready = True
    message = "Service ready to accept traffic"

    # In strict mode, if circuit breaker is OPEN, readiness is degraded but still functional due to fallback
    return {
        "ready": is_ready,
        "message": message,
        "circuit_breaker": circuit_status,
        "revision": settings.REVISION_ID
    }

@router.get("/metrics")
async def get_metrics():
    """
    Structured metrics endpoint reporting real-time request latencies,
    error counts, fallback triggers, and circuit trips.
    """
    summary = global_metrics.get_summary()
    circuit_status = shipping_circuit_breaker.get_status()
    return {
        "service": settings.SERVICE_NAME,
        "revision": settings.REVISION_ID,
        "circuit_breaker": circuit_status,
        "resilience_metrics": summary
    }
