#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

echo "=== Building FaultForge Submission Archive ==="
python3 "${REPO_ROOT}/scripts/build_submission_zip.py" "${1:-faultforge-submission.zip}"
