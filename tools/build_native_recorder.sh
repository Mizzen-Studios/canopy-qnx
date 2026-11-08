#!/bin/bash
set -euo pipefail
: "${CAN_SDP_ENV:?}" "${CAN_BUILD_FILE:?}" "${CAN_BSP_CWD:?}" "${CAN_OUT:?}"
source "$CAN_SDP_ENV"
root=$(cd "$(dirname "$0")/.." && pwd)
mkdir -p "$CAN_OUT"
qcc -Vgcc_ntox86_64 -std=gnu11 -Wall -Wextra -o "$CAN_OUT/incident_recorder" "$root/native/incident_recorder.c" -lslog2
qcc -Vgcc_ntox86_64 -std=gnu11 -o "$CAN_OUT/prereq_containment" "$root/native/prereq_containment.c" -lpthread
cp "$CAN_BUILD_FILE" "$CAN_OUT/incident.build"
printf '\n[type=file perms=0755] incident_recorder=%s/incident_recorder\n[type=file perms=0755] prereq_containment=%s/prereq_containment\n' "$CAN_OUT" "$CAN_OUT" >> "$CAN_OUT/incident.build"
(cd "$CAN_BSP_CWD"; mkifs "$CAN_OUT/incident.build" "$CAN_OUT/incident.ifs")
sha256sum "$root/native/incident_recorder.c" "$root/native/prereq_containment.c" "$CAN_OUT/incident_recorder" "$CAN_OUT/prereq_containment" "$CAN_OUT/incident.build" "$CAN_OUT/incident.ifs"
