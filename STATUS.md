# Status — 7 November 2026

## Current upgrade — 8 November 2026, implemented; scoped verification complete, council gate pending

Olly approved the substantive [upgrade package](docs/upgrade-acceptance-20261108.md); the earlier feature-freeze statements below are preserved history, not the current instruction. Previous independent acceptance remains conditional and does not transfer to these new features.

[Fresh prerequisite receipts](docs/acceptance/prereq-20261108/NOTES.md): same-ELF IO ability deny/allow in separate runs, bounded structured slog2 capture and actual co-located observer death/separate recorder survival were observed in the bound QEMU run. **Pathname policy BLOCKED**: installed tools alone do not establish attach/connect enforcement or loaded policy identities. Ability control is not /dev path policy or least-privilege proof.

The [BYO incident desk](docs/incident-pack.md) imports, validates and queries new bounded packs locally. Functional fixtures remain HOST_SIMULATION. The [reusable native recorder](docs/native-recorder.md) now has a [fresh source-bound capture](docs/acceptance/native-recorder-20261108/NOTES.md): SLM-managed driver kill/restart and independent ordered byte-exact100RX100TX plus finite slog2 capture and actual co-located death control. [Control integrity fixes](docs/acceptance/control-fix-20261108/NOTES.md) now require schema v2, two distinct co-located members, shared process/generation, bound termination observations and a separate survivor. The preserved v1 pack now returns UNKNOWN; the separately derived v2 pack binds the unchanged raw native evidence. Independent focused recheck PASS for all four assigned integrity findings; [final host verification and chronology](docs/acceptance/final-upgrade-20261108/NOTES.md) records exact tested revisions. This is not new council acceptance or a full audit. Imported origin labels remain collector declarations, not attestation. Historical viewer and native evidence are separate. SSH verdict is unsupported in the current v2 importer.

C6/native safety STOPPED; SocketCAN UNVERIFIED. No heartbeat, actuation, recording, publication or deployment. recorded:false. Videos remain deferred until all features and final verification, with the separate recording gate preserved. sshd internal cause UNVERIFIED; no platform-health, safety, timing or continuous-availability claim.

## Preserved prior review and milestone history


## Current priority — 17:28 UTC timing correction

Finish supported onboarding and product/evidence consistency, then verify completed revisions and return for independent gate. Videos are deferred to the end after final freeze+finalverification+independentgate and separate Olly OK; capture is not the next blocker. Existing dry checklist parked without script polishing. Native scope remains frozen; C6STOPPED. [Gate order](docs/readiness-gate.md).

## Preserved scoped evidence chronology

Private [claim-to-receipt review](REVIEW.md): this is historical evidence, not a fresh native run.

Actual [desktop/mobile Chromium validation](docs/acceptance/browser-20261107/NOTES.md): missing/corrupt/mixed → UNKNOWN; recorded native labels remain separate from simulation. Host suite **126 passed / 8 skipped**. No fresh native acceptance.

## Current direction — council approval, 7 November 2026

Canonical [capability ledger](docs/capabilities.md) separates host simulation,
recorded native libcan/SLM PASS, SocketCAN UNVERIFIED and C6 FAIL/stopped.
Recorded incident receipts are the hero; no native vehicle-safety positioning.
C6 remains STOPPED: no automatic retries, heartbeat work or renamed safety lane.
Read-only evidence-bound incident viewer implemented at f3b4fb0; parent verifier
and six corruption/HTML tests PASS. This is generation-time recorded evidence,
not fresh QNX execution or historical driver source attestation. Historical receipts below remain preserved, not fresh runs.


**Historical capture PASS (not rerun in this review): three native libcan byte-exact runs and three native SLM managed-process restarts.**

- CAN runs1–3:100/100RX and100/100TX each, ordered ID/DLC/eight-byte exact with independently captured host traffic. Preserved in [native CAN evidence](docs/acceptance/native-can-20261106/summary.json); parent offline recheckPASS. This is the libcan fallback, NOT an accepted io-sock SocketCAN ABI/C2 gate.
- Fresh dedicated SLM image parsed the original config and started the managed libcan CAN service. Exact observed PIDs were checked before each kill:278546→323602→434194→520210. All three restarted and /dev/can0/rx0 was present afterward. Mainio-sock PID163853 stayed unchanged in each before/after snapshot.
- Observation windows3.3863/3.3168/3.4429seconds include a fixed3-second settle. These are **observed in this QEMU run · app budget, not a QNX benchmark**; not exact restart latency or evidence of service availability at every instant.
- [Native SLM receipt](docs/acceptance/slm-20261107/receipt.json), [serial](docs/acceptance/slm-20261107/serial.txt), [exact VM-specific controller](docs/acceptance/slm-20261107/controller.py). Controller refuses missing caps, takes a local exclusive lock, kills only the positively observed managed CAN PID in its own fresh image, and stops/reaps only its own QEMU.
- Effective cgroup100%CPU/1GiB,nice15; guest1vCPU/512MiB. Native guests serialized. No shared Gateway restart.

EarlyC6 host-vcan fault tests, C/Python parity and source-bound SDP x86 compile-only evidence remain recorded in [safestop](docs/safestop-early.md). Native timer-pulse/FIFO/CAN runtime acceptance is not claimed.

