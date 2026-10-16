#!/usr/bin/env python3
import os
import sys
import ast

def inspect_client_ast(file_path: str = "app/clients/shipping_client.py") -> int:
    """
    Deterministic bisect probe for git bisect run.
    Exit codes for git bisect:
      0: Current commit is GOOD (resilient: has timeout and fallback)
      1: Current commit is BAD (fragile: missing timeout or fallback)
      125: Commit cannot be tested (skip)
    """
    if not os.path.exists(file_path):
        return 125

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            source = f.read()
        tree = ast.parse(source)
    except Exception:
        return 125

    has_timeout = False
    has_fallback = False

    # AST inspection: look for httpx.AsyncClient call with timeout keyword argument
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            # Check for timeout argument in httpx call
            for kw in node.keywords:
                if kw.arg == "timeout":
                    has_timeout = True
        # Check for fallback function reference or call
        if isinstance(node, ast.Name) and "fallback" in node.id.lower():
            has_fallback = True
        elif isinstance(node, ast.Attribute) and "fallback" in node.attr.lower():
            has_fallback = True

    if has_timeout and has_fallback:
        print(f"[+] Probe: GOOD commit (bounded timeout and fallback detected)")
        return 0
    else:
        print(f"[-] Probe: BAD commit (missing bounded timeout or fallback)")
        return 1

if __name__ == "__main__":
    target_file = sys.argv[1] if len(sys.argv) > 1 else "app/clients/shipping_client.py"
    exit_code = inspect_client_ast(target_file)
    sys.exit(exit_code)
