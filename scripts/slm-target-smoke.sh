#!/bin/sh
# Original target-only parser/readiness smoke; does NOT kill any process.
# Explicit opt-in and isolated fresh image required. NOT full C3 acceptance.
set -eu
[ "${CANOPY_SLM_FRESH_IMAGE:-}" = YES ] || {
    echo 'Refusing: require fresh isolated SLM image and explicit opt-in' >&2
    exit 2
}
SLM=/proc/boot/slm
CTL=/proc/boot/slmctl
CONFIG=/proc/boot/slm-can-fallback.xml
ENDPOINT=/dev/slm-canopy
for f in "$SLM" "$CTL"; do
    [ -x "$f" ] || { echo "Missing executable: $f" >&2; exit 2; }
done
[ -r "$CONFIG" ] || { echo 'Missing config' >&2; exit 2; }
[ ! -e "$ENDPOINT" ] || { echo 'Refusing existing SLM endpoint' >&2; exit 2; }
[ ! -e /dev/can0/rx0 ] || { echo 'Refusing already-owned CAN device' >&2; exit 2; }
echo CANOPY_SLM_SMOKE_BEGIN
# slogger2 must already run in the prepared image; preserve its ownership.
pidin ar
"$SLM" -V -n "$ENDPOINT" -R 5/min -s canopy-can "$CONFIG" > /tmp/canopy-slm.log 2>&1 &
SLM_LAUNCH_PID=$!
echo "CANOPY_SLM_LAUNCH_PID=$SLM_LAUNCH_PID"
# SLM startup child may daemonize: this PID is diagnostic, never a kill target.
if ! waitfor "$ENDPOINT" 15; then
    cat /tmp/canopy-slm.log
    echo CANOPY_SLM_ENDPOINT_FAIL >&2
    exit 1
fi
"$CTL" -n "$ENDPOINT" 'listall -v'
if ! waitfor /dev/can0/rx0 15; then
    cat /tmp/canopy-slm.log
    echo CANOPY_SLM_CAN_READY_FAIL >&2
    exit 1
fi
"$CTL" -n "$ENDPOINT" 'active -v'
pidin ar
cat /tmp/canopy-slm.log
echo 'CANOPY_SLM_SMOKE_READY: parser/node only; NOT restart/traffic/SSH proof'
# Leave SLM/driver running for lease owner identity inspection. Stop ONLY the
# managed component via slmctl -n /dev/slm-canopy 'stop canopy-can', then wait
# for confirmed inactive state. No name kill or stale PID cleanup here.
