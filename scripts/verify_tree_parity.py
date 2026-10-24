#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
FaultForge Replay-to-Deploy Tree Parity Gate
Verifies that the app/ tree SHA evaluated during replay exactly matches
the app/ tree SHA built into the container and deployed to Cloud Run.
"""
import os
import sys
import argparse
import subprocess

def get_tree_sha(ref_or_file: str) -> str:
    """
    Resolve tree SHA either by reading a reports file or running git rev-parse.
    """
    if os.path.exists(ref_or_file) and os.path.isfile(ref_or_file):
        with open(ref_or_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if len(content) == 40 and all(c in "0123456789abcdefABCDEF" for c in content):
                return content
        return ""
    if "/" in ref_or_file or "\\" in ref_or_file or ref_or_file.endswith(".txt"):
        return ""
    try:
        out = subprocess.check_output(
            ["git", "rev-parse", ref_or_file],
            text=True,
            stderr=subprocess.DEVNULL
        ).strip()
        if len(out) == 40 and all(c in "0123456789abcdefABCDEF" for c in out):
            return out
    except Exception:
        pass
    return ""

def verify_tree_parity(
    replay_tree_path: str = "reports/replay_tree_sha.txt",
    deployed_tree_path: str = "reports/deployed_tree_sha.txt",
    fail_on_mismatch: bool = True
) -> bool:
    print("\n=================================================================")
    print(" FaultForge Replay-to-Deploy App Tree Parity Gate")
    print("=================================================================")

    replay_sha = get_tree_sha(replay_tree_path)
    if not replay_sha and replay_tree_path == "reports/replay_tree_sha.txt":
        replay_sha = get_tree_sha("HEAD:app")

    deployed_sha = get_tree_sha(deployed_tree_path)
    if not deployed_sha and deployed_tree_path == "reports/deployed_tree_sha.txt":
        deployed_sha = get_tree_sha("HEAD:app")

    print(f"[*] Replay app/ Tree SHA:   {replay_sha or 'NOT_FOUND'}")
    print(f"[*] Deployed app/ Tree SHA: {deployed_sha or 'NOT_FOUND'}")

    if not replay_sha or not deployed_sha:
        msg = "[-] Tree Parity Gate Error: Unable to determine replay or deployed app tree SHA."
        print(msg, file=sys.stderr)
        if fail_on_mismatch:
            sys.exit(1)
        return False

    if replay_sha != deployed_sha:
        msg = (
            f"[-] Tree Parity Gate FAILED: Replay tree ({replay_sha}) does NOT match "
            f"deployed tree ({deployed_sha})!"
        )
        print(msg, file=sys.stderr)
        if fail_on_mismatch:
            sys.exit(1)
        return False

    print(f"[+] Tree Parity Gate PASSED: exact app/ tree match verified ({replay_sha}).\n")
    return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Verify app/ tree parity between replay and deploy")
    parser.add_argument("--replay-tree", default="reports/replay_tree_sha.txt", help="Path to replay tree SHA file")
    parser.add_argument("--deployed-tree", default="reports/deployed_tree_sha.txt", help="Path to deployed tree SHA file")
    parser.add_argument("--fail-on-mismatch", action="store_true", default=True, help="Exit with non-zero code on mismatch")
    args = parser.parse_args()

    ok = verify_tree_parity(
        replay_tree_path=args.replay_tree,
        deployed_tree_path=args.deployed_tree,
        fail_on_mismatch=args.fail_on_mismatch
    )
    sys.exit(0 if ok else 1)