## Follow-up 11: post-restart traffic and native preparation

Three additional managed-process kills now each have 100 RX + 100 TX ordered
ID/DLC/payload exact against independent host capture. Main io-sock PID163853
stayed unchanged. [Receipt](docs/acceptance/slm-traffic-20261107/receipt.json)
and all three frame arrays are preserved; offline corruption tests reject bad
bytes/order/count/PID/cap receipts. Evidence2b9be8c; verifiera093d13.
These are **observed in this QEMU run · app budget, not a QNX benchmark**.

**C3 requested libcan close-out PASS:** a further three kills each passed
100 RX +100 TX exact AND the same authenticated SSH connection kept streaming.
[Receipt](docs/acceptance/slm-continuity-20261107/receipt.json), client/server
authentication logs, raw serial, controller and all six frame arrays are saved;
evidence568ea6a. CAN PIDs626715→778263→2764823→4743191; main io-sock163853
unchanged; same host SSH client126654, contiguous counters0..96. Largest
observed tick gap1.385132s. Windows3.403986/3.377878/3.431113s include a fixed
3s settle, NOT pure restart latency. **Observed in this QEMU run · app budget,
not a QNX benchmark.**

Prerequisites actually discovered: missing SSH session/auth helpers were staged
from the installed SDK externally; main io-sock was attached to IRQ10 despite
PCI reporting11. Before the kills, virtio PIRQ-C and Kvaser PIRQ-D were routed
to the observed IRQ10; virtio used vectors=0, and IPv4 was configured. Earlier
network/banner failures and an unbounded remote-shell PATH mistake are NOT
counted as acceptance. The final bounded stream uses /proc/boot/sleep.

C6 strict actual qcc compile/link PASS ([receipt](docs/acceptance/safestop-build-20261107/receipt.json));
native FIFO/pulse/actuator runtime attempt FAILED; lane stopped after the focused
attempt below. SDK/native guests stopped/reaped. Effective caps remained
CPU100%,1GiB,nice15,1vCPU/512MiB.

## Still unverified

Full SocketCAN C2/C3 requires matching x86_64 module/board ABI. Identity-safe production supervision, rolling-window/manual-latch limits, least privilege and robust failure injection are not established by the restart smoke. The separate authenticated stream above—not PID snapshots—proves the bounded SSH observation. No full C3 policy acceptance is claimed.

C6 lane stopped; SDK, C3 and C6 guests stopped/reaped; lease free. Both repos private. SDK/licenses/headers/libs/images/binaries/QSC/secrets remain external. No publication, contacts, paid resources or upstream PRs.

## C6 failure recovery

**Runtime gate UNVERIFIED / last execution FAIL:**850 native TX attempts versus one host0x200 heartbeat; all SAFE_STOP, no fresh sensors. Evidence:docs/acceptance/safestop-failure-20261107. **observed in this QEMU run · app budget, not a QNX benchmark**. Guest stopped/reaped; at this historical checkpoint one focused fix attempt was next (completed below; now STOPPED).

## Focused C6 attempt closed — 11:06 UTC

**BLOCKED / runtime UNVERIFIED.** Fresh100RX+100TX exact baseline passed; raising all observed10r/20r CAN helpers24r did not fix850 native TX attempts versus1 host heartbeat. Root cause remains undetermined in persistent libcan RX/TX, not an accepted scheduler fix. Evidence:docs/acceptance/safestop-focused-failure-20261107. **observed in this QEMU run · app budget, not a QNX benchmark**. Guest stopped/reaped, lease free. C6 lane STOPPED per one-attempt rule; no automatic retry. E2 host/docs polish selected; no E2 snapshot runtime PASS. Experimental XML archived with failure evidence, not production-installed.

## Conditional private-validation corrections — 7 November 2026

Recorded viewer scope unchanged; no feature breadth or native rerun. Stale SocketCAN/vehicle-safety positioning corrected. UNKNOWN now gives bounded recovery without repinning or guest execution; static PASS is generation-time only.

Disposable missing/corrupt/mixed UNKNOWN pages and command/input/outcome/digest receipt: docs/acceptance/unknown-review-20261107/. Separate from authoritative docs/workbench/index.html; host-only rejection fixtures, not browser review.

Actual source-bound host full-suite logs and pinned receipt: docs/acceptance/host-review-20261107/receipt.json. Reviewed 0c65197 rerun: 133 total / 125 PASS / 8 SKIP. Current f09f69d: 134 total / 126 PASS / 8 SKIP, including saved UNKNOWN fixture regression. These counts are host checks, never fresh native acceptance. C6 remains FAIL/stopped.


## Residual packaging source — 21:05 UTC

Current packaging/review source: 22ffcaca1269ec0402099fc06b4876a4e8d51748 (owner remote-verified at 21:05 UTC). Conditional native-completion acceptance remains at 88b1bcf5fcc1f97da03321d35b03e89c85090227, receipt-inspected, not re-run. No CANopy native rerun. Historical native labels mean observed in this QEMU run, not benchmarks. recorded:false. C6 FAIL / STOPPED; SocketCAN UNVERIFIED. No capture, audio, publication, deployment, submission or outside contact. Historical frozen assets and source/build/image pins remain unchanged; packet_source_commit is separate from frozen_commit.
