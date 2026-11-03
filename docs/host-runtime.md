# Host SocketCAN safety runtime

**HOST VCAN, not QNX.** Linux raw SocketCAN traffic and separate OS processes
are real; vehicle, sensors and the 4 m/s² full-brake longitudinal model are
simulated. No safety certification, WCET or QNX performance claim.

## Run

With an operator-provisioned, UP vcan0 (the runner never configures the host):

    python3 -m canopy_host.runtime_runner --output .openclaw/tmp/live-run
    CANOPY_LIVE_VCAN=1 python3 -m unittest discover -s tests -p test_runtime.py -v

The output directory must be new. CI's ordinary unittest discovery skips the
live test with an explicit reason. The runner starts a ready actuator ECU first,
then a separate safestop sender; signals target only its owned sender child PID.
Each child has a nine-second bound; finally kills/reaps both, including a stopped
child. Standalone runtime roles accept --duration in (0,60] seconds.

The sender consumes atomic JSON snapshots with monotonic_ns, obstacle_m and
pilot_speed_mps, using measured monotonic age (30 ms input deadline). Missing,
malformed, future and nonfinite input fails closed. Pilot cannot supply a latch
clear: only ten consecutive healthy increasing-time cycles release it; the tenth
still sends SAFE_STOP and subsequent cycles ramp brake down by 10 per cycle.

CAN ID 0x200 retains protocol.py's four-byte state/brake/ctr4/CRC-8-J1850 wire
format. The independent actuator ticks even without packets, rejecting bad CRC
and repeated counters without refreshing its 100 ms watchdog. Startup requires
ten fresh SAFE_STOP packets before accepting release. Receiver readiness avoids
losing a startup recovery packet. Absolute-clock initialization avoids integrating
host uptime as simulated vehicle travel. Unrelated IDs cannot reset recovery.
The bus must be exclusive for ID 0x200; no authentication is claimed.

## Records and evidence

Every JSONL line carries source, schema canopy.host-runtime.v1, monotonic_ns,
pid and event. Heartbeats include transmitted bytes, input age and latch state;
actuator records include actual received bytes, acceptance, recovery, last-valid
monotonic millisecond, brake, hazards and simulated speed. Watchdog transitions
record measured elapsed milliseconds, not a hardcoded pass. Summary metrics are
computed from records and asserted: timeout observation 100–150 ms (host test
allowance, not a real-time guarantee), controlled stop and host-agent gaps <=100 ms.

The runner's 50 Hz host-agent log stays outside sender/actuator processes. This
proves host orchestration continues during its child outage only; it does **not**
prove QNX canopy-agent over eth0, SSH continuity or a main io-sock surviving.

Observed 2026-11-03 on this Ubuntu aarch64 host, Linux vcan0:

| Fault | Watchdog elapsed since valid (ms) | Fault to full brake (ms) | Fault to simulated zero (ms) | Max host-agent gap (ms) |
|---|---:|---:|---:|---:|
| stale | n/a, sender veto | 35.955 | 2320.494 | 22.886 |
| obstacle | n/a, sender veto | 4.960 | 2313.914 | 23.638 |
| pilot outside envelope | n/a, sender veto | 4.529 | 2308.085 | 27.140 |
| exact child SIGSTOP | 100 | 101.081 | 2414.905 | 26.162 |
| exact child SIGKILL | 100 | 99.195 | 2396.371 | 21.399 |
| bad CRC | 100 | 96.593 | 2401.780 | 24.489 |
| frozen counter | 100 | 97.927 | 2405.247 | 27.868 |

Full raw records and per-scenario summaries: host-runtime-evidence-20261103/.
Bad CRC rejected 289 packets; frozen rejected 280 packets. Each scenario first
observed release, then observed a monotonic controlled stop, hazards and full
brake. Fault-to-brake may be under 100 ms because last valid reception precedes
fault injection. Logging/sampling delay makes it differ from watchdog transition.

An initial development run exposed two bugs (absolute-clock initialization and
receiver startup race); it is not acceptance evidence. Both were repaired before
the seven-scenario evidence run. Portable tests cover malformed snapshots,
source tags and attempted pilot clear; existing safety tests cover ten-cycle
recovery, frozen/bad-CRC, modulo counter and exact timeout boundaries.

## Still blocked on SDK / actual QNX

No native safestop binary, QNX FIFO scheduling/timer pulses, QNX CAN driver,
QPP sensors, SLM recovery, guest process signals, eth0/SSH continuity, physical
actuator or guest/host CAN bridge was tested here. Those require the licensed SDK,
a bootable target image and native build/deployment/integration. C6's host-side
runtime is exercised, not completed QNX acceptance; C8 has host-only continuity,
not its required QNX agent stream. Do not relabel these records as QNX evidence.

Verification: portable discovery 43 tests, 42 passed and one explicit live skip.
Opt-in runtime discovery: five tests passed, including seven live fault subcases
and exact-child reaping checks (22.552 s observed). SDK guard and diff check pass.
