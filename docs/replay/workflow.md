# Record and replay without an SDK

Host simulation only. No QNX guest, SocketCAN, vcan, SSH, ttyd or driver process
is started. These commands execute the Python safety/actuator model and record
its outputs, not a prerecorded narrative of a successful QNX run.

    ./canopy demo --script hero --seed 7 --host-sim
    ./canopy record --script hero --seed 7 --host-sim --output run.jsonl
    ./canopy replay run.jsonl
    ./canopy replay run.jsonl --output replay.html
    ./canopy top --replay run.jsonl

Open replay.html directly in a browser, or docs/replay/index.html and choose
run.jsonl in its file picker. All code and the built-in run are inline; no
server, network, installed frontend dependencies or public listener is needed.
Output files must not already exist. demo writes JSONL to stdout unless -o is
supplied; record defaults to run.jsonl. --seed7 is accepted as a seed-7 alias.
The same seed produces byte-identical JSONL. Different seeds affect initial
model speed, not director event ordering. No real-time or wall-clock timing is
implied. The host model does not accelerate after stopping.

The hero script drops model heartbeat delivery at logical 500–3490 ms while
staling model sensor inputs, restores at 3500 ms, injects an obstacle at
4000–4490 ms and an excessive pilot request at 5000–5490 ms. Watchdog/latch and
vehicle-stop events are derived from model outputs. It never kills a process,
creates a fake PID, claims a restart or simulates a terminal transcript.

## Source schema

One object per line, schema canopy.host-run.v1. source must be exactly
"host deterministic simulation; NOT QNX"; clock is logical-ms, scenario hero.
sequence starts at zero and is contiguous; time_ms is a strictly increasing
nonnegative safe integer. seed is a consistent safe integer throughout the run.
Fields speed_mps, brake, hazards, watchdog, safestop and accepted describe host
model outputs. inputs contains speed_age_ms, obstacle_age_ms, obstacle_m,
pilot_speed_mps. heartbeat has can_id 512, four-byte payload_hex, delivered.
Payload CRC/state/ranges are checked. events is a list of distinct allowlisted
markers, ordered within each record. See canopy_host/director.py for the list.

The entire record inherits the explicit host-simulation source; neither the
source label nor CRC authenticates external files. Validation is structural,
not proof that an imported file ran the model. Unsupported sources (including
HOST VCAN and QNX) are rejected, never relabeled. A verified live-vcan recorder
and authenticated QNX telemetry require separate schemas/adapters and evidence.
Limit: 2 MB UTF-8, 10000 rows. Invalid files retain the previous displayed run.

## Offline instrument

A: vehicle outputs, C: recorded host inputs and latch; B: inspectable raw record,
D: unavailable QNX/transport evidence, E: watchdog states and timestamped event
buttons. All panel values inherit their adjacent source label. No target age,
PID, CPU, SSH continuity, priority, restart count or recovery latency is invented.
Play/pause, speed, reset, range scrub, event jumps and local file input work
without the SDK. Tab navigates controls; Space toggles playback from page body,
arrows step records, Home/End seek endpoints, I toggles record inspection.
Playback uses logical timestamps rather than a fixed record count per second.

## Remaining target work

C9/C10 target acceptance is NOT complete. Requires external licensed SDP/QSTI,
a genuine QNX 8.0 boot, x86_64 mods-can verification, RX/TX, SLM restart chain,
QPP/canstats/agent evidence and verified ttyd/SSH/PID telemetry. up remains
blocked by doctor. No Pages deployment or submission was performed.
