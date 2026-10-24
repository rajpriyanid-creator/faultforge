#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
Verify baseline-v0.1.0 tag integrity.
Confirms:
- baseline-v0.1.0 is an annotated git tag
- Annotated tag object SHA matches pinned 578689ad048f3bfdff9754dcd391e33c5f73b38e
- Peeled target commit matches pinned 4ec3a5ad7fd0cc635d9546acf6974b83f7a57054
"""
import sys
import subprocess

PINNED_TAG_OBJECT_SHA = "578689ad048f3bfdff9754dcd391e33c5f73b38e"
PINNED_TAG_COMMIT_SHA = "4ec3a5ad7fd0cc635d9546acf6974b83f7a57054"

def verify_baseline_tag() -> bool:
    try:
        tag_type = subprocess.check_output(
            ["git", "cat-file", "-t", "baseline-v0.1.0"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if tag_type != "tag":
            print(f"[-] Error: baseline-v0.1.0 is type '{tag_type}', expected 'tag'", file=sys.stderr)
            return False

        tag_obj = subprocess.check_output(
            ["git", "rev-parse", "baseline-v0.1.0"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if tag_obj != PINNED_TAG_OBJECT_SHA:
            print(f"[-] Error: baseline-v0.1.0 tag object '{tag_obj}' != pinned '{PINNED_TAG_OBJECT_SHA}'", file=sys.stderr)
            return False

        commit_sha = subprocess.check_output(
            ["git", "rev-parse", "baseline-v0.1.0^{commit}"],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        if commit_sha != PINNED_TAG_COMMIT_SHA:
            print(f"[-] Error: baseline-v0.1.0 target commit '{commit_sha}' != pinned '{PINNED_TAG_COMMIT_SHA}'", file=sys.stderr)
            return False

        print(f"[+] baseline-v0.1.0 verified: tag object {tag_obj[:8]} -> commit {commit_sha[:8]}")
        return True
    except Exception as e:
        print(f"[-] Error verifying baseline-v0.1.0: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    if not verify_baseline_tag():
        sys.exit(1)
