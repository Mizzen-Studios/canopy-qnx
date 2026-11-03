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

## Integrated Pilot / VSS / agent session

For the integrated **Linux host-only** path (exclusive ID 0x200 on vcan0):

    ./canopy host-session --interface vcan0 --duration 10 --output /external/new-run
    ./canopy host-record /external/new-run -o /external/new-run/replay.jsonl
    ./canopy replay /external/new-run/replay.jsonl -o /external/new-run/replay.html

The directory must not exist. No interface/system setup is performed. Project
VSS frames 0x100/101/102 are sent at approximately 100 Hz and decoded by a
separate SocketCAN receiver through HostAdapter. Sensors are explicitly
synthetic: 36 km/h, zero steering, configurable obstacle distance. The learned
host tree requests speed/steering; only its speed request goes into safestop.
Pilot cannot clear the latch. Sensor snapshots use the oldest actual reception
time, never coordinator refresh time. 30 ms age and 20 ms cycle-gap safeguards
remain independent of the approximately 20 Hz agent stream. These are ordinary
host scheduler loops, not hard real-time guarantees. Sender and actuator remain
separate owned OS processes; the actuator advances its watchdog without traffic.

Explicit foreground long-running operation (parent may own a background job):

    ./canopy host-session --interface vcan0 --long-running --output /external/new-run

Stop that exact session with SIGTERM or Ctrl-C; its real PID is written to
new-run/session.pid while running. For example, from another terminal:

    kill -TERM "$(cat /external/new-run/session.pid)"

The supervisor terminates/reaps both children, closes sockets and removes the
PID file. Each role/session JSONL rotates at 1 MB with three backups (roughly
12 MB total). stderr is normally empty; repeated fatal errors exit rather than
loop. No daemon, cron or service installation is involved. A SIGKILL of the
supervisor cannot run cleanup; use SIGTERM. Never reuse a stale PID blindly.

HOST VCAN replay schema is canopy.host-vcan-run.v1, source
“HOST VCAN live SocketCAN; simulated vehicle; NOT QNX”, clock
host-monotonic-ns. Original CLOCK_MONOTONIC nanoseconds, relative measured
milliseconds, interface and actual host child PIDs survive conversion. The
20 Hz view joins only preceding raw observations (<=100 ms age); no interpolation
or fabricated receipt. Raw logs are authoritative. Rotation conversion uses the
common retained time window. Convert a stopped session for an atomic recording;
concurrent incomplete lines fail closed. The 2 MB/10000-row offline limits still
apply (choose a bounded run for full evidence). Python and browser reject
unknown/mixed clocks/sources/schemas and corrupt heartbeats; the previous browser
replay is retained on error. Provenance tags are not cryptographic authentication.
No guest PIDs, SSH, QNX driver stats, native QPP writes or target timing are
invented. Browser connection panel remains offline and identifies host-only data.

Verification commands:

    python3 -m unittest discover -s tests -v
    CANOPY_LIVE_VCAN=1 python3 -m unittest discover -s tests -p test_session.py -v
    REPLAY_LIVE_FILE=/external/new-run/replay.jsonl REPLAY_EVIDENCE_DIR=/external/screens node tests/test_replay_browser.cjs

The live test verifies actual VSS frame reception, decoded values, learned Pilot
requests, obstacle veto, actual replay conversion, agent gaps and child reaping.
Portable tests validate schema rejection, rotation and Pilot veto without vcan.
These host results do not complete QNX C5/C6/C7/C8/C9 target acceptance.
