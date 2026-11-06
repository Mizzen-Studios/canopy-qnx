# Dedicated CAN fallback supervision — follow-up 10

Status: original config and host gates implemented; **native SLM/HAM restart NOT
validated**. This is not full C3. The current driver is libcan dev-can-linux,
not working SocketCAN. No QEMU started and no external image changed by this lane.

## Read-only investigation (2026-11-06)

- Installed external driver strings and existing private build-traffic.sh identify
  /proc/boot/dev-can-linux -b id=0,freq=500k as the native invocation.
  Its -u option takes suboptions, not an integer; the config uses the observed
  bitrate invocation instead. Foreground/daemon behavior still needs target proof.
- External ifs-edu-resmgr.bin string scan found /proc/ham/.info but no standalone
  SLM/HAM executable path. **This is not an image inventory or absence proof**:
  binaries may be compressed or live on the disk image. SDK is inside a separate
  x86 guest; local host file search cannot establish its installed contents.
- QNX 8 documentation inspected read-only:
  https://www.qnx.com/developers/docs/8.0/com.qnx.doc.neutrino.utilities/topic/s/slm.html
  and the analogous h/ham.html page. SLM has -n private control endpoint,
  -R 5/min recovery frequency and repair backoff in integer seconds.
  Backoff increases on unsuccessful restart attempts and resets after successful
  start: it is NOT exponential crash-loop backoff. HAM starts its own guardian;
  stop via hamctrl or ham_stop, never kill the manager casually.

## SDK owner inventory update

EDU's follow-up10 read-only inventory now confirms target x86_64 binaries at
/home/qnx/qnx800/target/qnx/x86_64/usr/sbin/slm and
/home/qnx/qnx800/target/qnx/x86_64/bin/slmctl. SLM direct NEEDED entries:
libexpat.so.2, libsecpol.so.1, libqh.so.1, libc.so.6, libgcc_s.so.1.
slmctl direct NEEDED: libc.so.6 and libgcc_s.so.1. Full transitive closure still
belongs to the SDK image builder. HAM was not found by that inventory.
No target execution/help output was included, so native behavior remains pending.
EDU is staging a distinct external IFS; SLM native lease remains third.

scripts/slm-target-smoke.sh is an original opt-in, fresh-image-only parser and
node readiness probe. It refuses an existing control endpoint or CAN node,
logs pidin and documented slmctl listall/active -v, and never kills a process.
Its shell syntax/refusal paths are host-verified, not its QNX runtime.
The control queries are from the QNX 8 slmctl reference, not inferred CLI syntax.
The script's READY marker explicitly excludes restart, traffic and SSH proof.

## Original config and limit design

config/supervision/slm-can-fallback.xml manages **only** canopy-can; no adoption,
main io-sock, sshd, critical launch, shell expansion, blanket abilities or dependent
network components. Namespace declaration is for XML host validation; actual SLM
parser compatibility must be checked before enabling this config.

Candidate target command (NOT run):

    slm -n /dev/slm-canopy -R 5/min -s canopy-can slm-can-fallback.xml

Requires slogger2, installed slm + runtime dependencies, a writable private control
endpoint and a driver process which does not detach behind SLM. Existing startup
must not launch a second driver. Do not run alongside the current CAN startup.
Do not add ifconfig to libcan: no SocketCAN can0 interface is established here.

canopy_host/supervision.py supplies a tested **host policy model**, not a deployed
controller. Five restart admissions in a rolling 60-second window; sixth request
latches manual mode. Proposed app-budget delays: 1,2,4,8,16 seconds, capped at16.
Keep safestop/actuator stop latched throughout; operator reset requires the driver
stopped and safestop latched. SLM -R behavior alone is not claimed to implement
this exact rolling window or persistent latch. A native controller must intercept
admission before spawning, persist the manual latch across controller restart,
and fail closed if state cannot be read. Do not layer this policy model on top
of autonomous SLM respawn and claim it enforces the limit: use a reviewed control
adapter (repair none plus explicit admission/start), or demonstrate equivalent
SLM semantics and external stop/latch authority first.

SLM unavailable: inspect installed HAM binary/library and supported 8.0 APIs next.
Register only the dedicated CAN process and death condition; implement the same
admission/manual latch before restart. If HAM unavailable/unusable, the plan's
last resort is an original native death-notification supervisor: retain a child
identity from spawn, wait/reap it, and admit respawn through the same policy.
No HAM API or own-supervisor implementation is claimed by these host tests.

## Exact identity / acceptance

Never slay io-sock, pkill by name, kill a process group, or trust a bare stale
PID file. Production target adapter must bind executable, arguments, PID,
process-start identity and supervisor-owned generation; verify the main io-sock
is distinct. Revalidate immediately before signaling with a documented native
identity-safe mechanism; if unable to eliminate PID reuse races, refuse injection.
Linux procfs start ticks are not a QNX implementation. can.pid alone is insufficient.

The host test starts and retains owned Popen children, kills only the CAN stand-in,
reaps it, restarts it, exchanges fresh dummy messages and proves the separate main
stand-in remains responsive across three kills. **Host NOT QNX, NOT SLM, NOT CAN**.
The evidence validator rejects PID-only readiness, wrong killed identity, main
instance changes, missing new CAN generation, missing readiness/traffic, and any
attempt to promote host records to native evidence. It checks truth conditions,
not transcript authenticity. Full C3 and SocketCAN always remain false here.

SSH continuity is separate: require an authenticated same-connection stream,
continuous probes and zero observed drops. Main PID continuity, keyscan success,
or a new authenticated connection do not establish uninterrupted SSH. Current
handshake is intermittent and authenticated SSH remains unverified.

## Native/SDK lease request for parent

Host milestone is test-ready. Please ask EDU (exclusive SDK owner) to read-only
inventory SDK target executables slm/slmctl/ham/hamctrl, inspect their use messages,
list dependencies and inventory current IFS. If slm exists, EDU owns adding it
and dependencies/config to a new **external** IFS; no SDK files go into Git.
Request native lease only after C2 and EDU finish/stop. No concurrent guest use.

Native next acceptance: parsed config -> one owned driver -> exact PID kill -> new
identity -> /dev/can0 readiness -> independent RX/TX byte-exact traffic after
restart, three consecutive runs, main io-sock same identity. Capture each hop
(death, spawn, node ready, first fresh frame) and keep SSH status explicitly
unverified unless the independent authenticated same-session evidence exists.
Test five admissions/sixth latch and manual reset independently. Least privilege
secpol deny/allow is pending; do not grant broad abilities just to pass.

Native caps mandatory: CPUQuota100%, MemoryMax1G, nice15, 1vCPU/512MiB.
SDK caps mandatory: CPUQuota200%, MemoryMax4G, nice15, 2vCPU/2GiB. Inspect real
cgroup cpu.max/memory.max; no uncapped fallback. Timing results must say
"observed in this QEMU run · app budget, not a QNX benchmark".

The independent SocketCAN gate remains blocked by a matching x86_64 mods-can.so,
io-sock module/board ABI and unavailable internal build hooks. This does not
block host configuration work or libcan fallback supervision, but it prevents
calling any fallback run full SocketCAN C3.

## Host verification

    python3 -m unittest discover -s tests -p test_supervision.py -v
    python3 -m unittest discover -s tests -v
    scripts/check-no-sdk.sh
    git diff --check

No benchmark, public evaluation, publication, PR, Pages, spend or contact implied.
