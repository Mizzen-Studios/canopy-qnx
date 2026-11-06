# Native libcan three-run acceptance

Private evidence only. Every count/timing is **observed in this QEMU run · app budget, not a QNX benchmark**.

This gate tests external dev-can-linux v1.12 libcan fallback through QEMU kvaser_pci/SJA1000 and host vcan1. It is **not native SocketCAN, io-sock, or acceptance of the original C2 io-sock board**. The matching mods-can/io-sock ABI blocker remains. No SDK, images, GPL tool binaries or secrets are included.

## Reproduce

Requires exclusive native-target/vcan1 lease; external licensed ifs-edu-resmgr.bin and disk-edu-libc; QEMU kvaser_pci/can-host-socketcan; host cangen; vcan1 UP; systemd user scopes. Do not change shared images or SDK guest. Disk writes use process-local QEMU snapshots. Sockets are unique under a fresh short output path; no host SSH forward is opened. The existing boot SSH fault is unrelated: this gate uses the serial shell, not authenticated SSH.

Run: scripts/qemu-native-capped.sh python3 tools/native_can_three.py /home/ubuntu/qnx-host/guest/shared/qnx-native /home/ubuntu/.openclaw/workspace/.openclaw/tmp/c2-unique

Wrapper enforces CPUQuota=100%, MemoryMax=1G, nice15. Python independently checks actual cgroup v2 cpu.max/memory.max and nice before launching QEMU TCG with 1vCPU/512MiB. No uncapped fallback.

Each fresh boot excludes pre-existing fixed boot traffic, checks actual native cansend help, applies known **experimental PIIX PIRQ A–D to IRQ10** qtest override with readback, then starts fresh native libcan candump. After target readiness (1s) plus settling (300ms), actual host command is:

cangen vcan1 -n 100 -I i -L 8 -D i -g 30

Independent host raw CAN reception captures actual cangen loopback, not generator printed intentions. Native candump ordered IDs/DLC/payloads must equal that actual host capture: exactly 100 frames and 100 distinct IDs/payloads. Native TX uses inspected libcan cansend CLI: IDs 0x400..0x463 and eight varying bytes per frame, target sleep 0.03 pacing. Independent host reception must match count, order, IDs and every byte. No filtering hides extra frames in either acceptance window.

Malformed native rows, missing completion lines, nonzero generator/native script status, count/order/content differences, constant fixtures, missing caps and exceptions fail closed. An earlier successful run cannot make a failed series pass. Owned QEMU processes are terminated/reaped in finally. Summary stays pass=false unless three consecutive runs pass.

This depends on experimental routing, settling and paced traffic. It does not prove production BSP routing, saturation/overruns, CAN FD, bus-off/error-passive, physical hardware, restart supervision, or SocketCAN target runtime.
