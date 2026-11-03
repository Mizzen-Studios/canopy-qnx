#!/bin/sh
# Explicit, local host setup only. No persisted network/service config.
set -eu
interface=${1:-vcan0}
case "$interface" in vcan[0-9]*) ;; *) echo 'usage: setup-vcan.sh [vcanN]' >&2; exit 64 ;; esac
case "${interface#vcan}" in *[!0-9]*|'') echo 'interface must be vcan plus digits' >&2; exit 64 ;; esac
for command in ip candump cansend cangen; do
    command -v "$command" >/dev/null 2>&1 || { echo 'Missing iproute2/can-utils; install via apt first.' >&2; exit 1; }
done
if [ "$(id -u)" -ne 0 ]; then echo 'Run this explicit setup as root (sudo).' >&2; exit 1; fi
modprobe vcan
if ip link show dev "$interface" >/dev/null 2>&1; then
    ip -details link show dev "$interface" | grep -q 'vcan ' || { echo 'Existing interface is not vcan; refusing modification.' >&2; exit 1; }
else
    ip link add dev "$interface" type vcan
fi
ip link set dev "$interface" up
ip -details link show dev "$interface"
echo 'Host vcan ready. Not a QNX driver or physical CAN acceptance test.'
