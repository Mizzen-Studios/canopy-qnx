#!/bin/bash
set -euo pipefail
: "${CAN_SDP_ENV:?}" "${CAN_BUILD_FILE:?}" "${CAN_BSP_CWD:?}" "${CAN_OUT:?}"
source "$CAN_SDP_ENV"
root=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$CAN_OUT"
export MAKEFLAGS="4{MAKEFLAGS:-} -j1"
stage() {
 echo "CAN_BUILD_STAGE_BEGIN=$1"; shift
 free -k
 set +e
 "$@"
 rc=$?
 set -e
 echo "CAN_BUILD_STAGE_RC=$rc"
 free -k
 return "$rc"
}
stage incident_recorder qcc -Vgcc_ntox86_64 -std=gnu11 -Wall -Wextra -o "$CAN_OUT/incident_recorder" "$root/native/incident_recorder.c" -lslog2
stage prereq_containment qcc -Vgcc_ntox86_64 -std=gnu11 -o "$CAN_OUT/prereq_containment" "$root/native/prereq_containment.c"
stage guest_query qcc -Vgcc_ntox86_64 -std=gnu11 -Wall -Wextra -o "$CAN_OUT/guest_query" "$root/native/guest_query.c"
cp "$CAN_BUILD_FILE" "$CAN_OUT/incident.build"
printf '\n[type=file perms=0755] incident_recorder=%s/incident_recorder\n[type=file perms=0755] prereq_containment=%s/prereq_containment\n' "$CAN_OUT" "$CAN_OUT" >> "$CAN_OUT/incident.build"
echo "[type=file perms=0755] guest_query=$CAN_OUT/guest_query" >> "$CAN_OUT/incident.build"
(cd "$CAN_BSP_CWD"; stage mkifs mkifs "$CAN_OUT/incident.build" "$CAN_OUT/incident.ifs")
test -s "$CAN_OUT/incident.ifs"
sha256sum "$root/native/guest_query.c" "$CAN_OUT/guest_query" "$root/native/incident_recorder.c" "$root/native/prereq_containment.c" "$CAN_OUT/incident_recorder" "$CAN_OUT/prereq_containment" "$CAN_OUT/incident.build" "$CAN_OUT/incident.ifs"
