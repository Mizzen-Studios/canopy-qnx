# Native libcan three-run acceptance

Private evidence only. Every count/timing is **observed in this QEMU run · app budget, not a QNX benchmark**.

This gate tests external dev-can-linux v1.12 libcan fallback through QEMU kvaser_pci/SJA1000 and host vcan1. It is **not native SocketCAN, io-sock, or acceptance of the original C2 io-sock board**. The matching mods-can/io-sock ABI blocker remains. No SDK, images, GPL tool binaries or secrets are included.

## Reproduce

Requires exclusive native-target/vcan1 lease; external licensed ifs-edu-resmgr.bin and disk-edu-libc; QEMU kvaser_pci/can-host-socketcan; host cangen; vcan1 UP; systemd user scopes. Do not change shared images or SDK guest. Disk writes use process-local QEMU snapshots. Sockets are unique under a fresh short output path; no host SSH forward is opened. The existing boot SSH fault is unrelated: this gate uses the serial shell, not authenticated SSH.

Run: scripts/qemu-native-capped.sh python3 tools/native_can_three.py /home/ubuntu/qnx-host/guest/shared/qnx-native /home/ubuntu/.openclaw/workspace/.openclaw/tmp/c2-unique

Wrapper enforces CPUQuota=100%, MemoryMax=1G, nice15. Python independently checks actual cgroup v2 cpu.max/memory.max and nice before launching QEMU TCG with 1vCPU/512MiB. No uncapped fallback.

Each fresh boot applies the known **experimental PIIX PIRQ A–D to IRQ10** qtest override with readback at the initial QNX_RX_READY marker, before old boot traffic can wedge the device. After the existing startup ends, fixed boot traffic is excluded, actual native cansend help is checked, and fresh native libcan candump starts. The original per-frame shell TX script is serial-uploaded with 100ms pacing/draining to avoid UART input loss; this is setup, not CAN pacing. After target readiness (1s) plus settling (300ms), actual host command is:

cangen vcan1 -n 100 -I i -L 8 -D i -g 30

Independent host raw CAN reception captures actual cangen loopback, not generator printed intentions. Native candump ordered IDs/DLC/payloads must equal that actual host capture: exactly 100 frames and 100 distinct IDs/payloads. Native TX uses inspected libcan cansend CLI: IDs 0x400..0x463 and eight varying bytes per frame, target sleep 0.03 pacing. Independent host reception must match count, order, IDs and every byte. No filtering hides extra frames in either acceptance window.

Malformed native rows, missing completion lines, nonzero generator/native script status, count/order/content differences, constant fixtures, missing caps and exceptions fail closed. An earlier successful run cannot make a failed series pass. Owned QEMU processes are terminated/reaped in finally. Summary stays pass=false unless three consecutive runs pass.

This depends on experimental routing, settling and paced traffic. It does not prove production BSP routing, saturation/overruns, CAN FD, bus-off/error-passive, physical hardware, restart supervision, or SocketCAN target runtime.

## Evidence replay

After a successful live run, copy its text/JSON files into a dated subdirectory
here; never copy images or binaries. Run:

python3 tools/verify_native_can_evidence.py docs/acceptance/native-can-20261106

This independently re-parses the saved native frame rows and compares all
three host/target sequences. It is an **offline recorded-evidence integrity
check**, not another live acceptance run.

Initial harness development attempts are not accepted runs: a padded-hex
readback assumption failed first; routing applied after startup yielded host
100/native RX0; unpaced serial script upload then lost UART input and timed
out after native RX100. Those failures were retained privately under
workspace scratch c2-10a/b/c, not counted as a successful three-run series.
Routing before initial traffic and paced serial upload address the observed
harness prerequisites, not the underlying BSP or UART throughput generally.

## Accepted series — 2026-11-06

Three consecutive fresh native QNX boots completed with live wrapper exit0.
Runs 1/2/3 each had host cangen capture100/native RX100 and native TX100/
independent host capture100, all ordered ID/DLC/eight-byte exact. RX had
100 distinct IDs and payloads; native TX likewise, with a different byte
sequence on each run. Counts are observed in this QEMU run · app budget,
not a QNX benchmark. This accepts the libcan fallback only, NOT io-sock C2.

Evidence: native-can-20261106/summary.json plus per-run actual host captures,
native candump rows, serial transcript, intended TX frames, routing readback
and result JSON. Offline replay verification passed. Actual inherited caps
were cpu.max=100000 100000, memory.max=1073741824, nice15; QEMU1vCPU/512MiB.
All three owned native QEMUs stopped/reaped; owned QMP/qtest sockets removed.
SDK guest was not used or stopped by this worker. Native lease is free.

Host regression: 102 tests ran, 8 skipped, suite OK. Six focused gate/parser/
source-qualification tests pass. Uncapped invocation rejected before creating
an output directory. Artifact guard and whitespace checks pass.

Archived text transcripts normalize serial CR bytes to LF and strip line-end
whitespace for Git diff hygiene; frame IDs/data and line order are unchanged.
Original byte transcripts remain privately in workspace scratch c2-10d.
