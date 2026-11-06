# C6 early build-order evidence (private, 2026-11-06)

This completes the **portable skeleton + existing host actuator** early step in
plan v3 §4.7, not QNX C6 acceptance. Original C source was written from the app
specification; no SDK headers, implementation, libraries or generated binary
are included. Demo of fail-safe patterns, not ISO 26262 / IEC 61508 compliance.

## What exists

- `safety/safestop.c` / `safestop.h`: allocation-free portable FSM and
  classic-CAN 0x200 four-byte encoder/decoder, counter modulo 16, CRC-8/J1850
  (ID bytes 02 00 included). CRC/counter are error detection, not authentication.
- Same observable FSM outputs as `canopy_host.safety.Safestop`: startup latch;
  either sensor age outside 0..30 ms, obstacle <=5 m, nonfinite input or pilot
  speed outside 0..20 m/s forces full brake; intercycle gap >20 ms relatches.
  These are demo app budgets, not QNX benchmarks or safety-derived limits.
- Only ten consecutive healthy, increasing-time cycles release the latch.
  Cycle ten still emits SAFE_STOP/full brake; cycle eleven begins the
  ten-percentage-point release ramp. Pilot has no latch-clear entrypoint.
- Nonincreasing timestamps return failure without changing state or output.
  Future adapters must handle that failure by withholding drive and failing
  closed; they must never reuse a previous DRIVE output as a new heartbeat.
- Fresh-cycle bookkeeping saturates at 12 after release to avoid C integer
  overflow. This is intentionally not the Python model's unbounded internal
  count; wire output and latch/brake behavior remain equivalent.
- Existing Python Actuator remains the independent host ECU watchdog. No new
  reset proof or duplicate actuator was introduced. Invalid CRC, frozen,
  skipped/backward counters never renew its 100 ms deadline. Timeout recovery
  still requires ten fresh SAFE_STOP frames, independently of the sender FSM.

## Reproduce on host

Host compiler required (a missing compiler is a test failure, not a hidden skip):

```sh
make -C safety
make -C safety clean  # guard scans even ignored compiled artifacts
python3 -m unittest discover -s tests -p test_native_safestop.py -v
CANOPY_LIVE_VCAN=1 CANOPY_CAN_INTERFACE=vcan2 \
  python3 -m unittest discover -s tests -p test_runtime.py -v
scripts/check-no-sdk.sh
git diff --check
```

The parent provisioned isolated Linux vcan2 UP. These tests never configure
interfaces and did not use C2's vcan1. Five new host-compiled C/Python tests pass:
all state/counter encodings; all single-bit corruptions of those encodings;
CRC-valid invalid fields, wrong IDs/lengths; hard stale/obstacle/pilot veto;
interrupted ten-fresh-cycle release and ramp; timing failures; seeded mixed
sequences and long-running saturation; C-encoded packets into the existing
Python ECU with frozen/bad-CRC/skipped-counter timeout.

The existing runtime suite also passed (five tests, including one executing
**seven actual Linux SocketCAN host fault scenarios**): stale, obstacle, pilot,
SIGSTOP, SIGKILL, bad CRC, frozen counter. Its assertions check initial ten-frame
arming, eventual zero simulated speed/full brake/hazards, sender latch for sensor
faults, watchdog assertion for sender/wire faults, invalid-frame rejection, and
owned child cleanup. Its host-agent timing is a host test heartbeat, **not SSH
continuity or QNX canstats telemetry**. The longitudinal model is simulated;
no physical actuator stopping distance is established. Live tests exercise the
existing Python sender, not a native C/QNX daemon. C parity is separate evidence.

Full host discovery: 101 tests ran, 8 explicitly skipped (opt-in live/optional
checks); 93 passed. The separate vcan2 runtime invocation above ran all five
runtime tests without skips. No failed test was relabelled as accepted.

Raw private run logs: workspace `.openclaw/tmp/qnx-followup10/safety-live.log`
and `safety-host-all.log`. No host timing is presented as a QNX result.

## Future QNX adapter boundary / remaining blocker

Portable core deliberately does **not** pretend to implement a QNX adapter.
Future work must provide CLOCK_MONOTONIC sensor timestamps, a genuine timer
pulse receive loop with checked errors, observed SCHED_FIFO policy/priority,
bounded nonblocking CAN TX with checked errors, and signal/driver reconnection
handling without releasing the latch. The core contains no FIFO setup or
MsgReceivePulse claim. Do not substitute sleep scheduling and label it native.

An SDK cross-compile is optional compile-only evidence via the parent's exclusive
SDK lease: copy only these original source files outside Git and run
`qcc -Vgcc_ntox86_64 -std=c11 -Wall -Wextra -Werror -c safestop.c`.
No guest was started by this safety task. Cross-compilation cannot establish
native timing, native CAN traffic, pause/kill handling or complete C6 acceptance.

True QNX integration is still blocked by the matching x86_64 mods-can.so/io-sock
module/board ABI and missing internal build hooks. The current native libcan
fallback is **not working SocketCAN**. Required target evidence remains: real
native heartbeat delivery into the host ECU; stale/obstacle/pilot veto and
safestop pause/kill; bad CRC/frozen counter; ten fresh-cycle resume; and driver
failure/restart with independent network continuity. Until then C6 is pending.
