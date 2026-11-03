# CANopy — host foundation for QNX® 8.0

Private first milestone: SDK-independent reference models, **not a QNX implementation**.
Intended direction: io-sock/SocketCAN plus a vehicle-level fail-stop model.
No driver, guest boot, SLM restart, QPP connector, real-time scheduling, learned
pilot, physical vehicle or certification is implemented or demonstrated here.
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
fonts or dependencies. It includes the deterministic drop/seed-7 fixture from
docs/replay/sample.jsonl. Play/pause, reset, scrub and change viewing speed.
Use the local file picker to load JSONL from any of the six host scenarios:

~~~sh
python3 -m canopy_host.sim --scenario frozen --seed 7 > replay.jsonl
~~~

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
- Objects are Python reference models in a single host process, not process
  isolation. A real actuator needs an independently scheduled watchdog; no
  host-process-death or actual driver-kill demonstration is claimed.

### Evidence map

| Model behavior | Implementation | Verification |
| --- | --- | --- |
| CRC, ctr4, strict fields | canopy_host/protocol.py | tests/test_safety.py |
| Actuator timeout and stop integration | canopy_host/safety.py:Actuator | boundary, delayed tick, corruption/freeze tests |
| Latch, pilot veto, recovery | canopy_host/safety.py:Safestop | ten-cycle, faults, ramp tests |
| Deterministic faults | canopy_host/sim.py | six scenarios; assert active before fault and stopped after |
| Optional classic SocketCAN | canopy_host/socketcan.py | frame codec only; live transport untested |
| No-SDK hygiene | scripts/check-no-sdk.sh | staged/deleted blob, binary, path, symlink negative tests |

## Optional Linux vcan transport

SocketCAN(interface='vcan0') is a standard-library transport adapter for an
**already configured** Linux CAN interface. It never loads modules, creates
interfaces or requires python-can. send/receive use classic standard CAN only;
extended, RTR, error and invalid-length frames reject. Callers must schedule
Actuator.advance from a monotonic clock even when receive returns None.
No integrated live actuator runner is supplied in this milestone.

No vcan interface existed on the development host; no actual vcan round trip
was tested. Byte pack/unpack tests are not live CAN evidence.

## Environment and unverified gates

Developed on Ubuntu 24.04 aarch64, Python 3.12.3. No /dev/kvm and no installed
qemu-system-x86_64 were found. No QNX SDK/QSTI installed or used. Target intent
is QNX SDP 8.0 x86_64; SDP build ID, QSTI/QEMU versions, qcc toolchain,
mods-can.so x86_64 loadability, kvaser_pci support, SLM, secpol and QPP APIs
are **unverified**. No target API has execution evidence yet. This milestone
does not satisfy the competition's runs-on-QNX gate. No QNX evaluation or
performance result is published. See docs/test-results.txt for local commands.

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
