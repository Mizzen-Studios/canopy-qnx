# Status — 7 November 2026

## Current direction — council approval, 7 November 2026

Canonical [capability ledger](docs/capabilities.md) separates host simulation,
recorded native libcan/SLM PASS, SocketCAN UNVERIFIED and C6 FAIL/stopped.
Recorded incident receipts are the hero; no native vehicle-safety positioning.
C6 remains STOPPED: no automatic retries, heartbeat work or renamed safety lane.
Read-only evidence-bound incident viewer implemented at f3b4fb0; parent verifier
and six corruption/HTML tests PASS. This is generation-time recorded evidence,
not fresh QNX execution or historical driver source attestation. Historical receipts below remain preserved, not fresh runs.


**PASS: three fresh native libcan byte-exact runs and three native SLM managed-process restarts.**

- CAN runs1–3:100/100RX and100/100TX each, ordered ID/DLC/eight-byte exact with independently captured host traffic. Preserved in [native CAN evidence](docs/acceptance/native-can-20261106/summary.json); parent offline recheckPASS. This is the libcan fallback, NOT an accepted io-sock SocketCAN ABI/C2 gate.
- Fresh dedicated SLM image parsed the original config and started the managed libcan CAN service. Exact observed PIDs were checked before each kill:278546→323602→434194→520210. All three restarted and /dev/can0/rx0 was present afterward. Mainio-sock PID163853 stayed unchanged in each before/after snapshot.
- Observation windows3.3863/3.3168/3.4429seconds include a fixed3-second settle. These are **observed in this QEMU run · app budget, not a QNX benchmark**; not exact restart latency or evidence of service availability at every instant.
- [Native SLM receipt](docs/acceptance/slm-20261107/receipt.json), [serial](docs/acceptance/slm-20261107/serial.txt), [exact VM-specific controller](docs/acceptance/slm-20261107/controller.py). Controller refuses missing caps, takes a local exclusive lock, kills only the positively observed managed CAN PID in its own fresh image, and stops/reaps only its own QEMU.
- Effective cgroup100%CPU/1GiB,nice15; guest1vCPU/512MiB. Native guests serialized. No shared Gateway restart.

EarlyC6 host-vcan fault tests, C/Python parity and source-bound SDP x86 compile-only evidence remain recorded in [safestop](docs/safestop-early.md). Native timer-pulse/FIFO/CAN runtime acceptance is not claimed.

## Follow-up 11: post-restart traffic and native preparation

Three additional managed-process kills now each have 100 RX + 100 TX ordered
ID/DLC/payload exact against independent host capture. Main io-sock PID163853
stayed unchanged. [Receipt](docs/acceptance/slm-traffic-20261107/receipt.json)
and all three frame arrays are preserved; offline corruption tests reject bad
bytes/order/count/PID/cap receipts. Evidence2b9be8c; verifiera093d13.
These are **observed in this QEMU run · app budget, not a QNX benchmark**.

**C3 requested libcan close-out PASS:** a further three kills each passed
100 RX +100 TX exact AND the same authenticated SSH connection kept streaming.
[Receipt](docs/acceptance/slm-continuity-20261107/receipt.json), client/server
authentication logs, raw serial, controller and all six frame arrays are saved;
evidence568ea6a. CAN PIDs626715→778263→2764823→4743191; main io-sock163853
unchanged; same host SSH client126654, contiguous counters0..96. Largest
observed tick gap1.385132s. Windows3.403986/3.377878/3.431113s include a fixed
3s settle, NOT pure restart latency. **Observed in this QEMU run · app budget,
not a QNX benchmark.**

Prerequisites actually discovered: missing SSH session/auth helpers were staged
from the installed SDK externally; main io-sock was attached to IRQ10 despite
PCI reporting11. Before the kills, virtio PIRQ-C and Kvaser PIRQ-D were routed
to the observed IRQ10; virtio used vectors=0, and IPv4 was configured. Earlier
network/banner failures and an unbounded remote-shell PATH mistake are NOT
counted as acceptance. The final bounded stream uses /proc/boot/sleep.

C6 strict actual qcc compile/link PASS ([receipt](docs/acceptance/safestop-build-20261107/receipt.json));
native FIFO/pulse/actuator runtime attempt FAILED; lane stopped after the focused
attempt below. SDK/native guests stopped/reaped. Effective caps remained
CPU100%,1GiB,nice15,1vCPU/512MiB.

## Still unverified

Full SocketCAN C2/C3 requires matching x86_64 module/board ABI. Identity-safe production supervision, rolling-window/manual-latch limits, least privilege and robust failure injection are not established by the restart smoke. The separate authenticated stream above—not PID snapshots—proves the bounded SSH observation. No full C3 policy acceptance is claimed.

C6 lane stopped; SDK, C3 and C6 guests stopped/reaped; lease free. Both repos private. SDK/licenses/headers/libs/images/binaries/QSC/secrets remain external. No publication, contacts, paid resources or upstream PRs.

## C6 failure recovery

**Runtime gate UNVERIFIED / last execution FAIL:**850 native TX attempts versus one host0x200 heartbeat; all SAFE_STOP, no fresh sensors. Evidence:docs/acceptance/safestop-failure-20261107. **observed in this QEMU run · app budget, not a QNX benchmark**. Guest stopped/reaped; one focused fix attempt next.

## Focused C6 attempt closed — 11:06 UTC

**BLOCKED / runtime UNVERIFIED.** Fresh100RX+100TX exact baseline passed; raising all observed10r/20r CAN helpers24r did not fix850 native TX attempts versus1 host heartbeat. Root cause remains undetermined in persistent libcan RX/TX, not an accepted scheduler fix. Evidence:docs/acceptance/safestop-focused-failure-20261107. **observed in this QEMU run · app budget, not a QNX benchmark**. Guest stopped/reaped, lease free. C6 lane STOPPED per one-attempt rule; no automatic retry. E2 host/docs polish selected; no E2 snapshot runtime PASS. Experimental XML archived with failure evidence, not production-installed.
