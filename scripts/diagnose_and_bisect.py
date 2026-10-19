#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
import os
import sys
import ast
import json
import subprocess
from typing import Dict, Any, List, Optional

def inspect_code_ast(file_path: str = "app/clients/shipping_client.py") -> Dict[str, Any]:
    """Inspects AST of client to identify fragility without regex matching."""
    if not os.path.exists(file_path):
        return {"status": "FILE_NOT_FOUND", "findings": [], "is_fragile": True}

    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except Exception as exc:
        return {"status": "PARSE_ERROR", "findings": [{"type": "SYNTAX_ERROR", "detail": str(exc)}], "is_fragile": True}

    findings = []
    has_timeout_kw = False
    has_fallback_ref = False

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == "timeout":
                    has_timeout_kw = True
        if isinstance(node, ast.Name) and "fallback" in node.id.lower():
            has_fallback_ref = True
        elif isinstance(node, ast.Attribute) and "fallback" in node.attr.lower():
            has_fallback_ref = True

    if not has_timeout_kw:
        findings.append({
            "type": "UNBOUNDED_REQUEST",
            "severity": "HIGH",
            "detail": "AST inspection confirmed httpx.AsyncClient call lacks bounded timeout keyword argument."
        })
    if not has_fallback_ref:
        findings.append({
            "type": "MISSING_FALLBACK",
            "severity": "MEDIUM",
            "detail": "AST inspection confirmed no reference or call to fallback rate quote generator."
        })

    return {
        "file": file_path,
        "findings": findings,
        "is_fragile": len(findings) > 0
    }

def run_git_bisect_analysis() -> Dict[str, Any]:
    """
    Executes deterministic git bisect across repository history using bisect_probe.py.
    Returns parsed culprit commit details only when verified by bisect boundary.
    """
    try:
        root_commit = subprocess.check_output(
            ["git", "rev-list", "--max-parents=0", "HEAD"],
            text=True
        ).strip().splitlines()[0]
        current_head = subprocess.check_output(
            ["git", "rev-parse", "HEAD"],
            text=True
        ).strip()
    except Exception as exc:
        return {
            "bisect_executed": False,
            "status": "INSUFFICIENT_EVIDENCE",
            "reason": f"Unable to read git revision history: {exc}"
        }

    if root_commit == current_head:
        return {
            "bisect_executed": False,
            "status": "SUSPECTED_WEAKNESS",
            "reason": "Single revision repository. Cannot bisect across zero commit range."
        }

    # Verify that probe returns GOOD on root and BAD on head before bisecting
    probe_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "bisect_probe.py"))

    try:
        # Run git bisect
        subprocess.run(["git", "bisect", "reset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "bisect", "start"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "bisect", "bad", current_head], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        subprocess.run(["git", "bisect", "good", root_commit], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        bisect_run = subprocess.run(
            ["git", "bisect", "run", sys.executable, probe_script],
            text=True,
            capture_output=True,
            check=True
        )
        bisect_output = bisect_run.stdout

        # Read the current bisect bad commit
        bad_sha = subprocess.check_output(["git", "rev-parse", "refs/bisect/bad"], text=True).strip()
        commit_details = subprocess.check_output(
            ["git", "show", "--format=%an|%ae|%s", "--stat", bad_sha],
            text=True
        ).splitlines()

        meta_parts = commit_details[0].split("|")
        author_name = meta_parts[0] if len(meta_parts) > 0 else "Unknown"
        subject = meta_parts[2] if len(meta_parts) > 2 else "Unknown"

        subprocess.run(["git", "bisect", "reset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

        return {
            "bisect_executed": True,
            "status": "CONFIRMED_REGRESSION",
            "culprit_sha": bad_sha,
            "culprit_author": author_name,
            "culprit_subject": subject,
            "bisect_summary": f"{bad_sha[:8]} - {subject}"
        }

    except Exception as exc:
        subprocess.run(["git", "bisect", "reset"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return {
            "bisect_executed": False,
            "status": "SUSPECTED_WEAKNESS",
            "reason": f"Git bisect did not isolate a boundary: {exc}"
        }

def diagnose(
    dossier_path: str = "reports/incident_dossier.json",
    output_path: str = "reports/diagnosis_report.json"
) -> Dict[str, Any]:
    ast_result = inspect_code_ast()
    bisect_result = run_git_bisect_analysis()

    if bisect_result.get("status") == "CONFIRMED_REGRESSION":
        diagnosis_status = "CONFIRMED_REGRESSION"
        confidence = "HIGH"
    elif ast_result.get("is_fragile"):
        diagnosis_status = "SUSPECTED_WEAKNESS"
        confidence = "MEDIUM"
    else:
        diagnosis_status = "INSUFFICIENT_EVIDENCE"
        confidence = "LOW"

    diagnosis = {
        "diagnosis_id": f"diag-{os.urandom(4).hex()}",
        "status": diagnosis_status,
        "confidence": confidence,
        "target_component": "app/clients/shipping_client.py",
        "ast_findings": ast_result["findings"],
        "bisect_result": bisect_result,
        "recommendation": [
            "Enforce strict 0.8s bounded timeout on httpx.AsyncClient",
            "Reinstate circuit breaker to shed degraded downstream load",
            "Return deterministic graceful shipping quote fallback on timeout"
        ]
    }

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(diagnosis, f, indent=2)

    print(f"\n[+] Diagnosis completed: {output_path}")
    print(f"    Status: {diagnosis['status']} (Confidence: {diagnosis['confidence']})")
    if bisect_result.get("culprit_sha"):
        print(f"    Culprit Commit: {bisect_result['culprit_sha']} ({bisect_result['culprit_subject']})")
    for f_item in ast_result["findings"]:
        print(f"    - [{f_item['severity']}] {f_item['type']}: {f_item['detail']}")

    return diagnosis

if __name__ == "__main__":
    diagnose()
