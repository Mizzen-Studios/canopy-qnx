#!/bin/bash
set -euo pipefail
BASE=/mnt/host/features-can-retry-20261110
exec > "$BASE/diagnostic.log" 2>&1
snapshot() { date -u; free -k; ps -eo pid,ppid,comm,rss,args --sort=-rss | awk 'NR<=21'; }
snapshot
# Allow first-boot work to settle; no permanent service configuration edits.
for n in $(seq 1 90); do
 test -f /var/lib/cloud/instance/boot-finished && break
 sleep 2
done
if ! test -f /var/lib/cloud/instance/boot-finished; then echo CLOUD_INIT_NOT_FINISHED; exit 70; fi
stopped=""
cleanup() {
 rc=$?
 test -z "${monitor:-}" || { kill "$monitor" 2>/dev/null || true; wait "$monitor" 2>/dev/null || true; }
 for unit in $stopped; do systemctl start "$unit" || true; done
 echo RESTORED_UNITS="$stopped"; echo RETRY_RC=$rc
 exit "$rc"
}
trap cleanup EXIT
for unit in snapd.socket snapd.service apport.service fwupd.service udisks2.service packagekit.service; do
 echo INSPECT_UNIT="$unit"
 systemctl show "$unit" -p ActiveState -p MainPID -p MemoryCurrent || true
 if systemctl is-active --quiet "$unit"; then systemctl stop "$unit"; stopped="$unit $stopped"; fi
done
snapshot
(while :; do snapshot; sleep 2; done) > "$BASE/memory-samples.log" 2>&1 & monitor=$!
runuser -u qnx -- env HOME=/home/qnx CAN_SDP_ENV=/home/qnx/qnx800/qnxsdp-env.sh CAN_BUILD_FILE=/home/qnx/qnx-work/edu-followup10/ifs.slm.build CAN_BSP_CWD=/home/qnx/qnx-work/can-gate CAN_OUT="$BASE/out" bash "$BASE/repo/tools/build_native_recorder.sh" > "$BASE/build.log" 2>&1
snapshot
