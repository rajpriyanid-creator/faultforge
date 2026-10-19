# SPDX-License-Identifier: MIT
import time
import pytest
from app.resilience.policy import (
    CircuitBreaker,
    CircuitState,
    get_graceful_shipping_fallback
)

def test_circuit_breaker_initial_state():
    cb = CircuitBreaker(fail_max=3, reset_timeout=1.0)
    assert cb.state == CircuitState.CLOSED
    assert cb.can_execute() is True

def test_circuit_breaker_trips_to_open_after_max_failures():
    cb = CircuitBreaker(fail_max=3, reset_timeout=1.0)
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.CLOSED
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

def test_circuit_breaker_transitions_to_half_open_after_timeout():
    cb = CircuitBreaker(fail_max=2, reset_timeout=0.1)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    assert cb.can_execute() is False

    time.sleep(0.15)
    assert cb.can_execute() is True
    assert cb.state == CircuitState.HALF_OPEN

def test_circuit_breaker_recovers_to_closed_on_success():
    cb = CircuitBreaker(fail_max=2, reset_timeout=0.1)
    cb.record_failure()
    cb.record_failure()
    assert cb.state == CircuitState.OPEN
    time.sleep(0.15)
    assert cb.can_execute() is True # Transitions to HALF_OPEN
    cb.record_success()
    assert cb.state == CircuitState.CLOSED
    assert cb.failure_count == 0

def test_get_graceful_shipping_fallback_deterministic():
    fallback = get_graceful_shipping_fallback(destination_zip="94103", weight_kg=2.0, reason="Test Timeout")
    assert fallback["is_fallback"] is True
    assert fallback["is_estimate"] is True
    assert fallback["rate"] == 10.00  # 7.50 + (2.0 * 1.25)
    assert fallback["currency"] == "USD"
    assert fallback["fallback_reason"] == "Test Timeout"
