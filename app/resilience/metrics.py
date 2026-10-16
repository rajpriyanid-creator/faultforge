# SPDX-License-Identifier: MIT
# Copyright (c) 2026 FaultForge Authors

import time
import math
from typing import Dict, Any, List

class ResilienceMetrics:
    def __init__(self):
        self.total_requests: int = 0
        self.successful_requests: int = 0
        self.failed_requests: int = 0
        self.fallback_invocations: int = 0
        self.circuit_trips: int = 0
        self.latencies: List[float] = []

    def record_request(self, latency_ms: float, success: bool, used_fallback: bool = False):
        self.total_requests += 1
        if success:
            self.successful_requests += 1
        else:
            self.failed_requests += 1
        if used_fallback:
            self.fallback_invocations += 1
        self.latencies.append(latency_ms)
        # Keep window bounded to last 1000 requests
        if len(self.latencies) > 1000:
            self.latencies.pop(0)

    def record_circuit_trip(self):
        self.circuit_trips += 1

    def get_summary(self) -> Dict[str, Any]:
        if not self.latencies:
            p50 = p95 = p99 = avg = 0.0
        else:
            sorted_lat = sorted(self.latencies)
            n = len(sorted_lat)
            avg = round(sum(sorted_lat) / n, 2)
            p50 = round(sorted_lat[int(n * 0.50)], 2)
            p95 = round(sorted_lat[min(int(n * 0.95), n - 1)], 2)
            p99 = round(sorted_lat[min(int(n * 0.99), n - 1)], 2)

        error_rate = round((self.failed_requests / self.total_requests) * 100, 2) if self.total_requests > 0 else 0.0

        return {
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "error_rate_percent": error_rate,
            "fallback_invocations": self.fallback_invocations,
            "circuit_trips": self.circuit_trips,
            "latency_p50_ms": p50,
            "latency_p95_ms": p95,
            "latency_p99_ms": p99,
            "latency_avg_ms": avg
        }

    def reset(self):
        self.total_requests = 0
        self.successful_requests = 0
        self.failed_requests = 0
        self.fallback_invocations = 0
        self.circuit_trips = 0
        self.latencies.clear()

global_metrics = ResilienceMetrics()
