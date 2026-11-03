# CANopy — host foundation for QNX® 8.0

Private SDK-independent host core, **not a QNX implementation**.
Implemented host-side: deterministic director/replay, separate Linux SocketCAN
actuator/safestop processes, DBC/VSS mapping, learned pilot and C export.
No QNX driver/guest, SLM restart, running QPP connector, native real-time scheduling,
physical vehicle or certification is implemented or demonstrated here.
No first-of-kind, availability, restart-speed, benchmark or safety guarantee is made.

Demo of fail-safe patterns; not an ISO 26262 / IEC 61508 claim.

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

All A-E panels say HOST SIMULATION / NOT QNX. Missing sensor inputs, SSH, PIDs
and driver stats remain explicitly unavailable. The timeline shows logical-time
watchdog states, not measured restart durations. Files must match the host sim
record contract, have strictly increasing time, and stay below 2 MB / 10000 rows.
Invalid files leave the previous replay intact. No data is uploaded.
See docs/dashboard-design.md and docs/replay/verification.md.

## Two-layer model

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

The development host now has can-utils and vcan0 UP. Three 100-frame host runs
were byte-exact; seven live fault scenarios passed. These are HOST VCAN results,
not QNX CAN acceptance. See [host setup](docs/host-vcan-setup.md),
[fail-safe runtime](docs/host-runtime.md), [VSS mapping](docs/vss-mapping.md),
[QPP integration boundary](docs/vss-qpp-integration.md) and [pilot](docs/pilot.md).

## Environment and unverified gates

Owner-approved platform: **the existing Ubuntu 24.04 ARM64 VM running an
x86_64 QNX guest under QEMU TCG, explicitly without KVM**. An x86_64 KVM host
is not a prerequisite. This supersedes the original plan's KVM-only preflight.
Developed with Python 3.12.3. The current host QEMU is 8.2.2; doctor queries the
installed binary rather than assuming its devices. No QNX SDK/QSTI installed
or used. Target intent is QNX SDP 8.0 x86_64; SDP build ID, QSTI version, qcc toolchain,
mods-can.so x86_64 loadability, kvaser_pci support, SLM, secpol and QPP APIs
are **unverified**. No target API has execution evidence yet. This milestone
does not satisfy the competition's runs-on-QNX gate. No QNX evaluation or
performance result is published. See docs/test-results.txt for local commands.

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
QEMU availability alone is not a ready CAN lab. At this milestone acceptance
is always NOT RUN and overall_ready is always false, even with all external
paths present. Exit 1 is intentional, not a crash; invalid CLI usage exits 2.
The SDK-independent host tests and offline dashboard remain usable independently.
Guest launch orchestration and target acceptance require the SDK follow-up.

## Repository hygiene and licence

Apache-2.0; original host implementation, no GPL code copied. No SDK files,
images, archives or compiled artifacts belong here. .gitignore prevents common
accidents, while check-no-sdk.sh inspects Git index blobs AND the entire current
worktree, including ignored artifacts. It rejects recognized paths, signatures,
symlinks, binary/archive contents and oversized files. Python cache directories
are ignored only in the worktree; tracked bytecode still fails. This heuristic
is not proof of provenance, an arbitrary SDK detector, or a substitute for review.
Keep SDK installations outside the repository. CI requires no SDK access.

Prior art we learned from: Deniz-Eren/dev-can-linux (GPL-2.0, libcan ports incl. kvaser_pci), stappdev/qnxCAN1000, NikhilGogu/qnx-ctucanfd (libcan CAN FD driver for ctucan_pci with supervised restart). CANopy differs by targeting io-sock/SocketCAN and by the vehicle-level fail-safe.

That credit describes design intent, not implemented target support. This
milestone was written from the supplied plan without copying rival source.
No Pages, public publication, upstream PR, video, submission or contact is
part of this milestone.
