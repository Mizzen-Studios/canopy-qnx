# Status — 7 November 2026

**PASS: three fresh native libcan byte-exact runs and three native SLM managed-process restarts.**

- CAN runs1–3:100/100RX and100/100TX each, ordered ID/DLC/eight-byte exact with independently captured host traffic. Preserved in [native CAN evidence](docs/acceptance/native-can-20261106/summary.json); parent offline recheckPASS. This is the libcan fallback, NOT an accepted io-sock SocketCAN ABI/C2 gate.
- Fresh dedicated SLM image parsed the original config and started the managed libcan CAN service. Exact observed PIDs were checked before each kill:278546→323602→434194→520210. All three restarted and /dev/can0/rx0 was present afterward. Mainio-sock PID163853 stayed unchanged in each before/after snapshot.
- Observation windows3.3863/3.3168/3.4429seconds include a fixed3-second settle. These are **observed in this QEMU run · app budget, not a QNX benchmark**; not exact restart latency or evidence of service availability at every instant.
- [Native SLM receipt](docs/acceptance/slm-20261107/receipt.json), [serial](docs/acceptance/slm-20261107/serial.txt), [exact VM-specific controller](docs/acceptance/slm-20261107/controller.py). Controller refuses missing caps, takes a local exclusive lock, kills only the positively observed managed CAN PID in its own fresh image, and stops/reaps only its own QEMU.
- Effective cgroup100%CPU/1GiB,nice15; guest1vCPU/512MiB. Native guests serialized. No shared Gateway restart.

EarlyC6 host-vcan fault tests, C/Python parity and source-bound SDP x86 compile-only evidence remain recorded in [safestop](docs/safestop-early.md). Native timer-pulse/FIFO/CAN runtime acceptance is not claimed.

## Still unverified

Full SocketCAN C2/C3 requires matching x86_64 module/board ABI. Post-restart byte-exact CAN traffic, authenticated same-session SSH continuity, identity-safe production supervision, rolling-window/manual-latch limits, least privilege and robust failure injection are not established by the restart smoke. Main PID snapshots do not prove uninterrupted SSH. No full C3 policy acceptance is claimed.

All native guests stopped/reaped; lease free. Both repos private. SDK/licenses/headers/libs/images/binaries/QSC/secrets remain external. No publication, contacts, paid resources or upstream PRs.
