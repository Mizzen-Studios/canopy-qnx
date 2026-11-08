# CANopy — reusable QNX incident recorder and workbench

**First action: [open the native-first incident desk](web/incident-pack/index.html).** It opens the original recorded QNX v2 pack locally. Query killed/recovery/survivors/isolation, inspect raw/control evidence, export/reset or import your own QNX pack. HOST simulation is a secondary NOT QNX route. This saved capture is not native PASS at the current tip, a live connection, or new SSH continuity.

## Capture → import → query → inspect evidence

Use the [native recorder](docs/native-recorder.md) for a NEW bounded QNX SLM/libcan incident, then open the [local incident desk](web/incident-pack/index.html) to import that exact pack, query interruption/recovery and inspect evidence. [Pack contract and CLI](docs/incident-pack.md). No server, upload or browser command execution. Missing/corrupt/mixed/stale/incompatible packs fail closed to UNKNOWN.

[Fresh native receipt](docs/acceptance/native-recorder-20261108/NOTES.md): actual supervised driver kill/restart and independent ordered byte-exact100RX100TX, bounded structured slog2 and a co-located observer death/separate-recorder control. New packs have NO authenticated SSH-continuity proof; that exists only in the separate historical record below. Origin labels and hash bindings are collector-declared cooperative integrity, not attestation. The current independent host review is being closed before final council inspection.

Olly approved these upgrades on8Nov; earlier feature-freeze gates are historical. New council acceptance pending. C6/native safety STOPPED; SocketCAN UNVERIFIED. recorded:false; no media now, no publication/deployment. Videos only after all features and final verification plus the separate recording gate.

## Historical recorded experiment — separate from new capture

Private [claim-to-receipt review](REVIEW.md): historical source/build gaps remain UNVERIFIED.

Actual [desktop/mobile Chromium validation](docs/acceptance/browser-20261107/NOTES.md): missing/corrupt/mixed → UNKNOWN; recorded native labels remain separate from simulation. That browser milestone records host suite **126 passed / 8 skipped** at its own pinned revision; later host receipts are chronological, not new native acceptance.

Private evidence workbench for a bounded **native QNX libcan + SLM experiment**.
The historical recorded journey is: positively identified CAN PID killed → new CAN PID →
100 RX + 100 TX ordered byte-exact post-restart traffic, while the **same
authenticated SSH connection** continued and main io-sock PID stayed unchanged.
See the canonical [capability ledger](docs/capabilities.md) and
[raw run receipt](docs/acceptance/slm-continuity-20261107/receipt.json).

**observed in this QEMU run · app budget, not a QNX benchmark**.
The recorded windows include a fixed3-second settle; they are not restart latency.
No continuous CAN availability, physical-safety, certification, QNX benchmark,
production isolation or clock-aligned causal timing claim is made.

**Native C6 FAIL / STOPPED.** Its FIFO20/timer-pulse execution did not establish
functional acceptance:850 TX attempts versus one captured heartbeat.
[Failure evidence](docs/acceptance/safestop-focused-failure-20261107/README.md)
is retained. No retry or new heartbeat/safety work is authorized.
**SocketCAN remains BLOCKED / UNVERIFIED** on matching module/board ABI;
libcan receipts are not SocketCAN acceptance. QPP remains unverified.

## Separate evidence journeys

- **Bring your own pack:** open the local [interactive incident desk](web/incident-pack/index.html); import, validate, query, reset and export without a server or SDK. [Schema, CLI and native adapter contract](docs/incident-pack.md). HOST fixtures are synthetic; QNX labels are collector declarations, not attestation. The pinned viewer below is unchanged.

- Recorded native incident: [SLM/SSH receipt](docs/acceptance/slm-continuity-20261107/receipt.json),
  [read-only workbench](docs/workbench/index.html),
  [strict viewer verifier](tools/incident_workbench.py). See [workflow and limits](docs/incident-workbench.md).
- Host simulation: [offline replay](docs/replay/index.html), deterministic
  director, Linux vcan actuator models, DBC/VSS mapping and pilot/C export.
  These never become QNX proof and are not the product's safety claim.
- [Experimental SocketCAN demo](docs/socketcan-demo.md): cross-build and host
  Linux tests only; does not resolve the native ABI gate.

## Run on host

Python 3.10+, Git, and Node.js 18+ for JavaScript replay contract tests;
no pip/npm packages, SDK, root or network needed:

~~~sh
python3 -m unittest discover -s tests -v
./scripts/check-no-sdk.sh
python3 -m canopy_host.sim --scenario drop --seed 7
~~~

