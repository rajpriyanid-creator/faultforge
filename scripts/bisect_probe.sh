#!/usr/bin/env bash
# SPDX-License-Identifier: MIT
# Bisect probe wrapper for git bisect run
python3 scripts/bisect_probe.py "$@"
exit $?
