#!/bin/bash
set -euo pipefail
export HOME=/home/qnx
export CAN_SDP_ENV=/home/qnx/qnx800/qnxsdp-env.sh
export CAN_BUILD_FILE=/home/qnx/qnx-work/edu-followup10/ifs.slm.build
export CAN_BSP_CWD=/home/qnx/qnx-work/can-gate
export CAN_OUT=/mnt/host/features-can-20261110/out
mkdir -p "$CAN_OUT"
sha256sum "$CAN_BUILD_FILE" > "$CAN_OUT/base-build.sha256"
bash /mnt/host/features-can-20261110/repo/tools/build_native_recorder.sh
