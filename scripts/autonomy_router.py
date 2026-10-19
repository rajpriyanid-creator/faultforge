#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge Autonomy Router
Routes proposed software changes to the appropriate autonomy tier:
- low risk (config, timeout, retry) -> auto-apply
- medium risk (dependency bump) -> supervised
- high risk (schema, auth) -> assisted
"""
import os
import sys
import json
import argparse
from typing import List, Dict, Any

HIGH_RISK_PATTERNS = ["auth", "payment", "schema", "migration", "secret", "iam"]
MEDIUM_RISK_PATTERNS = ["requirements.txt", "dockerfile", "docker-compose", "package.json"]
ALLOWED_LOW_RISK_PATHS = ["app/clients/", "app/resilience/", "tests/"]
MAX_LOW_RISK_LINES = 150

def route_change(files: List[str], lines_changed: int = 20) -> Dict[str, Any]:
    """
    Evaluates changed files and diff size to assign the appropriate autonomy route:
    - low risk (config, timeout, retry) -> auto-apply
    - medium risk (dependency bump) -> supervised
    - high risk (schema, auth) -> assisted
    """
    # 1. High Risk Check (schema, auth, payment, secret, or excessive diff)
    for f in files:
        f_lower = f.lower()
        for p in HIGH_RISK_PATTERNS:
            if p in f_lower:
                return {
                    "tier": "HIGH",
                    "route": "assisted",
                    "reason": f"File '{f}' matches high-risk pattern '{p}'. Human approval required for all actions.",
                    "requires_approval_at_each_step": True
                }

    if lines_changed > MAX_LOW_RISK_LINES:
        return {
            "tier": "HIGH",
            "route": "assisted",
            "reason": f"Diff size ({lines_changed} lines) exceeds low-risk threshold ({MAX_LOW_RISK_LINES}).",
            "requires_approval_at_each_step": True
        }

    # 2. Medium Risk Check (dependency bump, Dockerfile, etc.)
    for f in files:
        f_lower = f.lower()
        for p in MEDIUM_RISK_PATTERNS:
            if p in f_lower:
                return {
                    "tier": "MEDIUM",
                    "route": "supervised",
                    "reason": f"File '{f}' matches dependency/build pattern '{p}'. Autonomous staging; human sign-off for production.",
                    "requires_approval_at_each_step": False
                }

    for f in files:
        if not any(f.startswith(pfx) for pfx in ALLOWED_LOW_RISK_PATHS):
            return {
                "tier": "MEDIUM",
                "route": "supervised",
                "reason": f"File '{f}' is outside allowed low-risk components.",
                "requires_approval_at_each_step": False
            }

    # 3. Low Risk (config, timeout, retry within allowed resilience components)
    return {
        "tier": "LOW",
        "route": "auto-apply",
        "reason": "Scoped resilience change within allowed components with bounded timeout/fallback.",
        "requires_approval_at_each_step": False
    }

def main():
    parser = argparse.ArgumentParser(description="FaultForge Autonomy Router")
    parser.add_argument("--files", nargs="+", default=["app/clients/shipping_client.py"], help="Changed files")
    parser.add_argument("--lines", type=int, default=25, help="Number of lines changed")
    parser.add_argument("--output", default="reports/autonomy_route.json", help="Output path")
    args = parser.parse_args()

    decision = route_change(args.files, args.lines)
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(decision, f, indent=2)

    print(f"[Autonomy Router] Tier: {decision['tier']} -> Route: {decision['route'].upper()}")
    print(f"Reason: {decision['reason']}")

if __name__ == "__main__":
    main()
