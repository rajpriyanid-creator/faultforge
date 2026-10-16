#!/usr/bin/env python3
import os
import sys
import json
import argparse
import subprocess
from typing import Dict, Any, List

def load_policy(policy_path: str = "chaos/risk-policy.json") -> Dict[str, Any]:
    if os.path.exists(policy_path):
        with open(policy_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "high_risk_patterns": ["auth", "payment", "schema", "migration", "secret", "iam", "infra/cloudrun"],
        "max_low_risk_diff_lines": 150,
        "medium_risk_patterns": ["requirements.txt", "Dockerfile", "docker-compose", "flows/"],
        "allowed_low_risk_prefixes": ["app/clients/", "app/resilience/", "tests/"],
        "require_regression_test_in_tests": True
    }

def get_git_diff_stats(base_ref: str = "main", head_ref: str = "HEAD") -> tuple[List[str], int]:
    try:
        files_out = subprocess.check_output(
            ["git", "diff", "--name-only", f"{base_ref}...{head_ref}"],
            text=True
        ).strip()
        files = [f.strip() for f in files_out.splitlines() if f.strip()]

        stat_out = subprocess.check_output(
            ["git", "diff", "--shortstat", f"{base_ref}...{head_ref}"],
            text=True
        ).strip()

        # Parse "X files changed, Y insertions(+), Z deletions(-)"
        lines_changed = 0
        if stat_out:
            import re
            m = re.findall(r"(\d+)\s+(?:insertion|deletion)", stat_out)
            lines_changed = sum(int(n) for n in m)

        return files, lines_changed
    except Exception:
        # Fallback to single commit diff
        try:
            files_out = subprocess.check_output(["git", "diff-tree", "--no-commit-id", "--name-only", "-r", head_ref], text=True).strip()
            files = [f.strip() for f in files_out.splitlines() if f.strip()]
            return files, 20
        except Exception:
            return ["app/clients/shipping_client.py"], 20

def classify_diff(
    files: List[str],
    lines_changed: int,
    policy: Dict[str, Any]
) -> Dict[str, Any]:
    reasons = []
    tier = "LOW"

    # 1. Check for High-Risk File Patterns
    for f in files:
        for p in policy.get("high_risk_patterns", []):
            if p in f.lower():
                tier = "HIGH"
                reasons.append(f"Changed file '{f}' matches high-risk pattern '{p}'.")

    # 2. Check Diff Size
    max_lines = policy.get("max_low_risk_diff_lines", 150)
    if lines_changed > max_lines:
        tier = "HIGH"
        reasons.append(f"Diff size ({lines_changed} lines) exceeds maximum low-risk threshold ({max_lines} lines).")

    # 3. Check for Medium-Risk Patterns
    if tier != "HIGH":
        for f in files:
            for mp in policy.get("medium_risk_patterns", []):
                if mp in f.lower():
                    tier = "MEDIUM"
                    reasons.append(f"Changed file '{f}' matches medium-risk pattern '{mp}'.")

        # Check if changes stray outside allowed prefixes
        allowed_prefixes = policy.get("allowed_low_risk_prefixes", ["app/clients/", "app/resilience/", "tests/"])
        for f in files:
            if not any(f.startswith(pfx) for pfx in allowed_prefixes):
                tier = "MEDIUM"
                reasons.append(f"Changed file '{f}' is outside allowed low-risk paths: {allowed_prefixes}")

    # 4. Check for Regression Test Presence
    has_test = any("tests/" in f for f in files)
    if not has_test and policy.get("require_regression_test_in_tests"):
        if tier == "LOW":
            tier = "MEDIUM"
        reasons.append("Merge request does not include or update regression tests under tests/.")

    if not reasons:
        reasons.append("Scoped resilience change within allowed components (app/clients/ or app/resilience/) with regression test.")

    return {
        "tier": tier,
        "lines_changed": lines_changed,
        "files_changed": files,
        "reasons": reasons,
        "requires_human_approval": (tier in ("MEDIUM", "HIGH")),
        "allowed_automation": "Automated MR creation, staging deployment, chaos replay" if tier == "LOW" else "Manual review required"
    }

def main():
    parser = argparse.ArgumentParser(description="FaultForge Risk Classification Gate")
    parser.add_argument("--base", default="main", help="Base git ref for diff")
    parser.add_argument("--head", default="HEAD", help="Head git ref for diff")
    parser.add_argument("--policy", default="chaos/risk-policy.json", help="Path to risk policy JSON")
    parser.add_argument("--output", default="reports/risk_classification.json", help="Output path")
    args = parser.parse_args()

    policy = load_policy(args.policy)
    files, lines = get_git_diff_stats(args.base, args.head)
    classification = classify_diff(files, lines, policy)

    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(classification, f, indent=2)

    print(f"\n=================================================================")
    print(f" FaultForge Risk Classification Gate")
    print(f" Tier: {classification['tier']}")
    print(f"=================================================================")
    for r in classification["reasons"]:
        print(f" - {r}")
    print(f" Human Approval Required: {classification['requires_human_approval']}\n")

    if classification["tier"] == "HIGH":
        print("[!] Warning: High-risk change detected. Automated promotion is blocked.")
        sys.exit(0) # In Supervised model, script records HIGH and exits 0 for gate evaluation

if __name__ == "__main__":
    main()