Other scenarios: bad-crc, frozen, obstacle, stale, pilot. JSONL goes to stdout;
each row explicitly identifies host deterministic simulation, NOT QNX. Time is
logical integer milliseconds, never measured latency. Seed controls initial
speed; same seed/scenario produces identical records. CI runs host models,
replay contracts and artifact negative tests only.

## Offline replay dashboard

Open docs/replay/index.html directly in a browser; no server, ports, network,
fonts or dependencies. It includes the deterministic hero/seed-7 fixture from
docs/replay/run.jsonl. Play/pause, reset, scrub, event-jump, inspect and keyboard
controls work offline. Record and export a validated host hero:

~~~sh
./canopy record --script hero --seed 7 --host-sim --output run.jsonl
./canopy replay run.jsonl --output replay.html
~~~

The older single-fault sim JSONL is a different model schema, not a replay import.
See [record/replay workflow](docs/replay/workflow.md) for provenance and validation.

A-E panels preserve the imported source: HOST SIMULATION or HOST VCAN, always
NOT QNX. Guest SSH/PIDs/driver stats remain explicitly unavailable. The timeline
shows logical or measured host watchdog states, never QNX restart duration.
Files must match the separate strict simulation/live schema, have increasing
time, and stay below 2 MB / 10000 rows.
Invalid files leave the previous replay intact. No data is uploaded.
See docs/dashboard-design.md and docs/replay/verification.md.

## Historical host-only two-layer model (not native safety)

- Classic CAN ID 0x200, four bytes: state, brake percentage, low-nibble
  alive counter (upper nibble must be zero), CRC. CRC-8/SAE-J1850
  (poly 0x1d, init/xorout 0xff, no reflection) covers ID bytes 02 00 then
  state/brake/counter. Known-answer check: 123456789 -> 0x4b.
  E2E-style detection only; **not AUTOSAR conformance or authentication**.
- Actuator independently asserts 100% brake and hazards at >=100 ms since
  last accepted frame. Constant model deceleration is 4 m/s² at full brake;
  this is an illustrative controlled-stop model, not validated vehicle physics.
  Integration splits at the timeout even if the next scheduler call is late.
- Bad CRC, malformed fields, wrong ID, frozen, backward and skipped counters
  never refresh that deadline. Exact +1 modulo 16 is required while active.
  Timeout recovery requires ten consecutive SAFE_STOP frames with fresh counters;
  the first may establish a new counter baseline but cannot repeat the last one.
  DRIVE cannot re-arm a timed-out actuator. Restart and wrap ambiguity remains:
  a four-bit counter is not replay protection against an adversary.
- Safestop starts latched. Signal ages >30 ms, obstacle <=5 m, nonfinite values,
  pilot request outside 0..20 m/s, or cycle gap >20 ms latch stop. These are
  **application model parameters**, not measurements or validated limits.
  Only ten fresh healthy cycles release the latch. Cycle ten still emits full
  SAFE_STOP for actuator synchronization; subsequent fresh cycles reduce brake
  by 10 percentage points per cycle. Pilot has no latch-clear API.
- Pure model tests run in one process. The [live host runtime](docs/host-runtime.md)
  separately schedules the actuator and sender on Linux vcan; exact owned-child
  SIGSTOP/SIGKILL tests verify independent timeout behavior. This is not a QNX
  driver-kill, microkernel isolation, scheduling guarantee or physical watchdog.

### Evidence map

| Model behavior | Implementation | Verification |
| --- | --- | --- |
| CRC, ctr4, strict fields | canopy_host/protocol.py | tests/test_safety.py |
| Actuator timeout and stop integration | canopy_host/safety.py:Actuator | boundary, delayed tick, corruption/freeze tests |
| Latch, pilot veto, recovery | canopy_host/safety.py:Safestop | ten-cycle, faults, ramp tests |
| Deterministic faults | canopy_host/sim.py | six scenarios; assert active before fault and stopped after |
| Classic SocketCAN + independent processes | canopy_host/socketcan.py, runtime.py | seven actual Linux vcan fault scenarios; docs/host-runtime.md |
| DBC/VSS signal mapping | canopy_host/vss.py | golden vectors and exhaustive host codec inputs |
| Learned pilot + C export | canopy_host/pilot.py, ai/ | held-out synthetic data and C/Python parity; docs/pilot.md |
| Hero director and offline record | canopy_host/director.py, record.py | deterministic bytes and Chromium interaction tests |
| No-SDK hygiene | scripts/check-no-sdk.sh | staged/deleted blob, binary, path, symlink negative tests |

## Optional Linux vcan transport

SocketCAN(interface='vcan0') is a standard-library transport adapter for an
**already configured** Linux CAN interface. It never loads modules, creates
interfaces or requires python-can. send/receive use classic standard CAN only;
extended, RTR, error and invalid-length frames reject. Callers must schedule
Actuator.advance from a monotonic clock even when receive returns None.
The integrated live actuator fault runner is available:

