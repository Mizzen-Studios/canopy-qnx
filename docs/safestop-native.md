# C6 original native source — runtime PENDING

Original QNX source now passes actual SDP8 x86-64 qcc compile/link with strict
C11 warnings and -lm. [Source-bound compile receipt](acceptance/safestop-build-20261107/receipt.json).
It has NOT yet passed native runtime acceptance. Only parent owns SDK/guest execution. No Linux sender is presented as
native. Matching mods-can/io-sock ABI remains blocked. This explicitly uses
**dev-can-linux v1.12 raw devctl/libcan fallback**, not working SocketCAN.
Demo patterns only, no functional-safety certification or physical actuator.

## Wire review (unchanged)

Existing heartbeat is ALREADY four bytes at standard ID 0x200, DLC4:
state (0 DRIVE,1 BRAKE,2 SAFE_STOP,3 RECOVER), brake percent 0..100,
counter 0..15 (upper nibble zero), CRC-8 SAE-J1850. CRC input is 02 00
followed by the first three bytes; poly1d initff xoroutff non-reflected.
SAFE_STOP requires brake100. No gratuitous version migration or two-byte
compatibility mode was added. CRC/counter do not authenticate senders.
Existing C/Python cross-language encoder tests remain authoritative.

## Native mechanism

native/safestop_qnx.c links safety/safestop.c + native_inputs.c. It checks
sched_setscheduler(SCHED_FIFO,20), getscheduler and getparam, logs observed
policy/priority/PID, then uses ChannelCreate/ConnectAttach/SIGEV_PULSE_INIT,
timer_create(CLOCK_MONOTONIC), timer_settime(10ms), MsgReceivePulse.
All setup errors exit nonzero. No scheduling fallback. TimerTimeout bounds
SEND/REPLY for each devctl (2ms), receive (100ms), and only four RX operations
are allowed per pulse. Full RX budget invalidates sensors rather than trusting
a backlog. Output/log backpressure can still delay the loop: the FSM's >20ms
gap relatches; independent host ECU deadline remains essential. Runtime
scheduler policy/pulse timing must be collected, not inferred from source.

Inputs use existing 0x100 DLC2 LE .01km/h and 0x102 DLC2 BE .01m. Speed is
converted to m/s and feeds the existing bounded-speed veto (no new pilot ID,
no external latch-clear). 0x101 steering is unrelated and ignored. Missing,
invalid, future and >30ms inputs fail closed. Ten healthy cycles are required;
tenth remains SAFE_STOP100, eleventh ramps90. Normal driver -b invocation
without timestamp override is required.

Inspected public external API references (not copied): dev-can-linux commit
f120bdb001e289b3335bdefe37acab945fabcd99 commands.h, netif.c, resmgr.c,
queue.c and timer.c under external source checkout. Native struct can_msg,
CAN_DEVCTL_RX_FRAME_RAW_NOBLOCK / TX_FRAME_RAW come from sys/can_dcmd.h;
commands.h wrappers themselves use devctl and need no -lcan library. Our
app invokes public devctl directly, without embedding GPL inline wrappers.
The parent compiled against the installed SDK externally; no SDK header is
redistributed. _QNX_SOURCE exposes QNX extensions under -std=c11; -lm resolves
the actual QNX math linkage. Original-source command:

    qcc -Vgcc_ntox86_64 -std=c11 -O2 -Wall -Wextra -Werror -Isafety native/safestop_qnx.c safety/native_inputs.c safety/safestop.c -o safestop-qnx -lm

IMPORTANT fallback-specific quirk: netif_rx discards CAN_RTR_FLAG, then sets
is_remote_frame=1 for non-echo DATA. Rejecting that field as conventional RTR
would reject every actual input. We deliberately do not reinterpret it as RTR.
This is NOT portable across arbitrary libcan drivers. Driver timestamp is
ClockCycles divided by integer cycles_per_us, in uint32 milliseconds, not
CLOCK_MONOTONIC's epoch; adapter computes age in that same domain before
mapping into local monotonic ages. Driver timestamp overrides invalidate this
assumption and are unsupported. Actual timestamp/RTR tests remain required.

## Parent-owned bounded native run

After C3/SSH and exclusive guest lease, cross-compile externally, stage only
original source and external output. Maximum 60s / 6000 pulses per launch;
parent also needs a wall-clock watchdog (pulse count alone is not wall time).
Caps: SDK and guest each 100% host CPU,1GiB; QEMU 1vCPU/512MiB. No child
starts/reconfigures VM/images. Reuse parent's guest transport/correct IRQ route.
Stop candump and other rx0 consumers before launch; no shared 0x200 sender.

Guest commands (parent chooses upload path, do not assume /proc/boot):

    ./safestop-qnx 800 none > /tmp/c6.log 2>&1 &
    C6_PID=$!
    pidin -p $C6_PID threads
    pidin -p $C6_PID arguments
    cat /tmp/c6.log

Host, with actual parent-mapped interface (not assumed SocketCAN inside QNX):

    python3 -m tools.native_safestop_host ecu --interface vcan1 --duration 10 --output build/ecu.jsonl
    python3 -m tools.native_safestop_host stimulus --interface vcan1 --duration 8 --scenario stale

Run separately/concurrently using owned processes. Scenarios healthy,stale,
obstacle,pilot,malformed inject only existing IDs; faults t2..5s, then restore.
The three-second interval permits the simulated vehicle to reach zero before
restoration. --events appends timestamps at actual stale injection/restore actions.
Wire faults: guest 800 bad-crc or 800 frozen (first200 pulses healthy).
Pause/kill: parent sends kill -STOP/-CONT or kill -KILL to recorded C6_PID
after observed DRIVE and verifies host ECU <=100ms deadline assertion.
Restart native process to supply startup ten SAFE_STOP frames after wire fault;
DRIVE alone intentionally cannot rearm the ECU. Replayed same counter cannot
refresh deadline. Sensor faults must show native latch and ten-cycle release.
Capture independent host actual frames, native tick payloads/timestamps,
FIFO proof and pidin; compare payload byte exact (TX devctl success alone is
only queue acceptance). Capture zero simulated speed/full brake/hazards,
last_valid_ms never refreshed by corruption/freeze. No physical stopping claim.
An exit, timeout, lost timer, I/O fault or process kill stops heartbeats; host
ECU must brake, and parent must NOT relabel missing results as a native pass.

Host tests: strict gcc portable boundary+FSM into existing Python ECU exercises
seven faults; exhaustive existing C/Python wire parity remains. A negative
compile proves this native adapter refuses host-only builds. These tests are
not QNX scheduling/runtime acceptance. C6 native gate stays PENDING until
parent records real compiler and guest evidence.
