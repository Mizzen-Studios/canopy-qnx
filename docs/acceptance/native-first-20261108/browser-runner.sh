#!/bin/bash
set -u
W=/home/ubuntu/.openclaw/workspace
S=$W/.openclaw/tmp/final-upgrade-independent
systemd-run --user --quiet --wait --pipe -p MemoryMax=1G -p CPUQuota=100% -p TasksMax=200 -p RuntimeMaxSec=110 -p LimitFSIZE=33554432 timeout 100 bwrap --die-with-parent --unshare-net --unshare-pid --ro-bind /usr /usr --ro-bind /lib /lib --ro-bind /bin /bin --ro-bind /etc /etc --proc /proc --dev /dev --ro-bind "$W/apps" /target/apps --ro-bind "$W/node_modules" /target/node_modules --ro-bind /home/ubuntu/.cache/ms-playwright /browsers --bind "$S" /scratch --dir /tmp --bind "$S/tmp" /tmp --bind "$S/can-openclaw" /target/apps/canopy-qnx/.openclaw --clearenv --setenv PATH /usr/bin:/bin --setenv HOME /scratch/home --setenv TMPDIR /scratch/tmp --setenv NODE_PATH /target/node_modules --setenv PYTHONDONTWRITEBYTECODE 1 --setenv EDU_QA_CHROMIUM /browsers/chromium-1243/chrome-linux-arm64/chrome --setenv PLAYWRIGHT_BROWSERS_PATH /browsers /bin/bash -c "$1"
