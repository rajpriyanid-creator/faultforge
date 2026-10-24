#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge Clean Submission Archive Packager & Verification.
Creates a clean, reproducible submission zip without git history, binaries,
temporary caches, or unverified reports. Runs a strict secret scan over the archive.
"""
import os
import re
import sys
import zipfile
import hashlib
from typing import List, Tuple

FORBIDDEN_SECRET_PATTERNS = [
    re.compile(r"glpat-[0-9a-zA-Z\-_]{20,}", re.IGNORECASE),
    re.compile(r"ghp_[0-9a-zA-Z]{36}", re.IGNORECASE),
    re.compile(r"-----BEGIN (?:RSA |EC )?PRIVATE KEY-----"),
    re.compile(r'"private_key":\s*"-----BEGIN')
]

EXCLUDE_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".cache",
    "bin",
    ".idea",
    ".vscode",
    ".system_generated",
    "node_modules",
    "venv",
    ".venv"
}

def should_exclude(rel_path: str) -> bool:
    normalized = rel_path.replace("\\", "/")
    parts = normalized.split("/")

    # Exclude forbidden directories
    if any(p in EXCLUDE_DIRS for p in parts):
        return True

    # Exclude binaries, sqlite databases, caches, and test coverage artifacts
    binary_and_cache_exts = [
        ".exe", ".pyc", ".pyo", ".tmp", ".log", ".zip",
        ".db", ".sqlite", ".sqlite3", ".bin", ".dat", ".so", ".dll", ".dylib"
    ]
    if any(normalized.endswith(ext) for ext in binary_and_cache_exts):
        return True

    # Exclude coverage database and report files
    if any(p.startswith(".coverage") for p in parts):
        return True

    # Exclude secrets
    if any(p.startswith(".env") for p in parts) or any(normalized.endswith(ext) for ext in [".key", ".pem"]):
        return True

    # Exclude local/CI reports except documentation and gitkeep
    if parts[0] == "reports" and len(parts) > 1:
        if parts[1] not in (".gitkeep", "README.md"):
            return True

    return False

def scan_file_for_secrets(content_bytes: bytes, file_name: str) -> List[str]:
    violations = []
    try:
        text = content_bytes.decode("utf-8", errors="ignore")
        for pat in FORBIDDEN_SECRET_PATTERNS:
            if pat.search(text):
                violations.append(f"Secret pattern matched in {file_name}: {pat.pattern}")
    except Exception:
        pass
    return violations

def build_submission_zip(source_dir: str = ".", output_zip: str = "faultforge-submission.zip") -> Tuple[str, int, str]:
    abs_source = os.path.abspath(source_dir)
    abs_output = os.path.abspath(output_zip)

    print(f"[*] Building clean submission archive from: {abs_source}")
    print(f"[*] Target archive: {abs_output}")

    files_added = 0
    all_violations = []

    with zipfile.ZipFile(abs_output, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(abs_source):
            for file in files:
                full_path = os.path.join(root, file)
                rel_path = os.path.relpath(full_path, abs_source)

                if should_exclude(rel_path):
                    continue

                # Secret scan
                with open(full_path, "rb") as f:
                    content = f.read()

                violations = scan_file_for_secrets(content, rel_path)
                if violations:
                    all_violations.extend(violations)

                zf.write(full_path, arcname=rel_path)
                files_added += 1

    if all_violations:
        print("[-] FATAL: Secret scan failed with violations in archive files:", file=sys.stderr)
        for v in all_violations:
            print(f"    - {v}", file=sys.stderr)
        os.remove(abs_output)
        sys.exit(1)

    file_size = os.path.getsize(abs_output)
    hasher = hashlib.sha256()
    with open(abs_output, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    zip_sha = hasher.hexdigest()

    print(f"\n=================================================================")
    print(f" FaultForge Clean Submission Archive")
    print(f"=================================================================")
    print(f" Output:     {abs_output}")
    print(f" Files:      {files_added} files packed")
    print(f" Size:       {file_size / (1024 * 1024):.2f} MB ({file_size:,} bytes)")
    print(f" SHA-256:    {zip_sha}")
    print(f" Secret Scan: 0 violations (PASS)")
    print(f"=================================================================\n")

    return abs_output, file_size, zip_sha

if __name__ == "__main__":
    out_name = sys.argv[1] if len(sys.argv) > 1 else "faultforge-submission.zip"
    build_submission_zip(".", out_name)
