#!/bin/sh
# Native target only: no uncapped fallback. SDK guests need their separate cap.
set -eu
[ "$#" -gt 0 ] || exit 2
exec systemd-run --user --scope --quiet -p CPUQuota=100% -p MemoryMax=1G nice -n 15 "$@"
