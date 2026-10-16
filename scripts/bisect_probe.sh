#!/usr/bin/env bash
# Bisect probe wrapper for git bisect run
python3 scripts/bisect_probe.py "$@"
exit $?
