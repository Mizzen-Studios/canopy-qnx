#!/bin/bash
set -euo pipefail
printf 'EXISTING_LICENSED_HOST
'
uname -sm
findmnt /boot
findmnt /boot/efi
printf 'SDK_ENV_PRESENT
'
test -f /home/qnx/qnx800/qnxsdp-env.sh
runuser -u qnx -- env HOME=/home/qnx bash /mnt/host/features-can-20261110/build.sh > /mnt/host/features-can-20261110/build.log 2>&1
printf 'CAN_QUERY_BUILD_RC=0
'
