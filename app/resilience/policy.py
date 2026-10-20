# SPDX-License-Identifier: MIT
# Copyright (c) 2026 FaultForge Authors

import time
import random
import logging
from enum import Enum
from typing import Callable, Any, Dict, Optional
from app.config import settings
from app.resilience.metrics import global_metrics

logger = logging.getLogger("faultforge.resilience")

class CircuitState(str, Enum):
    CLOSED = "CLOSED"
    OPEN = "OPEN"
    HALF_OPEN = "HALF_OPEN"

class CircuitBreakerOpenException(Exception):
    """Raised when request is rejected because circuit breaker is in OPEN state."""
    pass

class CircuitBreaker:
    def __init__(self, fail_max: int = 3, reset_timeout: float = 10.0):
        self.fail_max = fail_max
        self.reset_timeout = reset_timeout
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.last_state_change = time.time()

    def can_execute(self) -> bool:
        if self.state == CircuitState.CLOSED:
            return True
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_failure_time >= self.reset_timeout:
                logger.info("Circuit breaker transitioning from OPEN to HALF_OPEN")
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
                return True
            return False
        # HALF_OPEN allows a trial request
        return True

    def reset(self):
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0

    def record_success(self):
        if self.state in (CircuitState.HALF_OPEN, CircuitState.OPEN):
            logger.info("Circuit breaker probe succeeded, transitioning to CLOSED")
        self.state = CircuitState.CLOSED
        self.failure_count = 0

    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.fail_max or self.state == CircuitState.HALF_OPEN:
            if self.state != CircuitState.OPEN:
                logger.warning(
                    f"Circuit breaker tripped to OPEN! Failures: {self.failure_count}/{self.fail_max}"
                )
                global_metrics.record_circuit_trip()
            self.state = CircuitState.OPEN
            self.last_state_change = self.last_failure_time

    def get_status(self) -> Dict[str, Any]:
        return {
            "state": self.state.value,
            "failure_count": self.failure_count,
            "fail_max": self.fail_max,
            "reset_timeout_seconds": self.reset_timeout,
            "seconds_since_last_failure": round(time.time() - self.last_failure_time, 2) if self.last_failure_time > 0 else None
        }

# Global circuit breaker instance for shipping dependency
shipping_circuit_breaker = CircuitBreaker(
    fail_max=settings.CIRCUIT_BREAKER_FAIL_MAX,
    reset_timeout=settings.CIRCUIT_BREAKER_RESET_TIMEOUT
)

def get_graceful_shipping_fallback(destination_zip: str, weight_kg: float, reason: str) -> Dict[str, Any]:
    """
    Generates a deterministic, safe fallback rate estimate when the external dependency
    is degraded, timed out, or circuit-broken.
    """
    # Deterministic standard calculation: Base flat fee $7.50 + $1.25 per kg
    estimated_rate = round(7.50 + (weight_kg * 1.25), 2)
    return {
        "carrier": "Standard Delivery (Fallback Estimate)",
        "service_level": "standard",
        "rate": estimated_rate,
        "currency": "USD",
        "estimated_days": 4,
        "is_fallback": True,
        "is_estimate": True,
        "fallback_reason": reason
    }
