# Status — 7 November 2026

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

Authenticated SSH continuity is still NOT PASS: the actual attempt failed
before authentication because the IFS lacked sshd-session. Installed SDK
helpers were located; an external image rebuild is active. Native guest was
stopped/reaped. Sole SDK build guest uses CPU100%,1GiB,nice15,1vCPU/512MiB;
no concurrent native guest. C6 native FIFO/timer source is prepared, with
real qcc rebuild pending after a strict-C API-visibility correction.

## Still unverified

Full SocketCAN C2/C3 requires matching x86_64 module/board ABI. Authenticated same-session SSH continuity, identity-safe production supervision, rolling-window/manual-latch limits, least privilege and robust failure injection are not established by the restart smoke. Main PID snapshots do not prove uninterrupted SSH. No full C3 policy acceptance is claimed.

Native guests stopped/reaped; the parent currently owns the serialized SDK build lane. Both repos private. SDK/licenses/headers/libs/images/binaries/QSC/secrets remain external. No publication, contacts, paid resources or upstream PRs.
