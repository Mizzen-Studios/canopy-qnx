#!/bin/sh
set -eu
cd "$(git rev-parse --show-toplevel)"
exec python3 scripts/check_no_sdk.py