~~~sh
sudo ./scripts/setup-vcan.sh vcan0
python3 -m canopy_host.runtime_runner --output /path/outside/repo/new-run
~~~

The dated host setup records can-utils and vcan0 UP (not current readiness). Three 100-frame host runs
were byte-exact; seven live fault scenarios passed. These are HOST VCAN results,
not QNX CAN acceptance. See [host setup](docs/host-vcan-setup.md),
[fail-safe runtime](docs/host-runtime.md), [VSS mapping](docs/vss-mapping.md),
[QPP integration boundary](docs/vss-qpp-integration.md) and [pilot](docs/pilot.md).

## Environment and unverified gates

Owner-approved platform: **the existing Ubuntu 24.04 ARM64 VM running an
x86_64 QNX guest under QEMU TCG, explicitly without KVM**. An x86_64 KVM host
is not a prerequisite. This supersedes the original plan's KVM-only preflight.
Developed with Python 3.12.3. The recorded host QEMU was 8.2.2; doctor queries the
installed binary rather than assuming its devices. Licensed SDP8 is installed in
an external private x86 Linux guest; actual qcc builds and native QNX libcan/SLM
experiments are recorded. QSTI provenance, SocketCAN module/board ABI, secpol
and QPP runtime remain unverified. No SDK, licence, binary or image is distributed.
The [capability ledger](docs/capabilities.md), not host doctor output, records
observed capability scope. No QNX evaluation/performance result is published.

## Read-only host preflight

~~~sh
./canopy doctor          # human-readable diagnostics; expected exit 1 today
./canopy doctor --json   # stable schema_version=1, same nonzero exit
./canopy up              # explicit blocked result; no guest started
~~~

Doctor probes QEMU version and help for TCG, edu, edu.dma_mask, kvaser_pci and
can-host-socketcan; x86_64 Linux user-emulator version and binfmt registration;
ip/candump/cansend/cangen; existing vcan interfaces and optional module metadata.
No /dev/kvm is fine. Binfmt is advisory because explicit qemu-x86_64-static
invocation is possible; neither route is SDK execution evidence. Probes have a
five-second timeout each. No modules/interfaces, packages or system settings are
changed, and no guest starts. Help-advertised support is not device execution.

For future external SDK setup, supply these environment variables:

- QNX_HOST and QNX_TARGET: existing external SDK directories.
- CANOPY_QNX_ENV: external nonempty qnxsdp-env.sh file (never sourced by doctor).
- CANOPY_QSTI_IMAGE: external nonempty guest image (never opened or booted).

Paths resolving inside this repository are rejected, including symlinks into it.
Only presence/type is checked; no SDK files are read, downloaded or executed.
An arbitrary nonempty file does **not** prove a valid QSTI/SDP version.

JSON separates host_ready, qnx_prerequisites_ready, qnx_accepted and overall_ready.
Host readiness includes configured vcan and can-utils for the planned CAN path;
QEMU availability alone is not a ready CAN lab. For this legacy host doctor, live acceptance
is always NOT RUN and overall_ready is always false, even with all external
paths present. Exit 1 is intentional, not a crash; invalid CLI usage exits 2.
The SDK-independent host tests and offline dashboard remain usable independently.
This doctor does not consume historical native receipts or launch target acceptance.

## Repository hygiene and licence

Apache-2.0; original host implementation, no GPL code copied. No SDK files,
images, archives or compiled artifacts belong here. .gitignore prevents common
accidents, while check-no-sdk.sh inspects Git index blobs AND the entire current
worktree, including ignored artifacts. It rejects recognized paths, signatures,
symlinks, binary/archive contents and oversized files. Python cache directories
are ignored only in the worktree; tracked bytecode still fails. This heuristic
is not proof of provenance, an arbitrary SDK detector, or a substitute for review.
Keep SDK installations outside the repository. CI requires no SDK access.

Prior art we learned from: Deniz-Eren/dev-can-linux (GPL-2.0, libcan ports incl. kvaser_pci), stappdev/qnxCAN1000, NikhilGogu/qnx-ctucanfd (libcan CAN FD driver for ctucan_pci with supervised restart). The current private CANopy slice is an evidence-bound recorded libcan/SLM incident workbench. SocketCAN remains blocked/unverified; the historical vehicle fail-safe lane is C6 FAIL/stopped, not current positioning or a validated capability.

That credit describes design intent, not implemented target support. This
milestone was written from the supplied plan without copying rival source.
No Pages, public publication, upstream PR, video, submission or contact is
part of this milestone.
