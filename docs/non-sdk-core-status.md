# Non-SDK core checkpoint — 2026-11-04 UTC

All changes committed as OlsOls2, no history rewritten; repositories remain private.

## Verified host implementation

- C5 project DBC/VSS overlay, golden vectors and exhaustive codec; pinned QPP API/unit/catalogue research. No native QPP writes performed.
- C6 independent host SocketCAN sender/actuator, 100ms watchdog contract, CRC8/counter rejection, ten-fresh-cycle latch recovery and controlled-stop simulation. Seven actual Linux vcan fault cases passed; parent independently reran them on vcan1.
- C7 learned9nodeCART:382/384synthetic held-out rows correct,2164/2164C/Python parity vectors; modelcard explains limitations.
- C8 host session connects learnedPilot, real SocketCAN VSS reception, high-rate synthetic sensor inputs and roughly20Hz host-agent logs. This is not a QNX agent/eth0 continuity test.
- C9/C10 deterministic hero recording plus actual monotonic HOST VCAN recording, separate schema/provenance, offline replay with controls/browser tests. No fake QNX terminal/PIDs/SSH/restart evidence.
- C11 strict budgets/CP101–104, byte-exact log comparator, fail-closed CLI and CI summary on explicitly invented HOST SIM fixtures. Missing real restart evidence cannot pass.

## Reproduce

```sh
python3 -m unittest discover -s tests -v
./scripts/check-no-sdk.sh
./canopy check tests/fixtures/budgets/host-sim-pass.json
sudo ./scripts/setup-vcan.sh vcan0
CANOPY_LIVE_VCAN=1 python3 -m unittest discover -s tests -p test_runtime.py -v
CANOPY_LIVE_VCAN=1 python3 -m unittest discover -s tests -p test_session.py -v
./canopy host-session --interface vcan0 --duration 2 --output /absolute/new-run
./canopy host-record /absolute/new-run -o /absolute/new-record.jsonl
./canopy replay /absolute/new-record.jsonl -o /absolute/new-replay.html
```

Host vcan ID0x200 must be exclusive. Do not run fault suites while a long-running session uses that interface; choose a separate vcan interface or stop the session first.

For explicit long-running host-only simulation:

```sh
./canopy host-session --interface vcan0 --long-running --output /absolute/new-session
# Stop only the owned supervisor PID stored in /absolute/new-session/session.pid
kill -TERM "$(cat /absolute/new-session/session.pid)"
```

Log rotation bounds retained data; stop before converting to obtain consistent raw records. This starts no network listener or service/timer configuration. Session supervisor reaps its children on SIGTERM.

## Parent verification

- Clean clone03ce4cd:84portable cases,81pass+3explicit live skips; artifact gate+CPfixture pass. docs/test-results.txt preserves output/revision.
- Parent opted-in seven-fault runtime suite:5tests pass; integrated session suite:6tests pass.
- Parent bounded actualvcan run converted38records and exported offlineHTML successfully.
- Parent Chromium offline browser suite with fake and actualvcan file:pass; desktop/mobile, filepicker, invalid-file retention, keyboard/playback, noHTTP/JSerrors.
- Doctor host_ready=true, overall_ready=false as intended: SDK/image and target acceptance absent.

## Genuine target dependencies

Licensed SDP/QSTI details are still absent. Required next: native builds/API checks, QNX guest and PCI discovery, driver RX/TX and interrupts, SLM/HAM/restart, secpol, installed QPP catalogue/overlay and connector, native FIFO safestop/pilot/QPP process wiring, canstats/agent/eth0/SSH evidence, target fault/overrun tests, on-QNX capture/video and full target tutorial learner runs. Host tests cannot satisfy runs-on-QNX acceptance.

No target code was represented as built or tested. No SDK files, images or binaries committed; no public publication/Pages/PR/upload/submission.

Demo of fail-safe patterns; not an ISO 26262 / IEC 61508 claim.
